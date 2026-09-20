#!/bin/sh

# ensure we are in the root dir
cd "$(dirname "$0")/.." || exit 1

prek run --all-files
