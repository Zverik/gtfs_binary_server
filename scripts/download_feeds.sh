#!/bin/sh
if [ -z "${1-}" ]; then
  echo "Usage: $0 <gtfs_path>"
  exit 1
fi

wget --limit-rate=30m --mirror -l 0 --no-parent --cut-dirs=1 --no-host-directories --include-directories=gtfs --accept .zip -e robots=off --no-verbose -P "$1" https://api.transitous.org/gtfs/
