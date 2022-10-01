#!/bin/bash

set -e

poetry run pytest
poetry run bandit -c pyproject.toml -r .
poetry run mypy . --show-error-codes
poetry run flake8 .
poetry run pylint rumex
poetry run pylint tests --disable=unbalanced-tuple-unpacking

echo "SUCCESS!"

