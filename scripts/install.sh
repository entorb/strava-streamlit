#!/bin/sh
set -e
cd "$(dirname "$0")/.."

uv lock --upgrade
uv sync --upgrade

# extract package info to requirements.txt
# uv export --format requirements.txt --no-dev --no-hashes -o requirements.txt
python scripts/gen_requirements.py
