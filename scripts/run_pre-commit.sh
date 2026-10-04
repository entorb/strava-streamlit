#!/bin/sh
set -e
cd "$(dirname "$0")/.."

prek run --all-files
