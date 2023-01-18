from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Callable, Protocol, TypeAlias
import inspect
import re

from .parsing.parser import InputFile, ParsedFile, ParserProto, parse

_STEP_DATA_KWARG = 'step_data'
_SCENARIO_CONTEXT_KWARG = 'context'


class HookAlreadyRegistered(Exception):
    pass


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


ExecutedStep: TypeAlias = FailedStep | PassedStep | IgnoredStep


@dataclass(frozen=True, kw_only=True)
class ExecutedScenario:

    name: str
    description: str
    steps: tuple[ExecutedStep, ...]

    def __new__(cls, *, steps, **_):
        if all(s.success for s in steps):
            return super().__new__(PassedScenario)
        return super().__new__(FailedScenario)


class PassedScenario(ExecutedScenario):
    success = True


class FailedScenario(ExecutedScenario):
    success = False


@dataclass(frozen=True, kw_only=True)
class ExecutedFile:

    scenarios: tuple[ExecutedScenario, ...]
    uri: str
    name: str
    description: str

    def __new__(cls, *, scenarios, **_):
        if all(s.success for s in scenarios):
            return super().__new__(PassedFile)
        return super().__new__(FailedFile)


class PassedFile(ExecutedFile):
    success = True


class FailedFile(ExecutedFile):
    success = False


@dataclass(frozen=True, kw_only=True)
class _Hook:
    name: str
    fn: Callable


class _Hooks:

    def __init__(self):
        self.run_before_step = None
        self.run_before_scenario = None

    def before_step(self, fn):
        self._add_hook(fn, 'before_step')

    def before_scenario(self, fn):
        self._add_hook(fn, 'before_scenario')

    def _add_hook(self, fn, hook_name):
        run_hook_name = 'run_' + hook_name
        # pylint: disable=comparison-with-callable
        if getattr(self, run_hook_name) is None:
            setattr(self, run_hook_name, _Hook(name=hook_name, fn=fn))
        else:
            raise HookAlreadyRegistered(hook_name)


class Executor(Protocol):

    def __call__(
            self,
            parsed: ParsedFile,
            /,
            *,
            steps: StepMapper,
            context_maker,
    ) -> ExecutedFile:
        pass


def execute_scenario(
        scenario,
        *,
        scenario_context,
        step_mapper,
):
    executed_steps = []
    failed = False
    for step_sentence, fn in step_mapper.iter_steps(scenario):
        if failed:
            executed = IgnoredStep(sentence=step_sentence)
        else:
            try:
                fn(**{_SCENARIO_CONTEXT_KWARG: scenario_context})
            except Exception as exc:  # pylint: disable=broad-except
                failed = True
                executed = FailedStep(
                        exception=exc,
                        sentence=step_sentence,
                )
            else:
                executed = PassedStep(sentence=step_sentence)
        executed_steps.append(executed)

    return ExecutedScenario(
            name=scenario.name,
            description=scenario.description,
            steps=tuple(executed_steps),
    )


def execute_file(
        parsed_file: ParsedFile,
        /,
        *,
        context_maker,
        steps: StepMapper,
):
    _ = steps
    executed_scenarios: list[ExecutedScenario] = []
    for scenario in parsed_file.scenarios:
        context = context_maker()
        executed_scenario = execute_scenario(
                scenario,
                step_mapper=steps,
                scenario_context=context,
        )
        executed_scenarios.append(executed_scenario)

    return ExecutedFile(
            scenarios=tuple(executed_scenarios),
            uri=parsed_file.uri,
            name=parsed_file.name,
            description=parsed_file.description,
    )


def report(files):
    for file in files:
        if not file.success:
            raise AssertionError(file)


def run(
        *,
        map_=map,
        files: Iterable[InputFile],
        parser: ParserProto = parse,
        steps: StepMapper,
        context_maker=lambda: None,
        executor: Executor = execute_file,
        reporter=report,
):
    parsed = map_(parser, files)
    executed = map_(
            lambda parsed_file: executor(
                    parsed_file,
                    steps=steps,
                    context_maker=context_maker,
            ),
            parsed,
    )
    return reporter(executed)


class StepMapper:

    def __init__(self):
        self._hooks = _Hooks()
        self._pattern_to_fn = {}
        self.before_scenario = self._hooks.before_scenario
        self.before_step = self._hooks.before_step

    def __call__(self, pattern):
        return lambda fn: self._add_step_fn(fn, pattern=pattern)

    def _add_step_fn(self, fn, /, *, pattern):
        self._pattern_to_fn[re.compile(pattern)] = fn

    def _wrap_mapped_function(self, *, fn_spec, fn, mapped_args, step_data):

        def wrapped(context):
            kwargs = {}
            if _STEP_DATA_KWARG in fn_spec.kwonlyargs:
                kwargs[_STEP_DATA_KWARG] = step_data
            if _SCENARIO_CONTEXT_KWARG in fn_spec.kwonlyargs:
                kwargs[_SCENARIO_CONTEXT_KWARG] = context
            return fn(*mapped_args, **kwargs)

        return wrapped

    def _prepare_step(self, step_):
        sentence = step_.sentence
        for pattern, fn in self._pattern_to_fn.items():
            if match_ := pattern.search(sentence):
                args = match_.groups()
                spec = inspect.getfullargspec(fn)
                mapped_args = [
                    spec.annotations.get(name, lambda x: x)(value)
                    for name, value in zip(spec.args, args)
                ]
                return self._wrap_mapped_function(
                    fn_spec=spec,
                    fn=fn,
                    mapped_args=mapped_args,
                    step_data=step_.data,
                    )
        raise Exception('TODO')

    def iter_steps(self, scenario):
        if (hook := self._hooks.run_before_scenario):
            yield hook.name, hook.fn
        for step_ in scenario.steps:
            fn = self._prepare_step(step_)
            yield step_.sentence, fn
            if (hook := self._hooks.run_before_step):
                yield hook.name, hook.fn
