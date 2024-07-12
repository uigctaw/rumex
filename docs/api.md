
# API

## Protocols

```python
class ParserProto(Protocol):
    def __call__(self, input_file: InputFile, /) -> ParsedFile:
        """Text in, object out."""
```

```python
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
```

```python
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
```


## Dataclasses

```python
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
```


## Classes

```python
class StepMapper:
    """Prepare step functions."""

    def before_scenario(self, callable_: ContextCallable, /):
        """Register a function to execute at the start of each scenario.

        Params
        ------
        callable_: The function to be executed.

        Raises
        ------
        HookAlreadyRegisteredError:
            When this decorator is used more than once.

        """

    def before_step(self, callable_: ContextCallable, /):
        """Register a function to execute before each step.

        Params
        ------
        callable_: The function to be executed.

        Raises
        ------
        HookAlreadyRegisteredError:
            When this decorator is used more than once.

        """

    def iter_steps(
        self,
        scenario: Scenario,
    ) -> Iterable[ExecutableStep | MissingStep]:
        """See documentation of `StepMapperProto`."""
```


## Functions

```python
def find_input_files(
    *,
    root: pathlib.Path,
    extension: str,
) -> Sequence[InputFile]:
    """Find regular files and return them as `InputFile[s]`.

    Params
    ------
    root: Where to start searching recursively.
    extension: Extension of the files to look for.
    """
```

```python
def run(  # noqa: PLR0913
    *,
    files: Iterable[InputFile],
    steps: StepMapperProto,
    context_maker: Callable[[], Any] | None = None,
    parser: ParserProto = parse,
    executor: ExecutorProto = execute_file,
    reporter=report,
    map_=map,
):
    """Entry point for running tests.

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
```

```python
def execute_file(
    parsed_file: ParsedFile,
    /,
    *,
    context_maker: Callable[[], Any] | None,
    steps: StepMapperProto,
    skip_scenario_tag: str | None = None,
):
    """Execute a single test file.

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
```
