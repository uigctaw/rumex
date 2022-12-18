from __future__ import annotations

import enum
import re

from .state_machine import Transition, CannotParseLine

# Often unused when e.g. blank line is skipped
# pylint: disable=unused-argument

_DESCRIPTION_DELIMITER_PATTERN = re.compile(r'\s*----+\s*')
_STEP_PATTERN = re.compile(r'\s*((?:And|Given|When|Then)\s+.*)')
_TABLE_ROW_SEPARATOR = '|'
_TABLE_ROW_PATTERN = re.compile(rf'^\s*\{_TABLE_ROW_SEPARATOR}')
_TABLE_BREAK_SEPARATOR = '+'
_TABLE_BREAK_PATTERN = re.compile(rf'^\s*\{_TABLE_BREAK_SEPARATOR}')
SCENARIO_NAME_PATTERN = re.compile(r'\s*Scenario:\s*(.*)')


class TableException(Exception):
    pass


class BadTableLine(TableException):
    pass


class InconsistentTable(TableException):
    pass


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
        TABLE_ROW = enum.auto()

    def _get_key(self, line):
        if not line.strip():
            return self._Key.BLANK

        if _STEP_PATTERN.match(line):
            return self._Key.STEP

        if _TABLE_ROW_PATTERN.match(line):
            return self._Key.TABLE_ROW

        raise CannotParseLine(line)

    def __init__(self):
        self._transitions = {
            self._Key.BLANK: self._skip,
            self._Key.STEP: self._start_step,
            self._Key.TABLE_ROW: self._start_table,
        }

    def _skip(self, line, *, builder):
        return self

    def _start_step(self, line, *, builder):
        step_, = _STEP_PATTERN.match(line).groups()
        builder.create_step(step_)
        return Step()

    def _start_table(self, line, *, builder):
        col_names = _parse_table_line(line, delimiter=_TABLE_ROW_SEPARATOR)
        builder.create_step_table(col_names)
        return StepTable(num_cols=len(col_names))


class StepTable(Transition):

    class _Key(enum.Enum):
        SKIP = enum.auto()
        TABLE_ROW = enum.auto()

    def _get_key(self, line):
        if _TABLE_ROW_PATTERN.match(line):
            return self._Key.TABLE_ROW

        if _TABLE_BREAK_PATTERN.match(line):
            return self._Key.SKIP

        raise CannotParseLine(line)

    def __init__(self, *, num_cols):
        self._num_cols = num_cols
        self._transitions = {
            self._Key.TABLE_ROW: self._populate_table,
            self._Key.SKIP: self._skip,
        }

    def _populate_table(self, line, *, builder):
        values = _parse_table_line(line, delimiter=_TABLE_ROW_SEPARATOR)
        if len(values) != self._num_cols:
            raise InconsistentTable(line)
        builder.add_step_table_row(values)
        return self

    def _skip(self, line, *, builder):
        no_ops = _parse_table_line(line, delimiter=_TABLE_BREAK_SEPARATOR)
        if len(no_ops) != self._num_cols:
            raise InconsistentTable(line)
        return self


def _parse_table_line(line, *, delimiter):
    line = line.strip()

    if len(line) < 2 or line[0] != delimiter or line[-1] != delimiter:
        raise BadTableLine(line)

    line = line[1:]

    escape_symbol = '\\'
    values = []
    current_value = []
    escape_next_symbol = False
    for symbol in line:
        if escape_next_symbol:
            current_value.append(symbol)
            escape_next_symbol = False
        else:
            if symbol == delimiter:
                values.append(''.join(current_value).strip())
                current_value = []
            elif symbol == escape_symbol:
                escape_next_symbol = True
            else:
                current_value.append(symbol)

    if current_value:  # Can happen if the last delimiter was escaped
        raise BadTableLine(line)

    return tuple(values)
