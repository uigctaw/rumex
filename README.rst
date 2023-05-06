=====
Rumex
=====

`Behaviour Driven Development`_ (BDD) testing library.

Rumex is trying to be more of a library rather than a framework.
This approach aims to increase flexibility and reduce dependency
on design choices made by designers of alternative frameworks.

Installation
------------

.. code::

    pip install rumex


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

Perhaps the best way to discover Rumex's fetures is to look at the examples:

`docs/examples`_


API
---

For API documentation see `docs/api`_


Some alternatives
-----------------

- `behave`_

- `pytest-bdd`_


.. _`Behaviour Driven Development`:
  https://en.wikipedia.org/wiki/Behavior-driven_development

.. _`docs/examples`: docs/examples

.. _`docs/api`: docs/api.rst

.. _`behave`: https://github.com/behave/behave

.. _`pytest-bdd`: https://github.com/pytest-dev/pytest-bdd
