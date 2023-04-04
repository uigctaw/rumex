import traceback

from rumex.tests import run_tests


def test_all():
    passed, failed = run_tests()
    assert passed or failed  # sanity check

    if failed:
        formatted = '\n\n'.join(
            '\n'.join(traceback.format_exception(exc)) for exc in failed
        )
        raise AssertionError(f'{len(failed)} test(s) failed:\n{formatted}')
