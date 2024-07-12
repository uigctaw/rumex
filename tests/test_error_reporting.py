import textwrap

from rumex import InputFile, StepMapper, run
from rumex.parsing.parser import CannotParseLineError

from .test_no_execution_cases import Reporter


def test_parsing_error_gives_problem_location_details():
    text = textwrap.dedent(
        """
        Scenario: Errors are reported nicely.

        Given 1
        When we divide it by 0
        -> Unexpected line <-
        Then the 3rd step won't even be executed
    """.strip(),
    )

    uri = "this is an important identifier"
    msg = ""
    try:
        run(
            files=[InputFile(uri=uri, text=text)],
            reporter=Reporter(),
            steps=StepMapper(),
        )
    except CannotParseLineError as exc:
        (msg,) = exc.args
    assert "-> Unexpected line <-" in msg
    assert uri in msg
    assert "line no. 5" in msg
