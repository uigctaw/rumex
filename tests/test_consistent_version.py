import pathlib
import toml

from rumex import __version__

PYPROJECT_FILE = 'pyproject.toml'
THIS_FOLDER = pathlib.Path(__file__).resolve().parent


def find_project_root():
    path = THIS_FOLDER
    for _ in range(10):  # aribtrary max depth
        if path.joinpath(PYPROJECT_FILE).exists():
            return path
        path = path.parent
    raise RuntimeError(f'Did not find {PYPROJECT_FILE} file.')


def test_pyproject_and_package_versions_are_the_same():
    root = find_project_root()
    with root.joinpath(PYPROJECT_FILE).open(encoding='utf8') as fio:
        file = toml.load(fio)

    assert file['tool']['poetry']['version'] == __version__
