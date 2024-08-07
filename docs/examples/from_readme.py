import rumex

example_file = rumex.InputFile(
    text="""
        Name: Basic example

        Scenario: Simple arithmetics

            Given an integer 1
            And an integer 2
            When addition is performed
            Then the result is 3
    """,
    uri="in place file, just an example",
)

steps = rumex.StepMapper()


class Context:
    def __init__(self):
        self.integers = []
        self.sum = None


@steps(r"an integer (\d+)")
def store_integer(integer: int, *, context: Context):
    context.integers.append(integer)


@steps(r"addition is performed")
def add(*, context: Context):
    context.sum = sum(context.integers)


@steps(r"the result is (\d+)")
def check_result(expected_result: int, *, context: Context):
    assert expected_result == context.sum


rumex.run(
    files=[example_file],
    steps=steps,
    context_maker=Context,
)
