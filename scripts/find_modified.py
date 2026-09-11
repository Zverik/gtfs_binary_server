#!/usr/bin/env python3
import os
import argparse
import sys
from zipfile import ZipFile
from hashlib import md5


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Finds differences in downloaded files (only zips)')
    parser.add_argument('-p', '--path', help='Path to the downloaded files, current by default')
    parser.add_argument('-s', '--hashes', help='File to keep the hashes in, located in the file path by default, created if missing')
    parser.add_argument('-o', '--output', help='Where to write a list of changed files, stdout by default')
    options = parser.parse_args()

    path = options.path or '.'
    hashfile = options.hashes or os.path.join(path, 'hashes.lst')
    hashes: dict[str, str] = {}

    if os.path.exists(hashfile):
        with open(hashfile, 'r') as f:
            for line in f:
                parts = [p.strip() for p in line.split('\t', 1)]
                if len(parts) == 2:
                    hashes[parts[0]] = parts[1]

    changed = sys.stdout if not options.output else open(options.output, 'w')
    for filename in os.listdir(path):
        if os.path.isfile(os.path.join(path, filename)) and '.zip' in filename:
            try:
                h = md5()
                with ZipFile(os.path.join(path, filename), 'r') as z:
                    for info in z.infolist():
                        if info.is_dir():
                            continue
                        h.update(info.filename.encode())
                        h.update(info.file_size.to_bytes(8, 'big'))
                        if info.CRC:
                            h.update(info.CRC.to_bytes(4))
                digest = h.hexdigest().lower()
                if hashes.get(filename) != digest:
                    print(filename, file=changed)
                    hashes[filename] = digest

            except Exception as e:
                sys.stderr.write(f'Could not open {filename} as a zip file: {e}\n')

    if hashes:
        with open(hashfile, 'w') as f:
            for filename, digest in hashes.items():
                print(f'{filename}\t{digest}', file=f)
