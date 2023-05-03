import json
import textwrap

from rumex.parsing.parser import InputFile

from .test_no_execution_cases import Reporter

# Happy to fail at runtime with this
# pylint: disable=unbalanced-tuple-unpacking


def test_scenario_with_examples(run, get_step_mapper, **_):
    text = textwrap.dedent('''
        Scenario: 2 examples, 2 vars

        Given <my_var>
        And <your_var>

        Examples:
            | my_var | your_var |
            |   1234 | 5678     |
            |   3456 | 7890     |
    ''')
    uri = 'test_file'

    reporter = Reporter()
    steps = get_step_mapper()

    nums = []

    @steps('Given (1234)')
    def given_a(_1234: int):
        nums.append(_1234)

    @steps('Given (3456)')
    def given_b(_3456: int):
        nums.append(_3456)

    @steps(r'And (\d+)')
    def given(num: int):
        nums.append(num)

    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=steps,
    )

    executed_file, = reporter.reported
    scenario_1, scenario_2 = executed_file.scenarios
    assert scenario_1.success
    assert scenario_2.success
    assert nums == [1234, 5678, 3456, 7890]


def test_scenario_with_examples_in_step_data(run, get_step_mapper, **_):
    text = textwrap.dedent('''
        Scenario: Variables in table values or text blocks are fine

        Given stuff:
            | price   | quantity |
            +---------+----------+
            | <price> | 2        |
            |       1 | 1        |

        And discount:
            """
                {"value": <discount>}
            """

        Then the final price is <result>

        Examples:

            | price | discount | result |
            +-------+----------+--------+
            |     0 |      0.1 |    0.9 |
            |     2 |      0.2 |      4 |
    ''')
    uri = 'test_file'

    reporter = Reporter()
    steps = get_step_mapper()

    class Context:

        def __init__(self):
            self.discount = None
            self.total = None

    @steps('Given stuff')
    def given(*, context, data):
        context.total = sum(
            int(row['price']) * int(row['quantity']) for row in data
        )

    @steps('And discount')
    def and_(*, context, data):
        context.discount = json.loads(data)['value']

    @steps(r'final price is (\d\.?\d*)')
    def calculate_result(result: float, *, context):
        assert result == (1 - context.discount) * context.total

    run(
        files=[InputFile(uri=uri, text=text)],
        reporter=reporter,
        steps=steps,
        context_maker=Context,
    )

    executed_file, = reporter.reported
    scenario_1, scenario_2 = executed_file.scenarios
    assert scenario_1.success
    assert scenario_2.success
