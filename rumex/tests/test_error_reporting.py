import textwrap

from rumex.parsing.parser import CannotParseLine, InputFile

from .test_no_execution_cases import Reporter

# pylint: disable=unbalanced-tuple-unpacking


def test_parsing_error_gives_problem_location_details(run, **_):
    text = textwrap.dedent('''
        Scenario: Errors are reported nicely.

        Given 1
        When we divide it by 0
        -> Unexpected line <-
        Then the 3rd step won't even be executed
    '''.strip())

    uri = 'this is an important identifier'
    msg = ''
    try:
        run(
            files=[InputFile(uri=uri, text=text)],
            reporter=Reporter(),
            steps=None,
        )
    except CannotParseLine as exc:
        msg, = exc.args
    assert '-> Unexpected line <-' in msg
    assert uri in msg
    assert 'line no. 5' in msg
