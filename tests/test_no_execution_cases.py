import textwrap

from rumex.parsing.parser import InputFile
from rumex.runner import run, StepMapper


class Reporter:

    def __init__(self):
        self.reported = []

    def __call__(self, executed_files):
        self.reported.extend(executed_files)


def test_empty_file():
    text = ''
    uri = 'test_file'
    reporter = Reporter()
    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=StepMapper(),
    )

    executed, = reporter.reported

    assert executed.uri == uri
    assert not executed.name
    assert not executed.description
    assert executed.success
    assert not executed.scenarios


def test_lone_file_name():
    text = 'Name: Test file'
    uri = 'test_file'
    reporter = Reporter()
    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=StepMapper(),
    )

    executed, = reporter.reported

    assert executed.uri == uri
    assert executed.name == 'Test file'
    assert not executed.description
    assert executed.success
    assert not executed.scenarios


def test_file_name_and_description():
    text1 = '''
        Name: Test file
        This is.

            Description.
    '''
    text2 = '''
        Name: Test file


        This is.

            Description.
    '''
    uri = 'test_file'
    for text in [text1, text2]:
        reporter = Reporter()
        run(
            files=[InputFile(uri=uri, text=text)],
            reporter=reporter,
            steps=StepMapper(),
        )

        executed, = reporter.reported

        assert executed.uri == uri
        assert executed.name == 'Test file'
        assert executed.description == textwrap.dedent('''
            This is.

                Description.
        ''').strip()
        assert executed.success
        assert not executed.scenarios


def test_lone_scenario():
    text = 'Scenario: My scenario'
    uri = 'test_file'
    reporter = Reporter()
    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=StepMapper(),
    )

    executed, = reporter.reported

    assert not executed.name
    assert not executed.description
    assert executed.success
    scenario, = executed.scenarios
    assert scenario.name == 'My scenario'
    assert scenario.success


def test_description_and_scenario():
    text = '''
                This file has no name.

            But it has a description.
        Scenario: My scenario
    '''
    uri = 'test_file'
    reporter = Reporter()
    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=StepMapper(),
    )

    executed, = reporter.reported

    assert not executed.name
    assert executed.description == textwrap.dedent('''
                This file has no name.

            But it has a description.
    ''').strip()
    assert executed.success
    scenario, = executed.scenarios
    assert scenario.name == 'My scenario'
    assert scenario.success


def test_name_description_and_a_scenario():
    text = textwrap.dedent('''
        Name: Test file.
        And then, we have a description.

        Which goes on, and on.
            And on...
                And on...
        Scenario: My scenario.
    ''')
    uri = 'test_file'
    reporter = Reporter()
    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=StepMapper(),
    )

    executed, = reporter.reported

    assert executed.uri == uri
    assert executed.name == 'Test file.'
    assert executed.description == textwrap.dedent('''
        And then, we have a description.

        Which goes on, and on.
            And on...
                And on...
    ''').strip()
    assert executed.success

    scenario, = executed.scenarios
    assert scenario.name == 'My scenario.'
    assert scenario.success


def test_scenario_with_description():
    text = textwrap.dedent('''
        Scenario: Given this scenario.

        ----
        And a description
            going over multiple lines.

                Given here.
        started and ended by a line of 4 or more continuous minus symbols.
        ----
    ''')
    uri = 'test_file'
    reporter = Reporter()
    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=StepMapper(),
    )

    executed, = reporter.reported
    scenario, = executed.scenarios
    assert scenario.name == 'Given this scenario.'
    assert scenario.description == textwrap.dedent('''
            And a description
                going over multiple lines.

                    Given here.
            started and ended by a line of 4 or more continuous minus symbols.
    ''').strip()
    assert scenario.success


def test_name_no_description_and_scenario():
    text = textwrap.dedent('''
        Name: Test file.

        Scenario: My scenario.
    ''')
    uri = 'test_file'
    reporter = Reporter()
    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=StepMapper(),
    )

    executed, = reporter.reported

    assert executed.uri == uri
    assert executed.name == 'Test file.'
    assert executed.description is None
    assert executed.success

    scenario, = executed.scenarios
    assert scenario.name == 'My scenario.'
    assert scenario.success
