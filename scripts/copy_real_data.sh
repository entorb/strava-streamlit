#!/bin/sh
cp dataReal/city-gps.dat data/
cp dataReal/knownLocations/* data/knownLocations/
rm -r cache
cp -r cacheReal cache
