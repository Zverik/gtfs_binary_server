#!/bin/sh
wget --limit-rate=30m --mirror -l 0 --no-parent --cut-dirs=1 --no-host-directories --include-directories=gtfs --accept .zip -e robots=off https://api.transitous.org/gtfs/
