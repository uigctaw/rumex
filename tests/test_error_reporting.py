import textwrap

import pytest

from rumex.parsing.parser import InputFile
from rumex.parsing.state_machine.state_machine import CannotParseLine
from rumex.runner import run

from .test_no_execution_cases import Reporter


def test_parsing_error_gives_problem_location_details():
    text = textwrap.dedent('''
        Scenario: Errors are reported nicely.

        Given 1
        When we divide it by 0
        -> Unexpected line <-
        Then the 3rd step won't even be executed
    '''.strip())

    uri = 'this is an important identifier'
    with pytest.raises(CannotParseLine) as exc:
        run(
            files=[InputFile(uri=uri, text=text)],
            reporter=Reporter(),
            steps=None,
        )
    msg, = exc.value.args
    assert '-> Unexpected line <-' in msg
    assert uri in msg
    assert 'line 6' in msg
