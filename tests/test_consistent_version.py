import pathlib
import toml

from rumex import __version__

THIS_FOLDER = pathlib.Path(__file__).resolve().parent


def _find_project_root():
    path = THIS_FOLDER
    for _ in range(10):  # aribtrary max depth
        if path.joinpath('__root__').exists():
            return path
        path = path.parent
    raise RuntimeError('Did not find project __root__ file.')


def test_pyproject_and_package_versions_are_the_same():
    root = _find_project_root()
    with root.joinpath('pyproject.toml').open(encoding='utf-8') as fio:
        file = toml.load(fio)

    assert file['tool']['poetry']['version'] == __version__
