import pathlib
from collections.abc import Callable, Iterable, Iterator, Sequence

from . import runner
from .parsing.parser import InputFile, ParsedFile


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
    return list(iter_input_files(root=root, extension=extension))


def iter_input_files(
    *,
    root: pathlib.Path,
    extension: str,
) -> Iterable[InputFile]:
    for dir_path, _, file_names in root.walk():
        for file_name in file_names:
            file = dir_path / file_name
            if file.suffix in (extension, "." + extension):
                with file.open(encoding="utf8") as fio:
                    text = fio.read()
                yield InputFile(text=text, uri=str(file))


def iter_tests(
    *,
    files,
    steps,
    context_maker=None,
) -> Iterator[
    tuple[
        ParsedFile,
        runner.Scenario,
        Callable[[], tuple[runner.ExecutedScenario]],
    ]
]:
    """Create zero parameter callables for each scenario."""
    context_maker = context_maker or (lambda: None)

    def get_scenario_fn(scenario, *, cm, steps_):
        return lambda: runner.execute_scenario(
            scenario,
            steps=steps_,
            context_maker=cm,
            skip_scenario_tag=None,
        )

    def execute_file(
        parsed_file,
        /,
        *,
        context_maker,
        steps,
    ):
        scenario_fns = [
            (
                scenario,
                get_scenario_fn(scenario, cm=context_maker, steps_=steps),
            )
            for scenario in parsed_file.scenarios
        ]
        return parsed_file, scenario_fns

    files_and_scenario_fns = []

    def gather(result):
        files_and_scenario_fns.extend(result)

    runner.run(
        files=files,
        steps=steps,
        context_maker=context_maker,
        executor=execute_file,
        reporter=gather,
    )

    for file, scenario_fns in files_and_scenario_fns:
        for scenario, scenario_fn in scenario_fns:
            yield file, scenario, scenario_fn
