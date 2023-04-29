"""Extending the language.

This example illustrates how the test language can be extended.

In the default implementation, there are no line breaks.
We are going to add them, allowing us to split file names,
scenario names or step sentences into multiple
lines by using the greater-than symbol '>'.

We can do this by modifying the default `parser` argument
of the `run` method.

We need:

    1) A tokenizer that will recognize '>' symbol
    2) A state machine that will understand the new token.
"""
import re

from rumex.parsing.parser import (
        State, StateMachine, default_state_machine, parse)
from rumex.parsing.tokenizer import default_tokenizers, iter_tokens
import rumex

# Let's start by defining our test

example_file = rumex.InputFile(
    text='''
        Name: Extending parser example
            > by introducing line breaks.

        Scenario: Simple arithmetics
            > or perhaps not so simple

            Given an integer 1
                > and an integer 2
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


@steps(r'an integer (\d+) and an integer (\d+)')
def store_integer(integer_a: int, integer_b: int, *, context: Context):
    context.integers.extend([integer_a, integer_b])


@steps(r'addition is performed')
def add(*, context: Context):
    context.sum = sum(context.integers)


@steps(r'the result is (\d+)')
def check_result(expected_result: int, *, context: Context):
    assert expected_result == context.sum


# Now we need to work on modifying the default parser

# 1) Define new tokenizing function

broken_line_token = object()


def match_broken_line(line):
    if match_ := re.match(r'^\s*>(.*)$', line):
        stripped_line, = match_.groups()
        return broken_line_token, stripped_line
    return None


# 2) Extend the sequence of default tokenizers

extended_tokenizers = (match_broken_line,) + tuple(default_tokenizers)


# 3) Create new functions to instruct a builder to
#    use the continued line.

def extend_file_name(builder, stripped_line):
    builder.name += stripped_line


def extend_scenario_name(builder, stripped_line):
    builder.current_scenario_builder.name += stripped_line


def extend_step_sentence(builder, stripped_line):
    builder.current_scenario_builder.current_step_builder.sentence += (
            stripped_line)


# 4) Extend the state machine to include the new token and functions

state_machine_extensions = {
    State.FILE_NAME: {
        broken_line_token: (State.FILE_NAME, extend_file_name),
    },
    State.SCENARIO: {
        broken_line_token: (State.SCENARIO, extend_scenario_name),
    },
    State.STEP: {
        broken_line_token: (State.STEP, extend_step_sentence),
    },
}

extended_state_machine = StateMachine({
    key: value | state_machine_extensions.get(key, {})
    for key, value in default_state_machine.items()
})


# 5) Define new `parser` function that will use our new
#    tokenizer and the state machine.

def extended_parser(input_file):
    return parse(
            input_file,
            state_machine=extended_state_machine,
            token_iterator=lambda text: iter_tokens(
                text, tokenizers=extended_tokenizers),
    )


# Define a class to inspect the results of the test.
class Reporter:

    def __init__(self):
        self.executed_file = None

    def __call__(self, executed_files):
        assert self.executed_file is None
        self.executed_file, = executed_files


reporter = Reporter()

rumex.run(
    files=[example_file],
    steps=steps,
    context_maker=Context,
    parser=extended_parser,
    reporter=reporter,
)


assert reporter.executed_file.name == (
        'Extending parser example by introducing line breaks.')

scenario, = reporter.executed_file.scenarios
assert scenario.name == 'Simple arithmetics or perhaps not so simple'

# This is not the end, however.
# By modifying the parser, we could have introduced regression.
# It's advisable to run tests to increase confidence
# that the orignal functionality is unaffected.

from rumex.tests import (  # noqa: E402 # pylint: disable=wrong-import-position
        iter_tests, run_test)


for test in iter_tests():
    run_test(test, parse=extended_parser)
