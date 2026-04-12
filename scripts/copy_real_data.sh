#!/bin/sh
cd $(dirname $0)/..

mkdir -p data/knownLocations
mkdir -p cache

rsync dataReal/city-gps.dat data/
rsync dataReal/knownLocations/* data/knownLocations/
rsync -r --delete cacheReal/ cache
