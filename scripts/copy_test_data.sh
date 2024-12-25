#!/bin/sh
mkdir -p data/knownLocations
mkdir -p cache

cp tests/testdata/city-gps.dat data/
cp tests/testdata/knownLocations/7656541.txt data/knownLocations/
cp tests/testdata/api-cache/* cache/
