from rumex.tests import iter_tests, run_test


def _get_test(_test):
    return lambda: run_test(_test)


for test in iter_tests():
    locals()[test.__qualname__] = _get_test(test)
del test  # pylint: disable=undefined-loop-variable
