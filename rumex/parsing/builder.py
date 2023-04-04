import textwrap

from .core import File, Scenario, Step
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
        return tuple(dict(zip(self._header, row)) for row in self._data)


class StepBuilder:

    def __init__(self, sentence):
        self.sentence = sentence
        self._table_builder = TableBuilder()

    def add_step_data(self, data):
        self._table_builder.consume(data)

    def get_built(self):
        return Step(
                sentence=self.sentence,
                data=self._table_builder.get_built(),
        )


class ScenarioBuilder:

    def __init__(self, name):
        self.name = name
        self._step_builders = []
        self.description = []

    @property
    def current_step_builder(self):
        return self._step_builders[-1]

    def new_step(self, sentence):
        self._step_builders.append(StepBuilder(sentence))

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
        )


class FileBuilder:

    def __init__(self):
        self.name = None
        self.description = []
        self._scenario_builders = []

    @property
    def current_scenario_builder(self):
        return self._scenario_builders[-1]

    def new_scenario(self, scenario_name):
        self._scenario_builders.append(ScenarioBuilder(scenario_name))

    def get_built(self, *, uri):
        if self.description:
            formatted_description = textwrap.dedent(
                    '\n'.join(self.description)).strip()
        else:
            formatted_description = None

        return File(
            name=self.name,
            description=formatted_description,
            scenarios=[
                builder.get_built() for builder in self._scenario_builders],
            uri=uri,
        )
