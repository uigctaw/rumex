from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Hashable
import re


class CannotTokenizeLine(Exception):
    pass


class TokenKind(Enum):

    NAME_KW = auto()
    SCENARIO_KW = auto()
    STEP_KW = auto()
    BLANK_LINE = auto()
    DESCRIPTION = auto()


@dataclass(frozen=True, kw_only=True)
class Token:
    """Every line must map to a `Token`."""

    kind: Hashable
    value: Any
    line: str
    line_num: int


# pylint: disable=inconsistent-return-statements

def match_keyword(keyword, *, line):
    if match_ := re.match(fr'^\s*{keyword}:\s*(.*)$', line):
        value, = match_.groups()
        return value


def match_scenario(line):
    if name := match_keyword('Scenario', line=line):
        return TokenKind.SCENARIO_KW, name


def match_name(line):
    if name := match_keyword('Name', line=line):
        return TokenKind.NAME_KW, name


def match_step(line):
    stripped = line.strip()
    if stripped.startswith(('Given ', 'When ', 'Then ', 'And ')):
        return TokenKind.STEP_KW, line


def match_blank_line(line):
    if not line.strip():
        return TokenKind.BLANK_LINE, line


def match_description(line):
    return TokenKind.DESCRIPTION, line

# pylint: enable=inconsistent-return-statements


class Tokenizers(Sequence):
    """Functions to extract line-tokens from text."""

    def __init__(self, *fns):
        self._fns = fns

    def __repr__(self):
        return f'Tokenizers({", ".join(self._fns)})'

    def __getitem__(self, item):
        return self._fns[item]

    def __len__(self):
        return len(self._fns)


default_tokenizers = Tokenizers(
    match_name,
    match_scenario,
    match_step,
    match_blank_line,
    match_description,
)


def iter_tokens(text, tokenizers=default_tokenizers):
    for i, line in enumerate(text.splitlines()):
        for tokenizer in tokenizers:
            if kind_and_value := tokenizer(line):
                token_kind, value = kind_and_value
                yield Token(
                        kind=token_kind, value=value, line=line, line_num=i)
                break
        else:
            raise CannotTokenizeLine(line)
