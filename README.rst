=====
Rumex
=====

`Behaviour Driven Development`_ (BDD) testing library.

Rumex is a lightweight library alternative to the `behave`_ framework.


Basic example
-------------

.. code:: python

    import rumex

    example_file = rumex.InputFile(
        text='''
            Name: Basic example

            Scenario: Simple arithmetics

                Given an integer 1
                And an integer 2
                When addition is performed
                Then the result is 3
        ''',
        uri='in place file, just an example',
    )

    steps = rumex.StepMapper()


    class Context:

        def __init__(self):
            self.integers = []
            self.sum = None


    @steps(r'an integer (\d+)')
    def store_integer(integer: int, *, context: Context):
        context.integers.append(integer)


    @steps(r'addition is performed')
    def add(*, context: Context):
        context.sum = sum(context.integers)


    @steps(r'the result is (\d+)')
    def check_result(expected_result: int, *, context: Context):
        assert expected_result == context.sum


    rumex.run(
        files=[example_file],
        steps=steps,
        context_maker=Context,
    )


More examples
~~~~~~~~~~~~~

See `docs/examples`_


API
---

rumex.run
~~~~~~~~~

.. code::

    rumex.run(
        *,
        files: Iterable[InputFile],
        steps: StepMapperProto,
        context_maker: Callable[[], Any] | None = None,
        parser: ParserProto = rumex.parsing.parser.parse,
        executor: ExecutorProto = rumex.runner.execute_file,
        reporter=rumex.runner.report,
        map_=builtins.map
    )

Rumex entry point for running tests.


.. rubric:: Parameters

- files: Files to be parsed and executed.
- steps: See `StepMapper` or `StepMapperProto` for more info.
- context_maker: A callable that returns an object that can be passed to step functions.
- parser: A callable that takes `InputFile` and returns `ParsedFile`.
- executor: A callable that takes `ParsedFile` `steps` and `context_maker` and returns `ExecutedFile`.
- reporter: A callable that takes the collection of all executed files. This can be as simple as raising an exception if any of the executed files is a `FailedFile`.
- map\_: Must have the same interface as the Python's built-in `map`. Custom implementation might be used to speed up file parsing or execution.

rumex.InputFile
~~~~~~~~~~~~~~~

Frozen dataclass

.. code::

    rumex.InputFile(
        *,
        uri: str,
        text: str
    )

Container for a test file to be parsed.

Does not have to represent an actual file.
Could be e.g. an entry in a database.


.. rubric:: Parameters

- uri: A unique identifer. If it's a file, this could be a path to this file.
- text: The content of the file.

rumex.runner.StepMapper
~~~~~~~~~~~~~~~~~~~~~~~

Prepare step functions.

Methods
.......

.. code::

    before_scenario(
        self,
        callable_: ContextCallable,
        /
    )

Register a function to execute at the start of each scenario.


.. rubric:: Parameters

- callable\_: The function to be executed.

----

.. code::

    before_step(
        self,
        callable_: ContextCallable,
        /
    )

Register a function to execute before each step.


.. rubric:: Parameters

- callable\_: The function to be executed.

----

.. code::

    __call__(
        self,
        pattern: str
    )

Create decorator for registering steps.

For example, to register a function:


.. code:: python

    def say_hello(person, *, context): ...


to match sentence "Then Bob says hello",
you can do:


.. code:: python

        steps = StepMapper()

        @steps(r'(\w+) says hello')
        def say_hello(person, *, context):
            context.get_person(person).say('hello')



.. rubric:: Parameters

- pattern: Regex pattern that will be used to match a sentence.

----

.. code::

    iter_steps(
        self,
        scenario: Scenario
    )

See documentation of `StepMapperProto`.


.. _`Behaviour Driven Development`:
  https://en.wikipedia.org/wiki/Behavior-driven_development

.. _`behave`: https://github.com/behave/behave

.. _`docs/examples`: docs/examples
