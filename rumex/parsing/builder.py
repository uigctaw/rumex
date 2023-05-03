import textwrap

from .core import ParsedFile, Scenario, Step
from .table import parse_table_line


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
        header = self._header or []
        return tuple(dict(zip(header, row)) for row in self._data)


class TextBlockBuilder:

    def __init__(self):
        self._lines = []

    def consume(self, line):
        self._lines.append(line)

    def get_built(self):
        return textwrap.dedent('\n'.join(self._lines)).strip()


class StepBuilder:

    def __init__(self, sentence):
        self.sentence = sentence
        self._builder = None
        self._table = False
        self._text_block = False

    def add_step_data(self, data):
        self._table = True
        if self._text_block:
            raise AssertionError('Unexpected usage.')
        self._builder = self._builder or TableBuilder()
        self._builder.consume(data)

    def add_text_block_line(self, line):
        self._text_block = True
        if self._table:
            raise AssertionError('Unexpected usage.')
        self._builder = self._builder or TextBlockBuilder()
        self._builder.consume(line)

    def get_built(self):
        return Step(
                sentence=self.sentence,
                data=self._builder.get_built() if self._builder else None,
        )


class ScenarioBuilder:

    def __init__(self, name):
        self.name = name
        self._step_builders = []
        self.description = []
        self.tags = []
        self._examples_builder = TableBuilder()

    @property
    def current_step_builder(self):
        return self._step_builders[-1]

    def new_step(self, sentence):
        self._step_builders.append(StepBuilder(sentence))

    def add_example(self, line):
        self._examples_builder.consume(line)

    def get_built(self):
        if self.description:
            formatted_description = textwrap.dedent(
                    '\n'.join(self.description)).strip()
        else:
            formatted_description = None
        return Scenario(
                name=self.name,
                description=formatted_description,
                steps=[builder.get_built() for builder in self._step_builders],
                tags=tuple(self.tags),
                examples_data=self._examples_builder.get_built(),
        )


class FileBuilder:

    def __init__(self):
        self.name = None
        self.description = []
        self._scenario_builders = []

    @property
    def current_scenario_builder(self):
        return self._scenario_builders[-1]

    def new_scenario(self, name=None):
        self._scenario_builders.append(ScenarioBuilder(name))

    def get_built(self, *, uri):
        if self.description:
            formatted_description = textwrap.dedent(
                    '\n'.join(self.description)).strip()
        else:
            formatted_description = None

        return ParsedFile(
            name=self.name,
            description=formatted_description,
            scenarios=[
                builder.get_built() for builder in self._scenario_builders],
            uri=uri,
        )
