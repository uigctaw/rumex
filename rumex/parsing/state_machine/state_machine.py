from __future__ import annotations

from typing import Any, Generic, Mapping, Protocol, TypeVar
import abc
import types

T = TypeVar('T')


class CannotParseLine(Exception):
    pass


class ChangeStateProto(Protocol):

    def __call__(self, line: str, *, builder: Any) -> Transition:
        pass


class Transition(Generic[T], abc.ABC):

    def __call__(self, line: str, *, builder: Any) -> Transition:
        key = self._get_key(line)
        return self._transitions[key](line, builder=builder)

    @abc.abstractmethod
    def _get_key(self, line: str) -> T:
        pass

    _transitions: Mapping[T, ChangeStateProto] = types.MappingProxyType({})
