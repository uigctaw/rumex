import pathlib
import sys

from modoc import get_doc

from rumex import (
    ExecutorProto,
    InputFile,
    ParserProto,
    StepMapper,
    StepMapperProto,
    execute_file,
    find_input_files,
    run,
)

_TEMPLATE = """
# API

## Protocols

{ParserProto}

{ExecutorProto}

{StepMapperProto}


## Dataclasses

{InputFile}


## Classes

{StepMapper}


## Functions

{find_input_files}

{run}

{execute_file}
"""

_inputs = {
    "ParserProto": ParserProto,
    "ExecutorProto": ExecutorProto,
    "StepMapperProto": StepMapperProto,
    "InputFile": InputFile,
    "StepMapper": StepMapper,
    "find_input_files": find_input_files,
    "run": run,
    "execute_file": execute_file,
}


def _comdify(text):
    return "```python\n" + text + "\n```"


def build_doc():
    return _TEMPLATE.format(
        **{k: _comdify(get_doc(v)) for k, v in _inputs.items()},
    )


if __name__ == "__main__":
    with pathlib.Path(sys.argv[1]).open(mode="w") as fio:
        fio.write(build_doc())
