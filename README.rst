=====
Rumex
=====

`Behaviour Driven Development`_ (BDD) testing library.

Rumex is a lightweight library alternative to an existing framework `behave`_.


Basic example
-------------

.. code:: python

	import rumex

	example_file = rumex.InputFile(
		text='''
			Name: Example file

			Scenario: Simple arithmetics

				Given an integer 1
				And an integer 2
				When addition is performed
				Then the result is 3
		''',
		uri='in place file, just an example',
	)

	steps = rumex.StepMapper()


	@steps(r'an integer (\d+)')
	def store_integer(integer: int, integers=None):
		integers = integers or []
		integers.append(integer)
		return dict(integers=integers)


	@steps(r'addition is performed')
	def add(integers):
		return dict(result=sum(integers))


	@steps(r'the result is (\d+)')
	def check_result(expected_result: int, *, result):
		assert expected_result == result


	rumex.run(
		files=[example_file],
		steps=steps,
	)


.. _`Behaviour Driven Development`:
  https://en.wikipedia.org/wiki/Behavior-driven_development

.. _`behave`: https://github.com/behave/behave
