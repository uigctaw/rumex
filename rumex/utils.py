from collections.abc import Iterable, Sequence
import glob
import pathlib

from .parsing.parser import InputFile


def find_input_files(
        *, root: pathlib.Path, extension: str) -> Sequence[InputFile]:
    """Find regular files and return them as `InputFile[s]`.

    Params
    ------
    root: Where to start searching recursively.
    extension: Extension of the files to look for.
    """
    return list(iter_input_files(root=root, extension=extension))


def iter_input_files(
        *, root: pathlib.Path, extension: str) -> Iterable[InputFile]:
    for file_name in glob.glob('*.' + extension, root_dir=root):
        file = root.joinpath(file_name)
        with file.open(encoding='utf8') as fio:
            text = fio.read()
        yield InputFile(text=text, uri=str(file))
    for dir_ in root.glob('*/'):
        yield from iter_input_files(root=dir_, extension=extension)
