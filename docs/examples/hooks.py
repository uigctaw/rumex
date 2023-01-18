import rumex

example_file = rumex.InputFile(
    text='''
        Name: Hooks example

        Scenario: Simple arithmetics

            Given an integer 1
            And an integer 2
            When addition is performed
            Then the result is 3
    ''',
    uri='in place file, just an example',
)

steps = rumex.StepMapper()


class Context:

    def __init__(self):
        self.integers = []
        self.sum = None
        self.step_counter = None


@steps.before_scenario
def before_scenario(context: Context):
    assert context.step_counter is None
    context.step_counter = 0


@steps.before_step
def before_step(context: Context):
    context.step_counter += 1


@steps(r'an integer (\d+)')
def store_integer(integer: int, *, context: Context):
    context.integers.append(integer)


@steps(r'addition is performed')
def add(*, context: Context):
    context.sum = sum(context.integers)


@steps(r'the result is (\d+)')
def check_result(expected_result: int, *, context: Context):
    assert expected_result == context.sum
    assert context.step_counter == 3


rumex.run(
    files=[example_file],
    steps=steps,
    context_maker=Context,
)
