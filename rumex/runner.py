from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any, Callable, Protocol, TypeAlias
import inspect
import re

from .parsing.core import InputFile, ParsedFile, ParserProto, Scenario
from .parsing.parser import parse


class RumexException(Exception):
    pass


class HookAlreadyRegistered(RumexException):
    pass


class MatchingFunctionNotFound(RumexException):
    pass


@dataclass(frozen=True, kw_only=True)
class _ExecutedStep:
    sentence: str


@dataclass(frozen=True, kw_only=True)
class FailedStep(_ExecutedStep):
    exception: Exception
    success = False


class PassedStep(_ExecutedStep):
    success = True


class IgnoredStep(_ExecutedStep):
    success = False


ExecutedStep: TypeAlias = FailedStep | PassedStep | IgnoredStep


@dataclass(frozen=True, kw_only=True)
class ExecutedScenario:

    name: str
    description: str
    steps: Sequence[ExecutedStep]
    tags: Sequence[str]
    example_number: int


class PassedScenario(ExecutedScenario):
    success = True


class SkippedScenario(PassedScenario):
    pass


class FailedScenario(ExecutedScenario):
    success = False


@dataclass(frozen=True, kw_only=True)
class ExecutedFile:

    scenarios: tuple[ExecutedScenario, ...]
    uri: str
    name: str | None
    description: str | None

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


class ContextCallable(Protocol):

    def __call__(self, context: Any) -> None:
        ...


class ExecutableStep:

    def __init__(self, *, sentence: str, callable_: ContextCallable):
        self.sentence = sentence
        self._callable = callable_

    def __call__(self, *, context: Any) -> None:
        self._callable(context=context)


@dataclass(frozen=True, kw_only=True)
class MissingStep:

    sentence: str


class StepMapperProto(Protocol):

    def iter_steps(
            self,
            scenario: Scenario,
    ) -> Iterable[ExecutableStep | MissingStep]:
        """Build callables representing steps of a scenario.

        Each callable takes one argument `context`.

        Params
        ------
        scenario: The scenario to which the step callables pertain.
        """


class ExecutorProto(Protocol):

    def __call__(
            self,
            parsed: ParsedFile,
            /,
            *,
            steps: StepMapperProto,
            context_maker: Callable[[], Any] | None,
    ) -> ExecutedFile:
        """Run the tests."""


def execute_scenario(
        scenario,
        *,
        context_maker,
        steps,
        skip_scenario_tag,
):
    executed_scenarios = []
    for example_num, scenario_steps in enumerate(
            steps.iter_steps(scenario), start=1):

        if skip_scenario_tag in scenario.tags:
            cls = SkippedScenario
            executed_steps = []
        else:
            cls, executed_steps = _execute_scenario(
                    steps=scenario_steps,
                    context_maker=context_maker,
            )

        executed_scenario = cls(
                name=scenario.name,
                description=scenario.description,
                steps=tuple(executed_steps),
                tags=scenario.tags,
                example_number=example_num,
        )
        executed_scenarios.append(executed_scenario)
    return executed_scenarios


def _execute_scenario(*, steps, context_maker):
    executed_steps = []
    failed = False
    context = context_maker()
    executed: _ExecutedStep
    for step_ in steps:
        if isinstance(step_, MissingStep):
            failed = True
            executed = FailedStep(
                exception=MatchingFunctionNotFound(step_.sentence),
                sentence=step_.sentence,
            )
        elif failed:
            executed = IgnoredStep(sentence=step_.sentence)
        else:
            try:
                step_(context=context)
            except Exception as exc:  # pylint: disable=broad-except
                failed = True
                executed = FailedStep(
                        exception=exc,
                        sentence=step_.sentence,
                )
            else:
                executed = PassedStep(sentence=step_.sentence)
        executed_steps.append(executed)
    cls = FailedScenario if failed else PassedScenario

    return cls, executed_steps


def execute_file(
        parsed_file: ParsedFile,
        /,
        *,
        context_maker: Callable[[], Any] | None,
        steps: StepMapperProto,
        skip_scenario_tag: str | None = None,
):
    """Executed a single test file.

    Params
    ------
    parsed_file: File to be executed.

    context_maker:
        Callable returning context object
        that will be passed to steps.

    steps:
        Step mapper that can generate executable steps
        for all the steps defined in the `parsed_file`.

    skip_scenario_tag:
        If a scenario in the `parsed_file` contains
        this tag, the scenario will not be executed.
    """

    context_maker = context_maker or (lambda: None)
    executed_scenarios: list[ExecutedScenario] = []

    for scenario in parsed_file.scenarios:
        executed = execute_scenario(
                scenario,
                steps=steps,
                context_maker=context_maker,
                skip_scenario_tag=skip_scenario_tag,
        )
        executed_scenarios.extend(executed)

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
        return fn

    def _wrap_mapped_function(self, *, fn_spec, fn, mapped_args, data):

        def wrapped(context):
            kwargs = {}
            if 'data' in fn_spec.kwonlyargs:
                kwargs['data'] = data
            if 'context' in fn_spec.kwonlyargs:
                kwargs['context'] = context
            return fn(*mapped_args, **kwargs)

        return wrapped

    def _prepare_step(self, *, sentence, data):
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
                    data=data,
                    )

        return None

    def iter_steps(
            self,
            scenario: Scenario,
    ) -> Iterable[ExecutableStep | MissingStep]:
        """See documentation of `StepMapperProto`."""
        for example_data in scenario.examples_data or [{}]:
            yield self._iter_steps(scenario, example_data=example_data)

    def _iter_steps(self, scenario, example_data):
        if (hook := self._hooks.run_before_scenario):
            yield ExecutableStep(sentence=hook.name, callable_=hook.fn)
        for step_ in scenario.steps:
            if (hook := self._hooks.run_before_step):
                yield ExecutableStep(sentence=hook.name, callable_=hook.fn)

            sentence = self._evaluate_sentence(
                    template=step_.sentence,
                    example_data=example_data,
            )
            data = self._evaluate_step_data(
                    template=step_.data,
                    example_data=example_data,
            )

            callable_ = self._prepare_step(sentence=sentence, data=data)

            if callable_:
                yield ExecutableStep(
                        sentence=sentence, callable_=callable_)
            else:
                yield MissingStep(sentence=sentence)

    def _evaluate_sentence(self, *, template, example_data):
        return self._evaluate_line(
                template=template, example_data=example_data)

    def _evaluate_line(self, template: str, *, example_data) -> str:
        pattern = re.compile(r'(?:^|[^\\])(?:\\\\)*(<(\w+)>)')
        line = template
        while match_ := re.search(pattern, line):
            _, end = match_.span()
            outer, key = match_.groups()
            start = end - len(outer)
            value = example_data[key]
            line = line[:start] + value + line[end:]
        return line

    def _evaluate_step_data(self, *, template, example_data):
        if template is None:
            return template

        if isinstance(template, str):
            return self._evaluate_step_text(
                    template, example_data=example_data)

        return self._evaluate_step_data_table(
                template, example_data=example_data)

    def _evaluate_step_text(self, template, *, example_data):
        return '\n'.join(
                self._evaluate_line(line, example_data=example_data)
                for line in template.splitlines()
        )

    def _evaluate_step_data_table(
            self,
            table_template: Sequence[dict[str, str]],
            *,
            example_data,
    ) -> tuple[dict[str, str], ...]:
        return tuple(
            {
                self._evaluate_line(key, example_data=example_data):
                    self._evaluate_line(value, example_data=example_data)
                for key, value in row.items()
            }
            for row in table_template
        )
