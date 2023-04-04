from dataclasses import dataclass
from typing import Protocol


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
class File:

    name: str
    description: str
    scenarios: list[Scenario]
    uri: str


class ParserProto(Protocol):

    def __call__(self, input_file: InputFile, /) -> File:
        """Build test files."""
