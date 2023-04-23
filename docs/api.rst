===
API
===

Protocols
---------

rumex.parsing.parser.ParserProto(Protocol)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Protocol methods
................

.. code::

    __call__(
        self,
        input_file: InputFile,
        /
    )

Text in, object out.



rumex.runner.ExecutorProto(Protocol)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Protocol methods
................

.. code::

    __call__(
        self,
        parsed: File,
        /,
        *,
        steps: StepMapperProto,
        context_maker: Callable[[], Any] | None
    )

Run the tests.



rumex.runner.StepMapperProto(Protocol)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Protocol methods
................

.. code::

    iter_steps(
        self,
        scenario: Scenario
    )

Build callables representing steps of a scenario.

Each callable takes one argument `context`.

.. rubric:: Parameters

- scenario: The scenario to which the step callables pertain.


Dataclasses
-----------

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

rumex.parsing.tokenizer.Token
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Frozen dataclass

.. code::

    rumex.parsing.tokenizer.Token(
        *,
        kind: Hashable,
        value: Any,
        line: str,
        line_num: int
    )

Every line must map to a `Token`.




Classes
-------

rumex.StepMapper
~~~~~~~~~~~~~~~~

Prepare step functions.

Methods
.......

:

----

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





Functions
---------

rumex.find_input_files
~~~~~~~~~~~~~~~~~~~~~~

.. code::

    rumex.find_input_files(
        *,
        root: Path,
        extension: str
    )

Find regular files and return them as `InputFile[s]`.

.. rubric:: Parameters

- root: Where to start searching recursively.
- extension: Extension of the files to look for.

rumex.parsing.parser.parse
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code::

    rumex.parsing.parser.parse(
        input_file: InputFile,
        *,
        state_machine: StateMachine = rumex.parsing.parser.StateMachine,
        make_builder=rumex.parsing.builder.FileBuilder,
        token_iterator=rumex.parsing.tokenizer.iter_tokens
    )

Text in, object out.



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
- parser: A callable that takes `InputFile` and returns `File`.
- executor: A callable that takes `File` `steps` and `context_maker` and returns `ExecutedFile`.
- reporter: A callable that takes the collection of all executed files. This can be as simple as raising an exception if any of the executed files is a `FailedFile`.
- map\_: Must have the same interface as the Python's built-in `map`. Custom implementation might be used to speed up file parsing or execution.

rumex.runner.execute_file
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code::

    rumex.runner.execute_file(
        parsed_file: File,
        /,
        *,
        context_maker: Callable[[], Any] | None,
        steps: StepMapperProto
    )

Executed a single test file.




Collections
-----------

rumex.parsing.parser.default_state_machine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Represents possible states of a parser.

This object is a map where keys are `State` enumerals
and values are maps where keys are `TokenKind` enumerals
and values are 2-tuples of (`State` enumeral, builder callback).

The "builder callback" objects are functions that take
two positional arguments: `builder` and a value extracted
from a token of the associated `TokenKind`.

The parser uses the state machine map in the following way:

1) Using `current_state` as a key, extracts the eligible
   state transitions from the state machine map.
2) Having token `t`, uses it to extract the 2-tuple
   from the eligible state transitions.
3) Sets `current_state` to the first value of the tuple.
4) Executes the callback, passing it a `builder` object
   and a value extracted from the token `t`.

Items
.....

- State.START

 - TokenKind.NAME_KW

  0. State.FILE_NAME
  1. :

  .. code:: python

    def set_file_name(builder, file_name):
        builder.name = file_name

 - TokenKind.BLANK_LINE

  0. State.START
  1. :

  .. code:: python

    def no_op(*_):
        pass

 - TokenKind.SCENARIO_KW

  0. State.NEW_SCENARIO
  1. :

  .. code:: python

    def new_scenario(builder, scenario_name):
        builder.new_scenario(scenario_name)

 - TokenKind.DESCRIPTION

  0. State.FILE_DESCRIPTION
  1. :

  .. code:: python

    def append_file_description(builder, line):
        builder.description.append(line)

 - TokenKind.STEP_KW

  0. State.FILE_DESCRIPTION
  1. :

  .. code:: python

    def append_file_description(builder, line):
        builder.description.append(line)


- State.FILE_NAME

 - TokenKind.DESCRIPTION

  0. State.FILE_DESCRIPTION
  1. :

  .. code:: python

    def append_file_description(builder, line):
        builder.description.append(line)

 - TokenKind.BLANK_LINE

  0. State.FILE_NAME
  1. :

  .. code:: python

    def no_op(*_):
        pass

 - TokenKind.STEP_KW

  0. State.FILE_DESCRIPTION
  1. :

  .. code:: python

    def append_file_description(builder, line):
        builder.description.append(line)

 - TokenKind.SCENARIO_KW

  0. State.NEW_SCENARIO
  1. :

  .. code:: python

    def new_scenario(builder, scenario_name):
        builder.new_scenario(scenario_name)


- State.FILE_DESCRIPTION

 - TokenKind.BLANK_LINE

  0. State.FILE_DESCRIPTION
  1. :

  .. code:: python

    def append_file_description(builder, line):
        builder.description.append(line)

 - TokenKind.DESCRIPTION

  0. State.FILE_DESCRIPTION
  1. :

  .. code:: python

    def append_file_description(builder, line):
        builder.description.append(line)

 - TokenKind.SCENARIO_KW

  0. State.NEW_SCENARIO
  1. :

  .. code:: python

    def new_scenario(builder, scenario_name):
        builder.new_scenario(scenario_name)

 - TokenKind.STEP_KW

  0. State.FILE_DESCRIPTION
  1. :

  .. code:: python

    def append_file_description(builder, line):
        builder.description.append(line)


- State.NEW_SCENARIO

 - TokenKind.BLANK_LINE

  0. State.NEW_SCENARIO
  1. :

  .. code:: python

    def no_op(*_):
        pass

 - TokenKind.STEP_KW

  0. State.STEP
  1. :

  .. code:: python

    def new_step(builder, sentence):
        builder.current_scenario_builder.new_step(sentence)

 - TokenKind.DESCRIPTION

  0. State.SCENARIO_DESCRIPTION
  1. :

  .. code:: python

    def append_scenario_description(builder, line):
        builder.current_scenario_builder.description.append(line)


- State.SCENARIO_DESCRIPTION

 - TokenKind.DESCRIPTION

  0. State.SCENARIO_DESCRIPTION
  1. :

  .. code:: python

    def append_scenario_description(builder, line):
        builder.current_scenario_builder.description.append(line)

 - TokenKind.BLANK_LINE

  0. State.SCENARIO_DESCRIPTION
  1. :

  .. code:: python

    def append_scenario_description(builder, line):
        builder.current_scenario_builder.description.append(line)

 - TokenKind.STEP_KW

  0. State.STEP
  1. :

  .. code:: python

    def new_step(builder, sentence):
        builder.current_scenario_builder.new_step(sentence)


- State.STEP

 - TokenKind.STEP_KW

  0. State.STEP
  1. :

  .. code:: python

    def new_step(builder, sentence):
        builder.current_scenario_builder.new_step(sentence)

 - TokenKind.DESCRIPTION

  0. State.STEP
  1. :

  .. code:: python

    def add_step_data(builder, data):
        builder.current_scenario_builder.current_step_builder.add_step_data(data)

 - TokenKind.TRIPLE_QUOTE

  0. State.BLOCK_OF_TEXT
  1. :

  .. code:: python

    def no_op(*_):
        pass

 - TokenKind.BLANK_LINE

  0. State.STEP
  1. :

  .. code:: python

    def no_op(*_):
        pass


- State.BLOCK_OF_TEXT

 - TokenKind.NAME_KW

  0. State.BLOCK_OF_TEXT
  1. :

  .. code:: python

    def add_text_block_line(builder, line):
        builder.current_scenario_builder.current_step_builder.add_text_block_line(
                line)

 - TokenKind.SCENARIO_KW

  0. State.BLOCK_OF_TEXT
  1. :

  .. code:: python

    def add_text_block_line(builder, line):
        builder.current_scenario_builder.current_step_builder.add_text_block_line(
                line)

 - TokenKind.STEP_KW

  0. State.BLOCK_OF_TEXT
  1. :

  .. code:: python

    def add_text_block_line(builder, line):
        builder.current_scenario_builder.current_step_builder.add_text_block_line(
                line)

 - TokenKind.BLANK_LINE

  0. State.BLOCK_OF_TEXT
  1. :

  .. code:: python

    def add_text_block_line(builder, line):
        builder.current_scenario_builder.current_step_builder.add_text_block_line(
                line)

 - TokenKind.DESCRIPTION

  0. State.BLOCK_OF_TEXT
  1. :

  .. code:: python

    def add_text_block_line(builder, line):
        builder.current_scenario_builder.current_step_builder.add_text_block_line(
                line)

 - TokenKind.TRIPLE_QUOTE

  0. State.NEW_SCENARIO
  1. :

  .. code:: python

    def no_op(*_):
        pass



rumex.parsing.tokenizer.default_tokenizers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Functions to extract line-tokens from text.

Elements
........


  0:

  .. code:: python

    def match_name(line):
        if name := match_keyword('Name', line=line):
            return TokenKind.NAME_KW, name

  1:

  .. code:: python

    def match_scenario(line):
        if name := match_keyword('Scenario', line=line):
            return TokenKind.SCENARIO_KW, name

  2:

  .. code:: python

    def match_triple_quote(line):
        if line.strip() == '"""':
            return TokenKind.TRIPLE_QUOTE, None

  3:

  .. code:: python

    def match_step(line):
        stripped = line.strip()
        if stripped.startswith(('Given ', 'When ', 'Then ', 'And ')):
            return TokenKind.STEP_KW, line

  4:

  .. code:: python

    def match_blank_line(line):
        if not line.strip():
            return TokenKind.BLANK_LINE, line

  5:

  .. code:: python

    def match_description(line):
        return TokenKind.DESCRIPTION, line



Enums
---------

rumex.parsing.parser.State
~~~~~~~~~~~~~~~~~~~~~~~~~~

Possible states of the default state machine.

Elements
........


 - START
 - FILE_NAME
 - FILE_DESCRIPTION
 - NEW_SCENARIO
 - STEP
 - BLOCK_OF_TEXT
 - SCENARIO_DESCRIPTION

rumex.parsing.tokenizer.TokenKind
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An enumeration.

Elements
........


 - NAME_KW
 - SCENARIO_KW
 - STEP_KW
 - BLANK_LINE
 - DESCRIPTION
 - TRIPLE_QUOTE
