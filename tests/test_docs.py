import re

from build_docs.api import build_doc as build_api_doc

from .test_consistent_version import find_project_root

EXAMPLES_DIR = find_project_root().joinpath("docs/examples")


def test_example_given_in_readme_is_same_as_the_one_in_examples_dir():
    with (
        find_project_root().joinpath("README.md").open(encoding="utf8") as fio
    ):
        readme = fio.read()

    (example_code_from_readme,) = re.search(  # type: ignore[union-attr]
        r"```python(.*)```",
        readme,
        flags=re.DOTALL,
    ).groups()

    with EXAMPLES_DIR.joinpath("from_readme.py").open(encoding="utf8") as fio:
        example_code = fio.read().strip()

    assert example_code_from_readme.strip() == example_code


def test_examples_execute_fine():
    executed = 0
    for file in EXAMPLES_DIR.glob("**/*.py"):
        with file.open(encoding="utf8") as fio:
            module_text = fio.read()
            try:
                exec(module_text, {"__file__": str(file)})  # noqa: S102
            except Exception as exc:
                raise type(exc)(file) from exc
            executed += 1
    assert executed  # sanity check


def test_api_doc_has_been_updated():
    with (find_project_root() / "docs" / "api.md").open() as fio:
        assert build_api_doc() == fio.read()
