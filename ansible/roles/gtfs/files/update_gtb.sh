#!/bin/bash
export GTFS=/var/gtfs
export GTB=/var/www/gtb
export PYTHON=/opt/gtfs/.venv/bin/python

cd /opt/gtfs/server/scripts
git pull
./update.sh > /var/log/gtb/update.log 2>/var/log/gtb/errors.log
