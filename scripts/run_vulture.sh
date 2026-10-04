#!/bin/sh
set -e
cd "$(dirname "$0")/.."

uv run vulture
