import textwrap

from rumex.parsing.parser import InputFile
from rumex.runner import run, StepMapper

from .test_no_execution_cases import Reporter


steps = StepMapper()


@steps('Given 1')
def given_1():
    return 1


@steps('divide by 0')
def divide_by_0(number):
    return number / 0


@steps(r'Then the 3rd step')
def does_not_matter():
    pass


def test_scenario_is_failed_when_step_fails():
    text = textwrap.dedent('''
        Scenario: 2nd step fails

        Given 1
        When we divide it by 0
        Then the 3rd step won't even be executed
    ''')
    uri = 'test_file'
    reporter = Reporter()
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
