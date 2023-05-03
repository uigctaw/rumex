from dataclasses import dataclass
import textwrap

from rumex.parsing.parser import InputFile
from rumex.runner import IgnoredStep, MatchingFunctionNotFound

from .test_no_execution_cases import Reporter

# pylint: disable=unbalanced-tuple-unpacking


def test_scenario_is_failed_when_step_fails(run, get_step_mapper, **_):
    text = textwrap.dedent('''
        Scenario: 2nd step fails

        Given 1
        When we divide it by 0
        Then the 3rd step won't even be executed
    ''')
    uri = 'test_file'
    reporter = Reporter()

    steps = get_step_mapper()

    run_steps = []

    @steps('Given 1')
    def given_1():
        run_steps.append(1)

    @steps('divide it by 0')
    def divide_by_0():
        run_steps.append(2)
        run_steps[0] / 0  # pylint: disable=pointless-statement

    @steps(r'Then the 3rd step')
    def does_not_matter():
        run_steps.append(3)

    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=steps,
    )

    assert run_steps == [1, 2]
    executed_file, = reporter.reported
    scenario, = executed_file.scenarios
    given, when, then = scenario.steps
    assert given.success
    assert not when.success
    assert not then.success
    assert not scenario.success
    assert not executed_file.success


def test_success(run, get_step_mapper, **_):  # pylint: disable=too-many-locals
    text = textwrap.dedent('''
        Scenario: All good.

        Given 2
        When we divide it by 2
        And add 1
        Then we have 2
    ''')
    uri = 'test_file'
    reporter = Reporter()

    steps = get_step_mapper()

    @dataclass
    class Context:
        value: float | None = None

    @steps('Given 2')
    def given_(*, context):
        context.value = 2

    @steps('divide it by 2')
    def when_(*, context):
        context.value /= 2

    @steps(r'And add (\d)')
    def and__(digit: int, *, context):
        context.value += digit

    @steps(r'we have 2')
    def then_(*, context):
        assert context.value == 2

    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=steps,
        context_maker=Context,
    )

    executed_file, = reporter.reported
    scenario, = executed_file.scenarios
    given, when, and_, then = scenario.steps
    assert given.success
    assert when.success
    assert and_.success
    assert then.success
    assert scenario.success
    assert executed_file.success


def test_parameterized_step_without_type_annotations(
        run, get_step_mapper, **_):
    text = textwrap.dedent('''
        Scenario: No annotations

        Given two numbers 1 and 12
    ''')
    reporter = Reporter()
    steps = get_step_mapper()

    @steps(r'Given two numbers (\d+) and (\d+)')
    def given_(num_a, num_b):
        assert num_a == '1'
        assert num_b == '12'

    run(
        files=[InputFile(uri='we', text=text)],
        reporter=reporter,
        steps=steps,
    )

    executed_file, = reporter.reported
    assert executed_file.success


def test_parameterized_step_with_type_annotations(run, get_step_mapper, **_):
    text = textwrap.dedent('''
        Scenario: All annotated

        Given two numbers 2 and 13.5
    ''')
    reporter = Reporter()
    steps = get_step_mapper()

    class TimesTwo:

        def __init__(self, val):
            self.value = 2 * int(val)

    @steps(r'Given two numbers (\d+) and (\d+\.\d+)')
    def given_(num_a: TimesTwo, num_b: float):
        assert num_a.value == 4
        assert num_b == 13.5

    run(
        files=[InputFile(uri='we', text=text)],
        reporter=reporter,
        steps=steps,
    )

    executed_file, = reporter.reported
    assert executed_file.success


def test_parameterized_step_with_some_annotations(run, get_step_mapper, **_):
    text = textwrap.dedent('''
        Scenario: Some annotated

        Given four numbers 1, 2, 3 and 4
    ''')
    reporter = Reporter()
    steps = get_step_mapper()

    @steps(r'Given four numbers (\d), (\d), (\d) and (\d)')
    def given_(a: int, b, c: float, d):  # pylint: disable=invalid-name
        assert a == 1
        assert b == '2'
        assert c == 3.0
        assert d == '4'

    run(
        files=[InputFile(uri='we', text=text)],
        reporter=reporter,
        steps=steps,
    )

    executed_file, = reporter.reported
    assert executed_file.success


def test_scenario_with_a_description_and_a_step(run, get_step_mapper, **_):
    text = textwrap.dedent('''
        Scenario: You can have a description in a scenario.

        First a description, then a step.

        Given an integer 5
    ''')
    reporter = Reporter()
    steps = get_step_mapper()

    @steps(r'Given an integer 5')
    def given_():
        pass

    run(
        files=[InputFile(uri='we', text=text)],
        reporter=reporter,
        steps=steps,
    )

    executed_file, = reporter.reported
    assert executed_file.success
    scenario, = executed_file.scenarios
    assert scenario.success
    assert scenario.description == 'First a description, then a step.'


def test_2_scenarios(run, get_step_mapper, **_):
    text = textwrap.dedent('''
        Name: Test file.

        Scenario: My scenario.
            Given something

        Scenario: My 2nd scenario.
            Given anything
    ''')
    uri = 'test_file'

    steps = get_step_mapper()

    @steps(r'thing')
    def given_():
        pass

    reporter = Reporter()
    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=steps,
    )

    executed, = reporter.reported

    scenario_1, scenario_2 = executed.scenarios
    assert scenario_1.name == 'My scenario.'
    assert scenario_2.name == 'My 2nd scenario.'


def test_unimplemented_scenario(run, get_step_mapper, **_):
    text = textwrap.dedent('''
        Name: Test file.

        Scenario: My scenario.
            Given stuff
            And anything
            And more stuff
            Then something
    ''')
    uri = 'test_file'

    steps = get_step_mapper()

    @steps(r'stuff')
    def given_():
        pass

    reporter = Reporter()
    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=steps,
    )

    executed, = reporter.reported
    scenario, = executed.scenarios
    assert not scenario.success
    passed, failed_1, ignored, failed_2 = scenario.steps
    assert passed.success
    assert not failed_1.success
    assert isinstance(failed_1.exception, MatchingFunctionNotFound)
    assert not ignored.success
    assert isinstance(ignored, IgnoredStep)
    assert not failed_2.success
    assert isinstance(failed_2.exception, MatchingFunctionNotFound)
