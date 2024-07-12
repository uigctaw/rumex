#!/bin/bash

set -euo pipefail

echo -e "\nruff format:"
poetry run ruff format

echo -e "\nruff check:"
poetry run ruff check --fix

echo -e "\npytest:"
poetry run pytest tests ; echo Success!

echo -e "\nmypy:"
poetry run mypy . --show-error-codes --check-untyped-defs ; echo Success!

aspell check README.md

echo -e "\nSUCCESS!"

