#!/bin/bash
set -e -u
SCRIPTS="$(dirname "$0")"
PYTHON="${PYTHON:-python3}"
GTFS="${GTFS:-/var/gtfs}"
GTB="${GTB:-/var/www/gtb}"
MAX_GTFS_ZIP_MB=${MAX_GTFS_ZIP_MB:-100}
KEEP_DIFFS=${KEEP_DIFFS:-20}
BSDIFF=${BSDIFF:-bsdiff}
RULES="$SCRIPTS/../feeds"

"$SCRIPTS/download_feeds.sh" "$GTFS"
"$PYTHON" "$SCRIPTS/download_extra.py" --gtfs "$GTFS" --rules "$RULES"
"$PYTHON" "$SCRIPTS/find_modified.py" --path "$GTFS" --output "$GTFS/updated.lst"
"$PYTHON" "$SCRIPTS/build_gtb.py" --gtfs "$GTFS" --output "$GTB" --list "$GTFS/updated.lst" \
  --rules "$RULES" --max $MAX_GTFS_ZIP_MB --verbose
"$PYTHON" "$SCRIPTS/calculate_diffs.py" --path "$GTB/archive" --output "$GTB/diffs" \
  --keep $KEEP_DIFFS --bsdiff "$BSDIFF"
"$PYTHON" "$SCRIPTS/generate_overview.py" --path "$GTB" --output "$GTB/feeds.json" \
  --rules "$RULES" ${BASE_URL+--url "$BASE_URL"}
