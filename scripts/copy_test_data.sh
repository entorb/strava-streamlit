#!/bin/sh
cd "$(dirname "$0")/.." || exit 1

mkdir -p data/knownLocations
mkdir -p cache

rsync tests/testdata/city-gps.dat data/
rsync tests/testdata/knownLocations/7656541.txt data/knownLocations/
rsync -r --delete tests/testdata/api-cache/ cache/
