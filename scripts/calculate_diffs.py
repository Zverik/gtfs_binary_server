#!/usr/bin/env python
import os
import sys
import argparse
import logging
import subprocess
import gzip
import shutil
import json


def to_version(s: str) -> int | None:
    if '.' not in s:
        return None
    try:
        return int(s[:s.index('.')])
    except ValueError:
        return None


def get_versions(path: str, ext: str) -> list[int]:
    versions_ = [to_version(v) for v in os.listdir(path) if v.endswith(ext)]
    if None in versions_:
        sys.stderr.write(f'Found non-numeric gtb in {path}\n')
    return [v for v in versions_ if v is not None]


def decompress_version(feedpath: str, version: int, target: str):
    with gzip.open(os.path.join(feedpath, f'{version}.gtb.gz'), 'rb') as f:
        with open(target, 'wb') as ff:
            shutil.copyfileobj(f, ff)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Builds a diff sequence to the latest GTFS Binary feed')
    parser.add_argument(
        '-p', '--path', required=True,
        help='Path to the latest GTB files, expected feedname/version.gtb')
    parser.add_argument(
        '-o', '--output',
        help='Path to the generated diffs, generating '
        'feedname/from_version.gtb. Default is path/../diffs')
    # TODO: --daily / --weekly for two-step updating
    parser.add_argument(
        '-k', '--keep', type=int, default=20,
        help='Maximum diff and archive versions to keep')
    parser.add_argument(
        '-r', '--remove', action='store_true',
        help='Remove diffs that update to a non-latest version')
    parser.add_argument(
        '--bsdiff', default='bsdiff', help='Path to the bsdiff binary')
    options = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG, format='%(levelname)s:%(message)s')

    diffs = os.path.normpath(options.output or os.path.join(
        options.path, '..', 'diffs'))
    for feed in os.listdir(options.path):
        feedpath = os.path.join(options.path, feed)
        if not os.path.isdir(feedpath):
            continue

        versions = get_versions(feedpath, '.gtb.gz')
        if len(versions) < 2:
            continue

        # Prune the archive
        versions.sort()
        while len(versions) > options.keep:
            os.remove(os.path.join(feedpath, f'{versions[0]}.gtb.gz'))
            versions.pop(0)

        diffpath = os.path.join(diffs, feed)
        if not os.path.exists(diffpath):
            os.makedirs(diffpath)
        dversions = get_versions(diffpath, '.diff')
        dversions.sort()

        # A new version means there are _two_ new archives.
        need_rebuild = False
        if versions[-1] in dversions:
            logging.warning(
                'Latest version %s for feed "%s" has a diff to something, '
                'rebuilding', versions[-1], feed)
            os.remove(os.path.join(diffpath, f'{versions[-1]}.diff'))
            need_rebuild = True
        if versions[-2] not in dversions:
            need_rebuild = True

        # Rebuild the diff for every version.
        latest = os.path.join(feedpath, 'latest.gtb')
        current = os.path.join(feedpath, 'current.gtb')
        decompress_version(feedpath, versions[-1], latest)
        for version in versions[:-1]:
            diff_file = os.path.join(diffpath, f'{version}.diff')
            try:
                os.remove(diff_file)
            except OSError:
                pass  # ok if no
            decompress_version(feedpath, version, current)
            logging.debug('Running bsdiff %s %s %s', current, latest, diff_file)
            p = subprocess.run(
                [options.bsdiff, current, latest, diff_file],
                check=False, capture_output=True)
            os.remove(current)
            if p.returncode:
                logging.error(
                    'Bsdiff failed on feed %s version %s with code %s: %s',
                    feed, version, p.returncode, p.stderr)
        os.remove(latest)

        # Remove old diffs.
        if options.remove:
            for version in dversions:
                if version not in versions:
                    os.remove(os.path.join(diffpath, f'{version}.diff'))

        # Prepare the version catalog for the feed.
        catalog = {
            'latest': versions[-1],
            'diffs': get_versions(diffpath, '.diff'),
        }
        with open(os.path.join(diffpath, 'versions.json'), 'w') as f:
            json.dump(catalog, f)
