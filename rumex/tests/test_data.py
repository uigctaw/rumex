import textwrap

from rumex.parsing.parser import InputFile
from rumex.parsing.table import (
        BadTableLine,
        parse_table_line,
)

from .test_no_execution_cases import Reporter

# pylint: disable=unbalanced-tuple-unpacking


def test_line_parser(**_):
    values = parse_table_line('| Col 1 | Col 2 |', delimiter='|')
    assert values == ('Col 1', 'Col 2')

    values = parse_table_line(r'| Col\|1 | \|Col\\\\2\| |', delimiter='|')
    assert values == ('Col|1', r'|Col\\2|')

    values = parse_table_line('|x||', delimiter='|')
    assert values == ('x', '')

    values = parse_table_line('||', delimiter='|')
    assert values == ('',)

    values = parse_table_line('+++', delimiter='+')
    assert values == ('', '')

    values = parse_table_line('  |Col1|Col2|  ', delimiter='|')
    assert values == ('Col1', 'Col2')

    for line in [
        '',
        ' ',
        'a',
        'a|',
        '|b',
        'a|b',
        '|',
        ' | ',
        r'|\|',
        r'\||',
    ]:
        try:
            parse_table_line(line, delimiter='|')
        except BadTableLine:
            pass
        else:
            raise AssertionError('BadTableLine not raised')


def test_simple_table(get_step_mapper, run, **_):
    text = textwrap.dedent('''
        Scenario: Step with a table

        Given the following stuff:
            | Col 1 | Col 2 |
            +-------+-------+
            | ab cd | AB CD |
            | efgh  |   UVW |
    ''')
    reporter = Reporter()
    steps = get_step_mapper()

    @steps(r'Given the following stuff:')
    def given_(*, data):
        assert data == (
                {'Col 1': 'ab cd', 'Col 2': 'AB CD'},
                {'Col 1': 'efgh', 'Col 2': 'UVW'},
        )

    run(
        files=[InputFile(uri='we', text=text)],
        reporter=reporter,
        steps=steps,
    )

    executed_file, = reporter.reported
    assert executed_file.success


def test_table_with_escaping(get_step_mapper, run, **_):
    text = textwrap.dedent(r'''
        Scenario: Step with a table

        Given the following stuff:
            | Col \|1 | Col\| 2   |
            +---------+-----------+
            | ab\|cd  |   AB CD\\ |
            | efgh\   | \| UVW \| |
    ''')
    reporter = Reporter()
    steps = get_step_mapper()

    @steps(r'Given the following stuff:')
    def given_(*, data):
        assert data == (
                {'Col |1': 'ab|cd', 'Col| 2': 'AB CD\\'},
                {'Col |1': 'efgh', 'Col| 2': '| UVW |'},
        )

    run(
        files=[InputFile(uri='we', text=text)],
        reporter=reporter,
        steps=steps,
    )

    executed_file, = reporter.reported
    assert executed_file.success


def test_two_tables(get_step_mapper, run, **_):
    text = textwrap.dedent('''
        Scenario: Step with 2 tables

        Given the following stuff:
            | Col 1 | Col 2 |
            +-------+-------+
            | foo   | bar   |

        Given this stuff:
            | Col a | Col b |
            +-------+-------+
            | baz   | qux   |
    ''')
    reporter = Reporter()
    steps = get_step_mapper()

    @steps(r'Given the following stuff:')
    def given_(*, data):
        assert data == (
                {'Col 1': 'foo', 'Col 2': 'bar'},
        )

    @steps(r'Given this stuff:')
    def given_2(*, data):
        assert data == (
                {'Col a': 'baz', 'Col b': 'qux'},
        )

    run(
        files=[InputFile(uri='we', text=text)],
        reporter=reporter,
        steps=steps,
    )

    executed_file, = reporter.reported
    assert executed_file.success


def test_steps_with_a_block_of_text(get_step_mapper, run, **_):
    text = textwrap.dedent('''
        Scenario: Steps with text

        Given the following stuff:
            """
            Hello!
                Hi!
            """
    ''')
    reporter = Reporter()
    steps = get_step_mapper()

    @steps(r'Given the following stuff:')
    def given_(*, data):
        assert data == 'Hello!\n    Hi!'

    run(
        files=[InputFile(uri='we', text=text)],
        reporter=reporter,
        steps=steps,
    )

    executed_file, = reporter.reported
    assert executed_file.success
