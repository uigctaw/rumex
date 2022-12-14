import textwrap

from rumex.parsing.parser import InputFile
from rumex.runner import run, StepMapper

from .test_no_execution_cases import Reporter


def test_scenario_is_failed_when_step_fails():
    text = textwrap.dedent('''
        Scenario: 2nd step fails

        Given 1
        When we divide it by 0
        Then the 3rd step won't even be executed
    ''')
    uri = 'test_file'
    reporter = Reporter()

    steps = StepMapper()

    @steps('Given 1')
    def given_1():
        return dict(number=1)

    @steps('divide by 0')
    def divide_by_0(number):
        return number / 0

    @steps(r'Then the 3rd step')
    def does_not_matter():
        pass

    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=steps,
    )

    executed_file, = reporter.reported
    scenario, = executed_file.scenarios
    given, when, then = scenario.steps
    assert given.success
    assert not when.success
    assert not then.success
    assert not scenario.success
    assert not executed_file.success


def test_success():
    text = textwrap.dedent('''
        Scenario: All good.

        Given 2
        When we divide it by 2
        And add 1
        Then we have 2
    ''')
    uri = 'test_file'
    reporter = Reporter()

    steps = StepMapper()

    @steps('Given 2')
    def given_():
        return dict(number=2)

    @steps('divide it by 2')
    def when_(*, number):
        return dict(number=number / 2)

    @steps(r'And add (\d)')
    def and__(digit: int, *, number):
        return dict(result=number + digit)

    @steps(r'we have 2')
    def then_(*, result):
        assert result == 2

    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=steps,
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


def test_parameterized_step_without_type_annotations():
    text = textwrap.dedent('''
        Scenario: No annotations

        Given two numbers 1 and 12
    ''')
    reporter = Reporter()
    steps = StepMapper()

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


def test_parameterized_step_with_type_annotations():
    text = textwrap.dedent('''
        Scenario: All annotated

        Given two numbers 2 and 13.5
    ''')
    reporter = Reporter()
    steps = StepMapper()

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


def test_parameterized_step_with_some_annotations():
    text = textwrap.dedent('''
        Scenario: Some annotated

        Given four numbers 1, 2, 3 and 4
    ''')
    reporter = Reporter()
    steps = StepMapper()

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
