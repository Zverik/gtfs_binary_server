from gtfs_binary.helpers import readers
from gtfs_binary import g
import os
import argparse
import json
import sys


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Generates metadata json for a list of GTFS Bnary files')
    parser.add_argument(
        '-p', '--path', required=True,
        help='Path to the latest GTB files')
    parser.add_argument(
        '-o', '--output',
        help='Path to the resulting JSON, stdout by default')
    parser.add_argument(
        '-u', '--url',
        help='Base URL for feeds to add to the metadata')
    options = parser.parse_args()

    if options.url:
        url = options.url
        if not url.endswith('/'):
            url += '/'
    else:
        url = ''

    result = {}
    for gtbfile in os.listdir(options.path):
        if not gtbfile.endswith('.gtb'):
            continue
        with open(os.path.join(options.path, gtbfile), 'rb') as f:
            footer = readers.read_footer(f)
        metadata = {
            'version': footer.date,
            'bbox_lat_lon': list(footer.bbox_lat_lon),
        }
        if footer.title:
            metadata['title'] = footer.title
        if footer.title_en:
            metadata['title_en'] = footer.title_en
        if url:
            metadata['url'] = url + gtbfile
        shape_blocks = [b for b in footer.blocks
                        if b.block == g.Block.B_SHAPES]
        metadata['has_shapes'] = len(shape_blocks) > 0
        result[gtbfile[:gtbfile.index('.')]] = metadata

    out = sys.stdout if not options.output else open(options.output, 'w')
    json.dump(result, out)
