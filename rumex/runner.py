from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Callable, Protocol, TypeAlias
import inspect
import re

from .parsing.parser import (
        InputFile, ParsedFile, ParserProto, Scenario, parse)

_STEP_DATA_KWARG = 'step_data'


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
    fn: Callable[[Any], None]


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


class ExecutorProto(Protocol):

    def __call__(
            self,
            parsed: ParsedFile,
            /,
            *,
            steps: StepMapperProto,
            context_maker: Callable[[], Any] | None,
    ) -> ExecutedFile:
        pass


def execute_scenario(
        scenario,
        *,
        context,
        steps,
):
    executed_steps = []
    failed = False
    for executable_step in steps.iter_steps(scenario):
        if failed:
            executed = IgnoredStep(sentence=executable_step.sentence)
        else:
            try:
                executable_step(context=context)
            except Exception as exc:  # pylint: disable=broad-except
                failed = True
                executed = FailedStep(
                        exception=exc,
                        sentence=executable_step.sentence,
                )
            else:
                executed = PassedStep(sentence=executable_step.sentence)
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
        context_maker: Callable[[], Any] | None,
        steps: StepMapperProto,
):
    context_maker = context_maker or (lambda: None)
    executed_scenarios: list[ExecutedScenario] = []
    for scenario in parsed_file.scenarios:
        context = context_maker()
        executed_scenario = execute_scenario(
                scenario,
                steps=steps,
                context=context,
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
        files: Iterable[InputFile],
        steps: StepMapperProto,
        context_maker: Callable[[], Any] | None = None,
        parser: ParserProto = parse,
        executor: ExecutorProto = execute_file,
        reporter=report,
        map_=map,
):
    """Rumex entry point for running tests.

    Params
    ------
    files: Files to be parsed and executed.

    steps: See `StepMapper` or `StepMapperProto` for more info.

    context_maker:
        A callable that returns an object that can be passed
        to step functions.

    parser:
        A callable that takes `InputFile` and returns `ParsedFile`.

    executor:
        A callable that takes `ParsedFile`
        `steps` and `context_maker` and returns `ExecutedFile`.

    reporter:
        A callable that takes the collection of all executed files.
        This can be as simple as raising an exception if any
        of the executed files is a `FailedFile`.

    map_:
        Must have the same interface as the Python's built-in `map`.
        Custom implementation might be used to speed up
        file parsing or execution.
    """
    parsed_files = map_(parser, files)
    executed = map_(
            lambda parsed_file: executor(
                    parsed_file,
                    steps=steps,
                    context_maker=context_maker,
            ),
            parsed_files,
    )
    return reporter(executed)


class ContextCallable(Protocol):

    def __call__(self, context: Any) -> None:
        ...


class ExecutableStep:

    def __init__(self, *, sentence: str, callable_: ContextCallable):
        self.sentence = sentence
        self._callable = callable_

    def __call__(self, *, context: Any) -> None:
        self._callable(context=context)


class StepMapperProto(Protocol):

    def iter_steps(self, scenario: Scenario) -> Iterable[ExecutableStep]:
        """Build callables representing steps of a scenario.

        Each callable takes one argument `context`.

        Params
        ------
        scenario: The scenario to which the step callables pertain.
        """


class StepMapper:
    """Prepare step functions."""

    def __init__(self):
        self._hooks = _Hooks()
        self._pattern_to_fn = {}

    def before_scenario(self, callable_: ContextCallable, /):
        """Register a function to execute at the start of each scenario.

        Params
        ------
        callable_: The function to be executed.

        Raises
        ------
        HookAlreadyRegistered:
            When this decorator is used more than once.
        """
        return self._hooks.before_scenario(callable_)

    def before_step(self, callable_: ContextCallable, /):
        """Register a function to execute before each step.

        Params
        ------
        callable_: The function to be executed.

        Raises
        ------
        HookAlreadyRegistered:
            When this decorator is used more than once.
        """
        return self._hooks.before_step(callable_)

    def __call__(self, pattern: str):
        """Create decorator for registering steps.

        For example, to register a function:

        ```
            def say_hello(person, *, context): ...
        ```

        to match sentence "Then Bob says hello",
        you can do:

        ```
            steps = StepMapper()

            @steps(r'(\\w+) says hello')
            def say_hello(person, *, context):
                context.get_person(person).say('hello')
        ```

        Params
        ------
        pattern:
            Regex pattern that will be used to match a sentence.

        Returns
        -------
        Decorator for registering a function as a step.
        """
        return lambda fn: self._add_step_fn(fn, pattern=pattern)

    def _add_step_fn(self, fn, /, *, pattern):
        self._pattern_to_fn[re.compile(pattern)] = fn

    def _wrap_mapped_function(self, *, fn_spec, fn, mapped_args, step_data):

        def wrapped(context):
            kwargs = {}
            if _STEP_DATA_KWARG in fn_spec.kwonlyargs:
                kwargs[_STEP_DATA_KWARG] = step_data
            if 'context' in fn_spec.kwonlyargs:
                kwargs['context'] = context
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

    def iter_steps(self, scenario: Scenario) -> Iterable[ExecutableStep]:
        """See documentation of `StepMapperProto`."""
        if (hook := self._hooks.run_before_scenario):
            yield ExecutableStep(sentence=hook.name, callable_=hook.fn)
        for step_ in scenario.steps:
            if (hook := self._hooks.run_before_step):
                yield ExecutableStep(sentence=hook.name, callable_=hook.fn)
            fn = self._prepare_step(step_)
            yield ExecutableStep(sentence=step_.sentence, callable_=fn)
