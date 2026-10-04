#!/bin/sh
set -e
cd "$(dirname "$0")/.."

out=$(mktemp)
trap 'rm -f "$out"' EXIT INT TERM

status=0
uv run --no-build ruff format --quiet >"$out" 2>&1 && uv run --no-build ruff check --fix --quiet >>"$out" 2>&1 || status=$?

if [ $status -ne 0 ]; then
  printf 'Issues remaining, you can try:\nuv run ruff check --fix --unsafe-fixes\n'
  head -n 100 "$out"
fi
exit $status
