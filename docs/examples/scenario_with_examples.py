import json

import rumex

example_file = rumex.InputFile(
    text='''
        Name: One scenario, multiple examples

        Scenario: Multitude of arithmetics

            Given an integers <int_a> and <int_b>
            When <operation> is performed
            Then the result is <result>

            Examples:

                | int_a | int_b |      operation | result |
                +-------+-------+----------------+--------+
                |     1 |     1 |       addition |      2 |
                |     1 |     0 |       addition |      1 |
                |     1 |     1 | multiplication |      1 |
                |     1 |     0 | multiplication |      0 |


        Scenario: Step data can use variables as well

            Given integers:
                | number  |
                +---------+
                | <int_a> |
                | <int_b> |

            When calculation is performed:
            """
                {"type": "<operation>"}
            """
            Then the result is <result>

            Examples:

                | int_a | int_b |      operation | result |
                +-------+-------+----------------+--------+
                |     1 |     1 |       addition |      2 |
                |     1 |     0 |       addition |      1 |
                |     1 |     1 | multiplication |      1 |
                |     1 |     0 | multiplication |      0 |
    ''',
    uri="in place file, just an example",
)

steps = rumex.StepMapper()


class Context:
    def __init__(self):
        self.integers = None
        self.result = None


@steps(r"integers (\d+) and (\d+)")
def store_integers_a(int_a: int, int_b: int, *, context: Context):
    context.integers = (int_a, int_b)


@steps(r"addition is performed")
def add(*, context: Context):
    assert context.integers
    context.result = sum(context.integers)


@steps(r"multiplication is performed")
def multiply(*, context: Context):
    assert context.integers
    int_a, int_b = context.integers
    context.result = int_a * int_b


@steps(r"integers:")
def store_integers_b(*, context: Context, data):
    context.integers = (int(row["number"]) for row in data)


@steps(r"calculation")
def calculate(*, context: Context, data):
    dict(
        addition=add,
        multiplication=multiply,
    )[json.loads(data)["type"]](context=context)


@steps(r"the result is (\d+)")
def check_result(expected_result: int, *, context: Context):
    assert context.result == expected_result


rumex.run(
    files=[example_file],
    steps=steps,
    context_maker=Context,
)
