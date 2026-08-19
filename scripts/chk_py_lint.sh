#!/bin/sh

# ensure we are in the root dir
cd "$(dirname "$0")/.."
out=$(mktemp)
trap 'rm -f "$out"' EXIT INT TERM

uv run --no-build ruff format --quiet >"$out" 2>&1 && uv run --no-build ruff check --fix --quiet >>"$out" 2>&1
status=$?

if [ $status -ne 0 ]; then
  echo "Issues remaining, you can try:\nuv run ruff check --fix --unsafe-fixes"
  head -n 100 "$out"
fi
exit $status
