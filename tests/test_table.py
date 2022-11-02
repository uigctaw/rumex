import textwrap

import pytest

from rumex.parsing.parser import InputFile
from rumex.parsing.state_machine.scenarios_sm import (
        BadTableLine,
        _parse_table_line,
)
from rumex.runner import run, StepMapper

from .test_no_execution_cases import Reporter


def test_line_parser():
    values = _parse_table_line('| Col 1 | Col 2 |', delimiter='|')
    assert values == ('Col 1', 'Col 2')

    values = _parse_table_line(r'| Col\|1 | \|Col\\\\2\| |', delimiter='|')
    assert values == ('Col|1', r'|Col\\2|')

    values = _parse_table_line('|x||', delimiter='|')
    assert values == ('x', '')

    values = _parse_table_line('||', delimiter='|')
    assert values == ('',)

    values = _parse_table_line('+++', delimiter='+')
    assert values == ('', '')

    values = _parse_table_line('  |Col1|Col2|  ', delimiter='|')
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
        with pytest.raises(BadTableLine):
            _parse_table_line(line, delimiter='|')


def test_table():
    text = textwrap.dedent('''
        Scenario: Step with a table

        Given the following stuff:
            | Col 1 | Col 2 |
            +-------+-------+
            | ab cd | AB CD |
            | efgh  |   UVW |
    ''')
    reporter = Reporter()
    steps = StepMapper()

    @steps(r'Given the following stuff:')
    def given_(*, step_data):
        assert step_data == (
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


def test_table_with_escaping():
    text = textwrap.dedent(r'''
        Scenario: Step with a table

        Given the following stuff:
            | Col \|1 | Col\| 2   |
            +---------+-----------+
            | ab\|cd  |     AB CD |
            | efgh    | \| UVW \| |
    ''')
    reporter = Reporter()
    steps = StepMapper()

    @steps(r'Given the following stuff:')
    def given_(*, step_data):
        assert step_data == (
                {'Col |1': 'ab|cd', 'Col| 2': 'AB CD'},
                {'Col |1': 'efgh', 'Col| 2': '| UVW |'},
        )

    run(
        files=[InputFile(uri='we', text=text)],
        reporter=reporter,
        steps=steps,
    )

    executed_file, = reporter.reported
    assert executed_file.success
