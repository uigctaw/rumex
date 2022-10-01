from __future__ import annotations

import enum
import re

from .state_machine import Transition, CannotParseLine

# Often unused when e.g. blank line is skipped
# pylint: disable=unused-argument

_DESCRIPTION_DELIMITER_PATTERN = re.compile(r'\s*----+\s*')
_STEP_PATTERN = re.compile(r'\s*((?:Given|When|Then)\s+.*)')
SCENARIO_NAME_PATTERN = re.compile(r'\s*Scenario:\s*(.*)')


class Start(Transition):

    def _get_key(self, line):
        return None

    def __init__(self):
        self._transitions = {None: self._new_scenario}

    def _new_scenario(self, line, *, builder):
        name, = SCENARIO_NAME_PATTERN.match(line).groups()
        builder.process_scenario_name(name)
        return Scenario()


class Scenario(Transition):

    class _Key(enum.Enum):
        BLANK = enum.auto()
        SCENARIO_KEYWORD = enum.auto()
        DESCRIPTION_DELIMITER = enum.auto()
        STEP = enum.auto()

    def _get_key(self, line):
        if not line.strip():
            return self._Key.BLANK

        if SCENARIO_NAME_PATTERN.match(line):
            return self._Key.SCENARIO_KEYWORD

        if _DESCRIPTION_DELIMITER_PATTERN.match(line):
            return self._Key.DESCRIPTION_DELIMITER

        if _STEP_PATTERN.match(line):
            return self._Key.STEP

        raise CannotParseLine(line)

    def __init__(self):
        self._transitions = {
            self._Key.BLANK: self._skip,
            self._Key.SCENARIO_KEYWORD: self._new_scenario,
            self._Key.DESCRIPTION_DELIMITER: self._start_description,
            self._Key.STEP: self._start_step,
        }

    def _new_scenario(self, line, *, builder):
        name, = SCENARIO_NAME_PATTERN.match(line).groups()
        builder.process_scenario_name(name)
        return self

    def _skip(self, line, *, builder):
        return self

    def _start_description(self, line, *, builder):
        return Description()

    def _start_step(self, line, *, builder):
        step_, = _STEP_PATTERN.match(line).groups()
        builder.create_step(step_)
        return Step()


class Description(Transition):

    class _Key(enum.Enum):
        BODY = enum.auto()
        DELIMITER = enum.auto()

    def _get_key(self, line):
        if _DESCRIPTION_DELIMITER_PATTERN.match(line):
            return self._Key.DELIMITER

        return self._Key.BODY

    def __init__(self):
        self._transitions = {
            self._Key.BODY: self._process_description_line,
            self._Key.DELIMITER: self._end_description,
        }

    def _process_description_line(self, line, *, builder):
        builder.process_description_line(line)
        return self

    def _end_description(self, line, *, builder):
        return Scenario()


class Step(Transition):

    class _Key(enum.Enum):
        BLANK = enum.auto()
        STEP = enum.auto()

    def _get_key(self, line):
        if not line.strip():
            return self._Key.BLANK

        if _STEP_PATTERN.match(line):
            return self._Key.STEP

        raise CannotParseLine(line)

    def __init__(self):
        self._transitions = {
            self._Key.BLANK: self._skip,
            self._Key.STEP: self._start_step,
        }

    def _skip(self, line, *, builder):
        return self

    def _start_step(self, line, *, builder):
        step_, = _STEP_PATTERN.match(line).groups()
        builder.create_step(step_)
        return Step()
