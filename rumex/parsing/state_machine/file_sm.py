import enum
import re

from .state_machine import Transition
from .scenarios_sm import SCENARIO_NAME_PATTERN

# Often unused when e.g. blank line is skipped
# pylint: disable=unused-argument


class Start(Transition):

    _NAME_PATTERN = re.compile(r'\s*Name:\s*(.*)')

    class _Key(enum.Enum):
        BLANK = enum.auto()
        NAME_KEYWORD = enum.auto()
        SCENARIO_KEYWORD = enum.auto()
        DESCRIPTION = enum.auto()

    def __init__(self):
        self._transitions = {
            self._Key.BLANK: self._skip_line,
            self._Key.NAME_KEYWORD: self._add_name,
            self._Key.SCENARIO_KEYWORD: self._scenario,
            self._Key.DESCRIPTION: self._add_description,
        }

    def _get_key(self, line):
        if not line.strip():
            return self._Key.BLANK

        if self._NAME_PATTERN.match(line):
            return self._Key.NAME_KEYWORD

        if SCENARIO_NAME_PATTERN.match(line):
            return self._Key.SCENARIO_KEYWORD

        return self._Key.DESCRIPTION

    def _skip_line(self, line, *, builder):
        return self

    def _add_name(self, line, *, builder):
        name, = self._NAME_PATTERN.match(line).groups()
        builder.process_name(name)
        return Name()

    def _scenario(self, line, *, builder):
        builder.process_scenario_line(line)
        return Scenarios()

    def _add_description(self, line, *, builder):
        builder.process_description(line)
        return Description()


class Name(Transition):

    class _Key(enum.Enum):
        BLANK = enum.auto()
        DESCRIPTION = enum.auto()
        SCENARIO_KEYWORD = enum.auto()

    def __init__(self):
        self._transitions = {
            self._Key.BLANK: self._skip_line,
            self._Key.SCENARIO_KEYWORD: self._scenario,
            self._Key.DESCRIPTION: self._add_description,
        }

    def _get_key(self, line):
        if not line.strip():
            return self._Key.BLANK

        if SCENARIO_NAME_PATTERN.match(line):
            return self._Key.SCENARIO_KEYWORD

        return self._Key.DESCRIPTION

    def _skip_line(self, line, *, builder):
        return self

    def _add_description(self, line, *, builder):
        builder.process_description(line)
        return Description()

    def _scenario(self, line, *, builder):
        builder.process_scenario_line(line)
        return Scenarios()


class Description(Transition):

    class _Key(enum.Enum):
        SCENARIO_KEYWORD = enum.auto()
        DESCRIPTION = enum.auto()

    def __init__(self):
        self._transitions = {
            self._Key.SCENARIO_KEYWORD: self._scenario,
            self._Key.DESCRIPTION: self._add_description,
        }

    def _get_key(self, line):
        if SCENARIO_NAME_PATTERN.match(line):
            return self._Key.SCENARIO_KEYWORD

        return self._Key.DESCRIPTION

    def _add_description(self, line, *, builder):
        builder.process_description(line)
        return self

    def _scenario(self, line, *, builder):
        builder.process_scenario_line(line)
        return Scenarios()


class Scenarios(Transition):

    def __init__(self):
        self._transitions = {None: self._scenario}

    def _get_key(self, line):
        return None

    def _scenario(self, line, *, builder):
        builder.process_scenario_line(line)
        return self
