import traceback
import unittest

import rumex
import rumex.utils

example_file = rumex.InputFile(
    text="""
        Name: Basic example

        Scenario: Simple arithmetics

            Given an integer 1
            When nothing is done
            Then we have an integer


        Scenario: Failing scenario

            Given a failing step...


        Scenario: Misdividing scenario

            Given division by zero


        Scenario: Passing scenario again
            Given an integer 1
    """,
    uri="in place file, just an example",
)

steps = rumex.StepMapper()


@steps("an integer")
def no_op_integer():
    pass


@steps("nothing is done")
def no_op_again():
    pass


@steps("division by zero")
def zero_div():
    return 1 / 0


class ThisShallNotPassError(Exception):
    pass


@steps("failing step")
def raise_():
    raise ThisShallNotPassError("DOH!")


def test_run_with_default_reporter():
    # This could be our test function that
    # is executed as a unit by a testing framework
    # such as Python's `unittest` or `pytest`.
    # This however might be very limitting,
    # since the default reporter will simply reraise
    # an exception generated by the first failing step.

    rumex.run(files=[example_file], steps=steps)


try:
    test_run_with_default_reporter()
except ThisShallNotPassError:
    pass
else:
    raise AssertionError(
        "We will not reach this point since an exception was raised.",
    )


def test_with_non_default_reporter():
    # The default reporter can be easily replaced
    # allowing us to perhaps generate an exception
    # group from the failed scenarios or otherwise
    # report them however we desire.

    class MyReporter:
        def __init__(self):
            self.failed_scenarios = []

        def __call__(self, executed_files):
            for file in executed_files:
                if not file.success:
                    for scenario in file.scenarios:
                        if not scenario.success:
                            self.failed_scenarios.append(scenario)

    my_reporter = MyReporter()
    rumex.run(files=[example_file], steps=steps, reporter=my_reporter)

    if my_reporter.failed_scenarios:
        _raise_on_failure(my_reporter.failed_scenarios)


def _raise_on_failure(failed_scenarios):
    msg = ["Failing scenarios:\n"]
    for scenario in failed_scenarios:
        msg.append(scenario.name + ":")
        for step_ in scenario.steps:
            if not step_.success:
                msg.extend(traceback.format_exception(step_.exception))
        msg.append("")
    raise AssertionError("\n".join(msg))


try:
    test_with_non_default_reporter()
except AssertionError as exc:
    _ERROR_MSG = str(exc)
    assert ThisShallNotPassError.__name__ in _ERROR_MSG
    assert ZeroDivisionError.__name__ in _ERROR_MSG
else:
    raise AssertionError(
        "We will not reach this point since an exception was raised.",
    )


# To be able to control what tests are executed
# we can write our own entry point that takes names of
# tags or pattern of file names to be used for filtering.
# Or, we can leverage functionality of existing frameworks
# that collect and execute tests based on their names.

# For this example, let's use Python's `unittest` framework.


def metodify(fn):
    def wrapped(self):
        """Unpack executed scenario objects.

        And fail loudly if necessary.
        """
        _ = self
        examples_results = fn()
        failed = False
        msg = [f"Failing examples in scenario {examples_results[0].name}:\n"]
        for example in examples_results:
            if not example.success:
                failed = True
                for step_ in example.steps:
                    if not step_.success:
                        msg.extend(traceback.format_exception(step_.exception))
                msg.append("")
        if failed:
            raise AssertionError("\n".join(msg))

    return wrapped


class DynamicAcceptanceTests(unittest.TestCase):
    for file, scenario, scenario_fn in rumex.utils.iter_tests(
        files=[example_file],
        steps=steps,
    ):
        locals()[f"test_{file.name}_{scenario.name}"] = metodify(scenario_fn)


suite = unittest.defaultTestLoader.loadTestsFromTestCase(
    DynamicAcceptanceTests,
)
result = unittest.TextTestRunner().run(suite)

# We had 4 scenarios
assert result.testsRun == 4  # noqa: PLR2004

# 2 were made to fail
assert len(result.failures) == 2  # noqa: PLR2004
(_, failure_msg_1), (_, failure_msg_2) = result.failures
assert ThisShallNotPassError.__name__ in failure_msg_1
assert ZeroDivisionError.__name__ in failure_msg_2
