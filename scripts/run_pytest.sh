#!/bin/sh
set -e
cd "$(dirname "$0")/.."

sh scripts/copy_test_data.sh

uv run pytest --cov --cov-report=html:coverage_report --cov-report=term-missing
