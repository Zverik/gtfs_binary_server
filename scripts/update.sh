#!/bin/sh
SCRIPTS=$(dirname "$0")
GTFS=/opt/gtfs
GTB=/opt/gtb

"$SCRIPTS/download_feeds.sh"
python3 "$SCRIPTS/find_modified.py"
python3 "$SCRIPTS/build_gtb.py"
python3 "$SCRIPTS/calculate_diffs.py"
