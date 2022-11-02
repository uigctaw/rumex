from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol, TypeVar
import functools
import inspect
import re

from .parsing.parser import InputFile, ParsedFile, ParserProto, parse

T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)


@dataclass(frozen=True, kw_only=True)
class ExecutedStep:
    pass


@dataclass(frozen=True, kw_only=True)
class ExecutedScenario:

    name: str
    description: str
    steps: tuple[ExecutedStep, ...]

    @property  # type: ignore [misc]
    @functools.cache  # pylint: disable=method-cache-max-size-none
    def success(self):
        return all(step.success for step in self.steps)


@dataclass(frozen=True, kw_only=True)
class ExecutedFile:

    scenarios: tuple[ExecutedScenario, ...]
    uri: str
    name: str
    description: str

    @property  # type: ignore [misc]
    @functools.cache  # pylint: disable=method-cache-max-size-none
    def success(self):
        return all(scenario.success for scenario in self.scenarios)


class Reporter(Protocol[T_co]):

    def __call__(self, executed_files: Iterable[ExecutedFile], /) -> T_co:
        pass


class Executor(Protocol):

    def __call__(
            self,
            parsed: ParsedFile,
            /,
            *,
            steps: StepMapper,
    ) -> ExecutedFile:
        pass


def execute_step(step_, *, sentences_to_functions, previous_step_return):
    fn_ = sentences_to_functions.prepare_function(step_.sentence)
    return fn_(
            **previous_step_return,
            step_data=step_.data,
    )


def execute_scenario(scenario, *, sentences_to_functions):
    executed_steps = []
    failed = False
    step_return = {}
    for step_ in scenario.steps:
        if failed:
            executed = IgnoredStep(sentence=step_.sentence)
        else:
            try:
                step_return = execute_step(
                        step_,
                        sentences_to_functions=sentences_to_functions,
                        previous_step_return=step_return,
                ) or {}
            except Exception as exc:  # pylint: disable=broad-except
                failed = True
                executed = FailedStep(
                        exception=exc,
                        sentence=step_.sentence,
                )
            else:
                executed = PassedStep(sentence=step_.sentence)
        executed_steps.append(executed)

    return ExecutedScenario(
            name=scenario.name,
            description=scenario.description,
            steps=tuple(executed_steps),
    )


@dataclass(frozen=True, kw_only=True)
class Step:
    sentence: str


@dataclass(frozen=True, kw_only=True)
class FailedStep(Step):
    exception: Exception
    success = False


class PassedStep(Step):
    success = True


class IgnoredStep(Step):
    success = False


def execute_file(parsed_file: ParsedFile, /, *, steps: StepMapper):
    _ = steps
    executed_scenarios: list[ExecutedScenario] = []
    for scenario in parsed_file.scenarios:
        executed_scenario = execute_scenario(
                scenario,
                sentences_to_functions=steps,
        )
        executed_scenarios.append(executed_scenario)
    return ExecutedFile(
            scenarios=tuple(executed_scenarios),
            uri=parsed_file.uri,
            name=parsed_file.name,
            description=parsed_file.description,
    )


def run(
        *,
        map_=map,
        files: Iterable[InputFile],
        parser: ParserProto = parse,
        steps: StepMapper,
        executor: Executor = execute_file,
        reporter: Reporter[T],
) -> T:
    parsed = map_(parser, files)
    executed = map_(
            lambda parsed_file: executor(parsed_file, steps=steps),
            parsed,
    )
    return reporter(executed)


class StepMapper:

    def __init__(self):
        self._pattern_to_fn = {}

    def __call__(self, pattern):
        return lambda fn: self._add_step_fn(fn, pattern=pattern)

    def _add_step_fn(self, fn_, /, *, pattern):
        self._pattern_to_fn[re.compile(pattern)] = fn_

    def prepare_function(self, sentence):
        for pattern, fn_ in self._pattern_to_fn.items():
            if match_ := pattern.search(sentence):
                args = match_.groups()
                spec = inspect.getfullargspec(fn_)
                mapped_args = [
                    spec.annotations.get(name, lambda x: x)(value)
                    for name, value in zip(spec.args, args)
                ]
                if 'step_data' in spec.kwonlyargs:
                    return lambda step_data, **kw: fn_(
                            *mapped_args, **kw, step_data=step_data)
                return lambda step_data, **kw: fn_(*mapped_args, **kw)

        raise Exception('TODO')
