#!/bin/sh
set -e
cd "$(dirname "$0")/.."

APP_ENV=Local uv run -m streamlit run src/main.py
