import textwrap

from rumex.parsing.parser import InputFile

# pylint: disable=unbalanced-tuple-unpacking


class Reporter:

    def __init__(self):
        self.reported = []

    def __call__(self, executed_files):
        self.reported.extend(executed_files)


def test_empty_file(run, get_step_mapper, **_):
    text = ''
    uri = 'test_file'
    reporter = Reporter()
    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=get_step_mapper(),
    )

    executed, = reporter.reported

    assert executed.uri == uri
    assert not executed.name
    assert not executed.description
    assert executed.success
    assert not executed.scenarios


def test_lone_file_name(run, get_step_mapper, **_):
    text = 'Name: Test file'
    uri = 'test_file'
    reporter = Reporter()
    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=get_step_mapper(),
    )

    executed, = reporter.reported

    assert executed.uri == uri
    assert executed.name == 'Test file'
    assert not executed.description
    assert executed.success
    assert not executed.scenarios


def test_file_name_and_description(run, get_step_mapper, **_):
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
            steps=get_step_mapper(),
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


def test_lone_scenario(run, get_step_mapper, **_):
    text = 'Scenario: My scenario'
    uri = 'test_file'
    reporter = Reporter()
    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=get_step_mapper(),
    )

    executed, = reporter.reported

    assert not executed.name
    assert not executed.description
    assert executed.success
    scenario, = executed.scenarios
    assert scenario.name == 'My scenario'
    assert scenario.success


def test_description_and_scenario(run, get_step_mapper, **_):
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
        steps=get_step_mapper(),
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


def test_name_description_and_a_scenario(run, get_step_mapper, **_):
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
        steps=get_step_mapper(),
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


def test_scenario_with_description(run, get_step_mapper, **_):
    text = textwrap.dedent('''
        Scenario: Given this scenario.

        A text
            going over multiple lines.

                As shown here.

        Is considered a description, because it does not
        start with any keywords.
    ''')
    uri = 'test_file'
    reporter = Reporter()
    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=get_step_mapper(),
    )

    executed, = reporter.reported
    scenario, = executed.scenarios
    assert scenario.name == 'Given this scenario.'
    assert scenario.description == textwrap.dedent('''
        A text
            going over multiple lines.

                As shown here.

        Is considered a description, because it does not
        start with any keywords.
    ''').strip()
    assert scenario.success


def test_name_no_description_and_scenario(run, get_step_mapper, **_):
    text = textwrap.dedent('''
        Name: Test file.

        Scenario: My scenario.
    ''')
    uri = 'test_file'
    reporter = Reporter()
    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=get_step_mapper(),
    )

    executed, = reporter.reported

    assert executed.uri == uri
    assert executed.name == 'Test file.'
    assert executed.description is None
    assert executed.success

    scenario, = executed.scenarios
    assert scenario.name == 'My scenario.'
    assert scenario.success
