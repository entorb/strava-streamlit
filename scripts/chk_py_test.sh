#!/bin/sh

# ensure we are in the root dir
cd "$(dirname "$0")/.."
out=$(mktemp)
trap 'rm -f "$out"' EXIT INT TERM

uv run --no-build pytest --quiet --tb=short >"$out" 2>&1
status=$?

# tail because summary is at bottom
if [ $status -ne 0 ]; then
    tail -n 100 "$out"
fi
exit $status
