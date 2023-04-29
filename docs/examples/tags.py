from functools import partial

import rumex

example_file = rumex.InputFile(
    text='''
        Name: Basic example

        @a_tag
        @another_tag
        Scenario: Simple arithmetics

            Given an integer 1
            Then we have an integer 1!

        @todo
        @IMPORTANT
        Scenario: This is not implemented

            Given some difficult math
            Then stuff happens
    ''',
    uri='Using tags to ignore scenarios.',
)

steps = rumex.StepMapper()


@steps(r'integer \d+')
def do_not_store_integer():
    """This does nothing..."""


def reporter(executed_files):
    executed_file, = executed_files
    scenario_1, scenario_2 = executed_file.scenarios
    assert scenario_1.success
    assert isinstance(scenario_1, rumex.runner.PassedScenario)
    assert scenario_2.success
    assert isinstance(scenario_2, rumex.runner.SkippedScenario)


rumex.run(
    files=[example_file],
    steps=steps,
    reporter=reporter,
    executor=partial(rumex.runner.execute_file, skip_scenario_tag='todo'),
)
