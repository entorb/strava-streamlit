#!/bin/sh
set -e
cd "$(dirname "$0")/.."

echo "## Python Packages"
# bump [project].dependencies (==) to latest; dev group is bumped by Renovate (tools-py),
# uv upgrade cannot yet do dependency groups (astral-sh/uv#20783)
uv upgrade
uv sync --no-build --upgrade

uv run --no-build python scripts/gen_requirements.py

echo "## Code checks"
echo "### Prek update"
prek update --cooldown-days 7

echo "### run_checks.sh"
./scripts/run_checks.sh

echo "## Git"
if [ -n "$(git status --porcelain)" ]; then
  echo "### git push"
  FILES="pyproject.toml uv.lock .pre-commit-config.yaml .python-version"
  # shellcheck disable=SC2086
  git add $FILES
  # shellcheck disable=SC2086
  git diff --staged --quiet || git commit -m "chore(deps): Package update" -- $FILES
  git push
fi

echo "update DONE, not yet deployed"
