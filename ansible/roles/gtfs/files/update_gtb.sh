#!/bin/bash
export GTFS=/var/gtfs
export GTB=/var/www/gtb
export PYTHON=/opt/gtfs/.venv/bin/python

/opt/gtfs/scripts/update.sh
