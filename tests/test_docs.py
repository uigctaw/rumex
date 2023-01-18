import textwrap

from .test_consistent_version import find_project_root

EXAMPLES_DIR = find_project_root().joinpath('docs/examples')


def test_example_given_in_readme_is_same_as_the_one_in_examples_dir():
    with find_project_root().joinpath(
            'README.rst').open(encoding='utf8') as fio:
        readme = fio.read().replace('\t', '    ')

    example_code_lines_from_readme = []
    in_example_code_header = False
    in_example_code = False
    for line in readme.splitlines():
        if line.startswith('Basic example'):
            in_example_code_header = True
            continue
        if in_example_code_header:
            if line.startswith('..'):
                in_example_code = True
                in_example_code_header = False
            continue
        if in_example_code and line.startswith('..'):
            break
        if in_example_code:
            example_code_lines_from_readme.append(line)

    example_code_from_readme = textwrap.dedent(
            '\n'.join(example_code_lines_from_readme)).strip()

    with EXAMPLES_DIR.joinpath('from_readme.py').open(encoding='utf8') as fio:
        example_code = fio.read().strip()

    assert example_code_from_readme == example_code


def test_examples_execute_fine():
    executed = 0
    for file in EXAMPLES_DIR.glob('*.py'):
        with file.open(encoding='utf8') as fio:
            module_text = fio.read()
            # pylint: disable=exec-used
            try:
                exec(module_text)  # nosec exec_used
            except Exception as exc:
                raise type(exc)(file) from exc
            executed += 1
    assert executed  # sanity check
