from dataclasses import dataclass
from typing import Protocol
import textwrap

from .state_machine import file_sm, scenarios_sm


@dataclass(frozen=True, kw_only=True)
class InputFile:

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


def default_parse(
            input_file: InputFile,
            /,
            *,
            parsed_file_builder,
) -> ParsedFile:
    lines = input_file.text.splitlines()

    for line in lines:
        parsed_file_builder.consume_line(line)

    return parsed_file_builder.get_built(uri=input_file.uri)


def parse(input_file: InputFile, /) -> ParsedFile:
    return default_parse(
            input_file,
            parsed_file_builder=FileBuilder(
                scenarios_builder=ScenariosBuilder(
                    state_machine=scenarios_sm.Start(),
                ),
                state_machine=file_sm.Start(),
            ),
    )


class FileBuilder:

    def __init__(self, *, scenarios_builder, state_machine):
        self._name = None
        self._description_lines = []
        self._scenarios_builder = scenarios_builder
        self._sm = state_machine

    def process_name(self, name):
        self._name = name

    def process_description(self, description_line):
        self._description_lines.append(description_line)

    def process_scenario_line(self, scenario_line):
        self._scenarios_builder.consume_line(scenario_line)

    def consume_line(self, line):
        self._sm = self._sm(line, builder=self)

    def _get_description(self):
        desc_lines = self._description_lines.copy()
        while desc_lines and not desc_lines[-1].strip():
            desc_lines.pop()
        description = textwrap.dedent('\n'.join(desc_lines)).strip() or None
        return description

    def get_built(self, *, uri):
        return ParsedFile(
            name=self._name,
            description=self._get_description(),
            scenarios=self._scenarios_builder.get_built(),
            uri=uri,
        )


class ScenariosBuilder:

    def __init__(self, state_machine):
        self._sm = state_machine
        self._scenarios = []
        self._scenario_builders = []

    @property
    def _current_scenario_builder(self):
        return self._scenario_builders[-1]

    def consume_line(self, line):
        self._sm = self._sm(line, builder=self)

    def process_scenario_name(self, name):
        self._scenario_builders.append(ScenarioBuilder())
        self._current_scenario_builder.process_scenario_name(name)

    def process_description_line(self, line):
        self._current_scenario_builder.process_description_line(line)

    def create_step(self, sentence):
        self._current_scenario_builder.create_step(sentence)

    def create_step_table(self, column_names):
        self._current_scenario_builder.create_step_table(column_names)

    def add_step_table_row(self, values):
        self._current_scenario_builder.add_step_table_row(values)

    def get_built(self):
        return tuple(sb.get_built() for sb in self._scenario_builders)


class ScenarioBuilder:

    def __init__(self):
        self._name = None
        self._description_lines = []
        self._step_builders = []

    @property
    def _current_step_builder(self):
        return self._step_builders[-1]

    def process_scenario_name(self, name):
        self._name = name

    def get_built(self):
        steps = tuple(sb.get_built() for sb in self._step_builders)
        return Scenario(
                name=self._name,
                description=self._get_description(),
                steps=steps,
        )

    def process_description_line(self, line):
        self._description_lines.append(line)

    def _get_description(self):
        desc_lines = self._description_lines.copy()
        while desc_lines and not desc_lines[-1].strip():
            desc_lines.pop()
        description = textwrap.dedent('\n'.join(desc_lines)).strip() or None
        return description

    def create_step(self, sentence):
        self._step_builders.append(StepBuilder())
        self._current_step_builder.process_step_sentence(sentence)

    def create_step_table(self, column_names):
        self._current_step_builder.create_table(column_names)

    def add_step_table_row(self, values):
        self._current_step_builder.add_table_row(values)


class StepBuilder:

    def __init__(self):
        self._sentence = None
        self._table_names = None
        self._table_rows = []

    def process_step_sentence(self, sentence):
        self._sentence = sentence

    def get_built(self):
        return Step(
                sentence=self._sentence,
                data=tuple(
                    dict(zip(self._table_names, row, strict=True))
                    for row in self._table_rows
                )
        )

    def create_table(self, column_names):
        self._table_names = column_names

    def add_table_row(self, values):
        self._table_rows.append(values)
