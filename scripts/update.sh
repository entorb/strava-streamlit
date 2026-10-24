#!/bin/sh
set -e
cd "$(dirname "$0")/.."

uv remove numpy pandas pyarrow sentry-sdk streamlit XlsxWriter
uv remove --dev ruff pytest pytest-cov tomli-w vulture watchdog

uv lock --upgrade
uv sync --upgrade

# pin to old versions due to Uberspace restrictions
uv add numpy==2.2.3 pandas==2.2.3 pyarrow==20.0.0 sentry-sdk streamlit XlsxWriter
uv add --dev ruff pytest pytest-cov tomli-w vulture watchdog

uv lock --upgrade
uv sync --upgrade

python scripts/gen_requirements.py

# ruff
uv run ruff format
uv run ruff check --fix

# pre-commit
prek autoupdate --cooldown-days 7
prek run --all-files

echo DONE
