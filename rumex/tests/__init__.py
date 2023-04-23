import importlib
import pathlib

import rumex
import rumex.parsing.parser
import rumex.runner


def get_tests():
    return tuple(iter_tests())


def iter_tests():
    for file in pathlib.Path(__file__).resolve().parent.glob('test_*.py'):
        module = importlib.import_module(f'{__package__}.{file.stem}')
        for key, value in vars(module).items():
            if key.startswith('test_'):
                yield value


def run_tests():
    passed = []
    failed = []
    for test in iter_tests():
        try:
            run_test(test)
        except Exception as exc:  # pylint: disable=broad-except
            failed.append(exc)
        else:
            passed.append(test)
    return passed, failed


def run_test(
        test,
        parse=rumex.parsing.parser.parse,
        get_step_mapper=rumex.StepMapper,
        run=rumex.run,
):
    def wrapped_run(
        *,
        files,
        steps,
        context_maker=None,
        parser=parse,
        executor=rumex.runner.execute_file,
        reporter,
        map_=map,
    ):
        run(
                files=files,
                steps=steps,
                context_maker=context_maker,
                parser=parser,
                executor=executor,
                reporter=reporter,
                map_=map_,
        )
    test(
            parse=parse,
            get_step_mapper=get_step_mapper,
            run=wrapped_run,
    )
