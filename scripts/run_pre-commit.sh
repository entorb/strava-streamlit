#!/bin/sh

# ensure we are in the root dir
cd $(dirname $0)/..

uv run pre-commit run --all-files
