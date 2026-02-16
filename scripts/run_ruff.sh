#!/bin/sh

# ensure we are in the root dir
cd $(dirname $0)/..

uv run ruff check --fix
uv run ruff format
