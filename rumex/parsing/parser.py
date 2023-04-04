from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import Protocol

from .builder import FileBuilder
from .core import InputFile, File
from .tokenizer import TokenKind, iter_tokens


class CannotParseLine(Exception):
    pass


@dataclass(frozen=True, kw_only=True)
class Step:

    sentence: str
    data: type


@dataclass(frozen=True, kw_only=True)
class Scenario:

    name: str
    description: str
    steps: Sequence[Step]


@dataclass(frozen=True, kw_only=True)
class ParsedFile:

    name: str
    description: str
    scenarios: Sequence[Scenario]
    uri: str


class ParserProto(Protocol):

    def __call__(self, input_file: InputFile, /) -> ParsedFile:
        """Text in, object out."""


class State(Enum):
    """Possible states of the default state machine."""

    START = auto()
    FILE_NAME = auto()
    FILE_DESCRIPTION = auto()
    NEW_SCENARIO = auto()
    STEP = auto()
    SCENARIO_DESCRIPTION = auto()


class StateMachine(Mapping):
    """Represents possible states of a parser.

    This object is a map where keys are `State` enumerals
    and values are maps where keys are `TokenKind` enumerals
    and values are 2-tuples of (`State` enumeral, builder callback).

    The "builder callback" objects are functions that take
    two positional arguments: `builder` and a value extracted
    from a token of the associated `TokenKind`.

    The parser uses the state machine map in the following way:

    1) Using `current_state` as a key, extracts the eligible
       state transitions from the state machine map.
    2) Having token `t`, uses it to extract the 2-tuple
       from the eligible state transitions.
    3) Sets `current_state` to the first value of the tuple.
    4) Executes the callback, passing it a `builder` object
       and a value extracted from the token `t`.
    """

    def __init__(self, transitions):
        self._transitions = transitions

    def __getitem__(self, item):
        return self._transitions[item]

    def __iter__(self):
        return iter(self._transitions)

    def __len__(self):
        return len(self._transitions)


def new_scenario(builder, scenario_name):
    builder.new_scenario(scenario_name)


def no_op(*_):
    pass


def set_file_name(builder, file_name):
    builder.name = file_name


def append_file_description(builder, line):
    builder.description.append(line)


def new_step(builder, sentence):
    builder.current_scenario_builder.new_step(sentence)


def append_scenario_description(builder, line):
    builder.current_scenario_builder.description.append(line)


def add_step_data(builder, data):
    builder.current_scenario_builder.current_step_builder.add_step_data(data)


default_state_machine = StateMachine({
    State.START: {
        TokenKind.NAME_KW: (State.FILE_NAME, set_file_name),
        TokenKind.BLANK_LINE: (State.START, no_op),
        TokenKind.SCENARIO_KW: (State.NEW_SCENARIO, new_scenario),
        TokenKind.DESCRIPTION: (
            State.FILE_DESCRIPTION, append_file_description),

        # Step keyword outside of scenario context
        # does not mean anything special.
        TokenKind.STEP_KW: (
            State.FILE_DESCRIPTION, append_file_description),
    },

    State.FILE_NAME: {
        TokenKind.DESCRIPTION: (
            State.FILE_DESCRIPTION, append_file_description),
        TokenKind.BLANK_LINE: (State.FILE_NAME, no_op),

        # Step keyword outside of scenario context
        # does not mean anything special.
        TokenKind.STEP_KW: (
            State.FILE_DESCRIPTION, append_file_description),
        TokenKind.SCENARIO_KW: (State.NEW_SCENARIO, new_scenario),
    },

    State.FILE_DESCRIPTION: {
        TokenKind.BLANK_LINE: (
            State.FILE_DESCRIPTION, append_file_description),
        TokenKind.DESCRIPTION: (
            State.FILE_DESCRIPTION, append_file_description),
        TokenKind.SCENARIO_KW: (State.NEW_SCENARIO, new_scenario),

        # Step keyword outside of scenario context
        # does not mean anything special.
        TokenKind.STEP_KW: (
            State.FILE_DESCRIPTION, append_file_description),
    },

    State.NEW_SCENARIO: {
        TokenKind.BLANK_LINE: (State.NEW_SCENARIO, no_op),
        TokenKind.STEP_KW: (State.STEP, new_step),
        TokenKind.DESCRIPTION: (
            State.SCENARIO_DESCRIPTION, append_scenario_description),
    },

    State.SCENARIO_DESCRIPTION: {
        TokenKind.DESCRIPTION: (
            State.SCENARIO_DESCRIPTION, append_scenario_description),
        TokenKind.BLANK_LINE: (
            State.SCENARIO_DESCRIPTION, append_scenario_description),
        TokenKind.STEP_KW: (State.STEP, new_step),
    },

    State.STEP: {
        TokenKind.STEP_KW: (State.STEP, new_step),
        TokenKind.DESCRIPTION: (State.STEP, add_step_data),
        TokenKind.BLANK_LINE: (State.STEP, no_op),
    },

})


def parse(
        input_file: InputFile,
        *,
        state_machine: StateMachine = default_state_machine,
        make_builder=FileBuilder,
        token_iterator=iter_tokens,
) -> File:
    """Text in, object out.

    """
    state = State.START
    builder = make_builder()

    previous_token = None
    tokens = token_iterator(input_file.text)
    for token in tokens:
        try:
            state, transition = state_machine[state][token.kind]
        except KeyError as exc:
            raise KeyError(f'{state}, {token}') from exc
        try:
            transition(builder, token.value)
        except Exception as exc:
            exc_msg = _get_exception_msg(
                    previous_token=previous_token,
                    token=token,
                    tokens=tokens,
                    file_uri=input_file.uri,
            )
            raise CannotParseLine(exc_msg) from exc
        previous_token = token

    return builder.get_built(uri=input_file.uri)


def _get_exception_msg(*, previous_token, token, tokens, file_uri):
    line_num = token.line_num + 1  # it's 0-based but we want to report 1-based

    context = []
    if previous_token is not None:
        context.append((f'{line_num - 1}: ', previous_token.line))
    context.append((f'ERR> {line_num}: ', token.line))
    try:
        next_token = next(tokens)
    except StopIteration:
        pass
    else:
        context.append((f'{line_num + 1}: ', next_token.line))

    max_prefix_len = max(
            len(prefix_and_line[0]) for prefix_and_line in context)

    formatted_context = []
    max_line_len = 80 - max_prefix_len
    for prefix, line in context:
        prefix = prefix.rjust(max_prefix_len)
        if len(line) > max_line_len:
            line = line[:-3] + '...'
        formatted_context.append(prefix + line)

    return (
            f'Error parsing file "{file_uri}"'
            + f' (line no. {line_num})'
            + '\n\n'
            + '\n'.join(formatted_context)
            + '\n\n'
    )
