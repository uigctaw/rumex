from dataclasses import dataclass
from enum import Enum, auto
from types import MappingProxyType
from typing import Protocol
import textwrap

from .table import parse_table_line
from .tokenizer import Token, iter_tokens


class CannotParseLine(Exception):
    pass


@dataclass(frozen=True, kw_only=True)
class InputFile:
    """Container for a test file to be parsed.

    Does not have to represent an actual file.
    Could be e.g. an entry in a database.

    Params
    ------

    uri: A unique identifer. If it's a file,
        this could be a path to this file.

    text: The content of the file.
    """

    uri: str
    text: str


@dataclass(frozen=True, kw_only=True)
class Step:

    sentence: str
    data: type


@dataclass(frozen=True, kw_only=True)
class Scenario:

    name: str
    description: str
    steps: tuple[Step, ...]


@dataclass(frozen=True, kw_only=True)
class ParsedFile:

    name: str
    description: str
    scenarios: list[Scenario]
    uri: str


class ParserProto(Protocol):

    def __call__(self, input_file: InputFile, /) -> ParsedFile:
        pass


class State(Enum):
    START = auto()
    FILE_NAME = auto()
    FILE_DESCRIPTION = auto()
    NEW_SCENARIO = auto()
    STEP = auto()
    SCENARIO_DESCRIPTION = auto()


_default_state_machine = {

    State.START: {
        Token.NameKW: (
            State.FILE_NAME, lambda b, fn: b.set_file_name(fn)),
        Token.BlankLine: (State.START, lambda b, fn: None),
        Token.ScenarioKW: (
            State.NEW_SCENARIO, lambda b, sn: b.new_scenario(sn)),
        Token.Description: (
            State.FILE_DESCRIPTION,
            lambda b, desc: b.append_file_description(desc)
        ),
        # Step keyword outside of scenario context
        # does not mean anything special.
        Token.StepKW: (
            State.FILE_DESCRIPTION,
            lambda b, desc: b.append_file_description(desc)
        ),
    },

    State.FILE_NAME: {
        Token.Description: (
            State.FILE_DESCRIPTION,
            lambda b, desc: b.append_file_description(desc)
        ),
        Token.BlankLine: (State.FILE_NAME, lambda b, fn: None),

        # Step keyword outside of scenario context
        # does not mean anything special.
        Token.StepKW: (
            State.FILE_DESCRIPTION,
            lambda b, desc: b.append_file_description(desc)
        ),
        Token.ScenarioKW: (
            State.NEW_SCENARIO, lambda b, sn: b.new_scenario(sn)),
    },

    State.FILE_DESCRIPTION: {
        Token.BlankLine: (
            State.FILE_DESCRIPTION,
            lambda b, desc: b.append_file_description(desc)
        ),
        Token.Description: (
            State.FILE_DESCRIPTION,
            lambda b, desc: b.append_file_description(desc)
        ),
        Token.ScenarioKW: (
            State.NEW_SCENARIO, lambda b, sn: b.new_scenario(sn)),

        # Step keyword outside of scenario context
        # does not mean anything special.
        Token.StepKW: (
            State.FILE_DESCRIPTION,
            lambda b, desc: b.append_file_description(desc)
        ),
    },

    State.NEW_SCENARIO: {
        Token.BlankLine: (State.NEW_SCENARIO, lambda b, fn: None),
        Token.StepKW: (State.STEP, lambda b, snt: b.new_step(snt)),
        Token.Description: (
            State.SCENARIO_DESCRIPTION,
            lambda b, desc: b.append_scenario_description(desc)
        ),
    },

    State.SCENARIO_DESCRIPTION: {
        Token.Description: (
            State.SCENARIO_DESCRIPTION,
            lambda b, desc: b.append_scenario_description(desc)
        ),
        Token.BlankLine: (
            State.SCENARIO_DESCRIPTION,
            lambda b, desc: b.append_scenario_description(desc)
        ),
    },

    State.STEP: {
        Token.StepKW: (State.STEP, lambda b, sentence: b.new_step(sentence)),
        Token.Description: (
            State.STEP,
            lambda b, data: b.add_step_data(data),
        ),
        Token.BlankLine: (State.STEP, lambda b, _: None),
    },

}


default_state_machine = MappingProxyType({
    k: MappingProxyType(v) for k, v in _default_state_machine.items()
})


def parse(
        input_file: InputFile,
        *,
        state_machine=default_state_machine,
        start_state=State.START,
) -> ParsedFile:
    builder = FileBuilder()
    state = start_state

    previous_token = None
    tokens = iter_tokens(input_file.text)
    for token in tokens:
        try:
            state, transition = state_machine[state][type(token)]
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


class TableBuilder:

    def __init__(self):
        self._header = None
        self._data = []

    def consume(self, line):
        table_break_symbols = set('+- ')
        if set(line) <= table_break_symbols:
            return

        row = parse_table_line(line, delimiter='|')
        if self._header is None:
            self._header = row
        else:
            self._data.append(row)

    def get_built(self):
        return tuple(dict(zip(self._header, row)) for row in self._data)


class StepBuilder:

    def __init__(self, sentence):
        self._sentence = sentence
        self._table_builder = TableBuilder()

    def add_step_data(self, data):
        self._table_builder.consume(data)

    def get_built(self):
        return Step(
                sentence=self._sentence,
                data=self._table_builder.get_built(),
        )


class ScenarioBuilder:

    def __init__(self, name):
        self._name = name
        self._step_builders = []
        self._description = []

    def __getattr__(self, name):
        try:
            attr = getattr(self._step_builders[-1], name)
        except AttributeError as exc:
            raise AttributeError(name) from exc
        return attr

    def new_step(self, sentence):
        self._step_builders.append(StepBuilder(sentence))

    def append_scenario_description(self, line):
        self._description.append(line)

    def get_built(self):
        if self._description:
            formatted_description = textwrap.dedent(
                    '\n'.join(self._description)).strip()
        else:
            formatted_description = None

        return Scenario(
                name=self._name,
                description=formatted_description,
                steps=[builder.get_built() for builder in self._step_builders],
        )


class FileBuilder:

    def __init__(self):
        self._name = None
        self._description = []
        self._scenario_builders = []

    def set_file_name(self, name):
        self._name = name

    def append_file_description(self, line):
        self._description.append(line)

    def new_scenario(self, scenario_name):
        self._scenario_builders.append(ScenarioBuilder(scenario_name))

    def __getattr__(self, name):
        try:
            attr = getattr(self._scenario_builders[-1], name)
        except AttributeError as exc:
            raise AttributeError(name) from exc
        return attr

    def get_built(self, *, uri):
        if self._description:
            formatted_description = textwrap.dedent(
                    '\n'.join(self._description)).strip()
        else:
            formatted_description = None

        return ParsedFile(
            name=self._name,
            description=formatted_description,
            scenarios=[
                builder.get_built() for builder in self._scenario_builders],
            uri=uri,
        )
