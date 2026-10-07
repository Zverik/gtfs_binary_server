from gtfs_binary.helpers import readers
from gtfs_binary import g
from datetime import date
from rules import read_rules
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
        '-r', '--rules',
        help='Path to feed processing rules, ../feeds by default')
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

    if not options.rules or not os.path.exists(options.rules):
        gtbfiles = os.listdir(options.path)
    else:
        gtbfiles = []
        rules = read_rules(options.rules)
        for language, feeds in rules.items():
            lprefix = language + '_'
            for feed, frules in feeds.items():
                if not frules.get('skip'):
                    gtbname = f'{language}_{feed}.gtb'
                    if os.path.exists(os.path.join(options.path, gtbname)):
                        gtbfiles.append(gtbname)

    result = {}
    for gtbfile in gtbfiles:
        if not gtbfile.endswith('.gtb'):
            continue
        with open(os.path.join(options.path, gtbfile), 'rb') as f:
            footer = readers.read_footer(f)
        metadata = {
            'version': footer.build,
            'bbox_lat_lon': list(footer.bbox_lat_lon),
        }
        if footer.date:
            fdate = date(
                2000 + footer.date // 10000,
                (footer.date // 100) % 100,
                footer.date % 100,
            )
            metadata['date'] = fdate.strftime('%Y-%m-%d'),
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
