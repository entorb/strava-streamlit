#!/bin/sh

# ensure we are in the root dir
cd $(dirname $0)/..

# exit upon error
set -e

uv remove numpy pandas pyarrow sentry-sdk streamlit XlsxWriter
uv remove --dev ruff pre-commit pytest pytest-cov tomli-w watchdog

uv lock --upgrade
uv sync --upgrade

# pin to old versions due to Uberspace restrictions
uv add numpy==2.2.3 pandas==2.2.3 pyarrow==20.0.0 sentry-sdk streamlit XlsxWriter
uv add --dev ruff pre-commit pytest pytest-cov tomli-w watchdog

uv lock --upgrade
uv sync --upgrade

python scripts/gen_requirements.py

# ruff
uv run ruff format
uv run ruff check --fix

# pre-commit
uv run pre-commit autoupdate
uv run pre-commit run --all-files

echo DONE
