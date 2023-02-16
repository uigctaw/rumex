from collections import defaultdict
from dataclasses import dataclass
import itertools
import re
import textwrap


class Absent:

    _inst = None

    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
        return cls._inst

    def __iter__(self):
        return self

    def __next__(self):
        raise StopIteration()

    def __bool__(self):
        return False


absent = Absent()


@dataclass(frozen=True, kw_only=True)
class _InDescriptionNamedElement:
    name: str
    description: str


class NumpyesqueDocstring:

    _DESC = '_description'
    _PARAMS = 'Params'
    _RETURNS = 'Returns'
    _YIELDS = 'Yields'
    _RAISES = 'Raises'

    def __init__(self, docstring: str):
        self.docstring = docstring
        sections = self._get_sections(docstring)
        self.description = self._format_description(sections[self._DESC])
        self.parameters = self._format_parameters(sections[self._PARAMS])
        self.returns = self._format_returns(sections[self._RETURNS])
        self.yields = self._format_yields(sections[self._YIELDS])
        self.raises = self._format_raises(sections[self._RAISES])

    def _format_description(self, lines):
        if not lines:
            return absent

        head, *tail = lines
        formatted = head + '\n' + textwrap.dedent('\n'.join(tail))
        return formatted.strip()

    def _format_returns(self, lines):
        return self._format_returns_or_yields(lines)

    def _format_yields(self, lines):
        return self._format_returns_or_yields(lines)

    def _format_returns_or_yields(self, lines):
        if not lines:
            return absent

        return textwrap.dedent('\n'.join(lines)).strip()

    def _format_parameters(self, lines):
        return self._format_named_with_description(lines)

    def _format_raises(self, lines):
        return self._format_named_with_description(lines)

    def _format_named_with_description(self, lines):
        if not lines:
            return absent

        pattern = re.compile(r'^\s*(\w+)\s*:\s*(.*)$')

        descs = {}
        lines = itertools.dropwhile(lambda line: not line.strip(), lines)

        for line in lines:
            if match_ := pattern.match(line):
                param, desc = match_.groups()
                descs[param] = [desc]
            else:
                descs[param].append(line)

        params = []
        for name, description in descs.items():
            params.append(_InDescriptionNamedElement(
                name=name,
                description=textwrap.dedent('\n'.join(description)).strip(),
            ))
        return tuple(params)

    def _get_sections(self, docstring):
        lines = docstring.splitlines()
        next_lines = lines[1:] + ['']
        current_section = self._DESC
        keywords = set((
            self._DESC,
            self._PARAMS,
            self._RETURNS,
            self._YIELDS,
            self._RAISES,
        ))
        sections = defaultdict(list)
        jump = False
        for line, next_line in zip(lines, next_lines):
            if jump:
                jump = False
                continue
            stripped = line.strip()
            if stripped in keywords:
                if set(next_line.strip()) == set('-'):
                    current_section = stripped
                    jump = True
                    continue
            sections[current_section].append(line)
        return sections
