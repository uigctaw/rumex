#!/bin/bash

set -euo pipefail

echo -e "\nPytest:"
poetry run pytest ; echo Success!
echo -e "\nBandit:"
poetry run bandit -c pyproject.toml -r . ; echo Success!
echo -e "\nMypy:"
poetry run mypy . --show-error-codes ; echo Success!
echo -e "\nFlake8:"
poetry run flake8 --per-file-ignores="rumex/__init__.py:F401" . ; echo Success!
echo -e "\nPylint rumex:"
poetry run pylint rumex ; echo Success!
echo -e "\nPylint tests:"
poetry run pylint tests --disable=unbalanced-tuple-unpacking ; echo Success!
echo -e "\nPylint docs:"
poetry run pylint docs --disable="duplicate-code"; echo Success!

echo -e "\nSUCCESS!"

