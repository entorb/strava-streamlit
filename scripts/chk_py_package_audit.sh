#!/bin/sh
set -e
cd "$(dirname "$0")/.."

out=$(mktemp)
trap 'rm -f "$out"' EXIT INT TERM

status=0
uv audit --preview-features audit >"$out" 2>&1 || status=$?

# print output in good case only if more than 2 lines
if [ $status -eq 0 ]; then
  lines=$(wc -l <"$out")
  if [ "$lines" -gt 2 ]; then
    head -n 10 "$out"
  fi
else
  head -n 100 "$out"
fi
exit $status
