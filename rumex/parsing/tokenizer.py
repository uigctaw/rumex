from dataclasses import dataclass
from typing import Any
import re


class CannotTokenizeLine(Exception):
    pass


class _Token:

    def __set_name__(self, owner, name):
        # pylint: disable=attribute-defined-outside-init
        self._inst = dataclass(frozen=True)(
            type(
                name,
                (),
                {
                    '__annotations__': {
                        'value': Any,
                        'line': str,
                        'line_num': int,
                    },
                },
            )
        )
        # pylint: enable=attribute-defined-outside-init

    def __get__(self, obj, objtype):
        return self._inst


class Token:

    NameKW = _Token()
    ScenarioKW = _Token()
    StepKW = _Token()
    BlankLine = _Token()
    Description = _Token()


# pylint: disable=inconsistent-return-statements

def match_keyword(keyword, *, line):
    if match_ := re.match(fr'^\s*{keyword}:\s*(.*)$', line):
        value, = match_.groups()
        return value


def match_scenario(line):
    if name := match_keyword('Scenario', line=line):
        return Token.ScenarioKW, name


def match_name(line):
    if name := match_keyword('Name', line=line):
        return Token.NameKW, name


def match_step(line):
    stripped = line.strip()
    if stripped.startswith(('Given ', 'When ', 'Then ', 'And ')):
        return Token.StepKW, line


def match_blank_line(line):
    if not line.strip():
        return Token.BlankLine, line


def match_description(line):
    return Token.Description, line

# pylint: enable=inconsistent-return-statements


default_tokenizers = (
    match_name,
    match_scenario,
    match_step,
    match_blank_line,
    match_description,
)


def iter_tokens(text, tokenizers=default_tokenizers):
    for i, line in enumerate(text.splitlines()):
        for tokenizer in tokenizers:
            if cls_and_value := tokenizer(line):
                token_cls, value = cls_and_value
                yield token_cls(value=value, line=line, line_num=i)
                break
        else:
            raise CannotTokenizeLine(line)
