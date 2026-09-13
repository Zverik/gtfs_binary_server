import os
from gtfs_binary import pack
from split_gtfs import split
import argparse
import yaml
import gzip
import shutil
import logging


def convert_feed(source: str, rules: dict, target_path: str):
    basename = os.path.basename(source)
    basename = (basename if '.' not in basename
                else basename[:basename.index('.')])
    gtb_file = f'{basename}.gtb'
    gtb_full = os.path.join(target_path, gtb_file)
    follows = gtb_full if os.path.exists(gtb_full) else '0'
    version = pack(source, gtb_full, follows=follows, metadata=rules)

    # Gzip the file into the archive
    archive_path = os.path.join(
        os.path.normpath(target_path), 'archive', basename)
    if not os.path.exists(archive_path):
        os.makedirs(archive_path)
    archive = os.path.join(archive_path, f'{version}.gtb.gz')
    with open(gtb_full, 'rb') as f:
        with gzip.open(archive, 'wb') as ff:
            shutil.copyfileobj(f, ff)


def merge_rules(grules: dict, frules: dict) -> dict:
    result = {}
    for k in ('realtime', 'ticket_info'):
        value = frules.get(k, grules.get(k))
        if value:
            result[k] = value
    for k in ('title', 'title_en'):
        if k in frules:
            if k in grules:
                result[k] = f'{frules[k]}, {grules[k]}'
            else:
                result[k] = frules[k]
    return result


def inline_info(rules: dict, rules_path: str):
    for ti in rules.get('ticket_info', []):
        if 'file' in ti:
            infopath = os.path.join(rules_path, 'meta', ti)
            with open(infopath, 'r') as f:
                ti['content'] = f.read()


def merge_feeds(feeds: list[str], target: str):
    raise NotImplementedError('Merging is not implemented yet')


def split_feed(source: str, rules: dict, rules_path: str, target: str):
    agencies = [str(s) for s in rules.get('agencies', [])]
    geometry = None if 'geojson' in rules else os.path.join(
        rules_path, 'meta', rules['geojson'])
    polygons = [str(s) for s in rules.get('polygons', [])]
    negate = rules.get('negate', False)
    split(source, target, agencies, geometry, polygons, negate)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Builds GTFS Binary')
    parser.add_argument(
        '-g', '--gtfs', required=True,
        help='Path to downloaded GTFS files')
    parser.add_argument(
        '-o', '--output', required=True,
        help='Path to GTFS Binary files')
    parser.add_argument(
        '-l', '--list',
        help='List of changed feeds to limit the number of processed files')
    parser.add_argument(
        '-r', '--rules',
        help='Path to feed processing rules, ../feeds by default')
    parser.add_argument(
        '-m', '--max', type=int,
        help='Maximum size of a zip file in MB to be processed')
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Verbose logging')
    options = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if options.verbose else logging.WARNING,
        format='%(levelname)s:%(message)s')

    # Read rules
    rules: dict[str, dict] = {}
    rules_path = options.rules or os.path.join(
        os.path.dirname(__file__), '..', 'feeds')
    rules_list = [f for f in os.listdir(rules_path) if f[-5:] == '.yaml']
    if not rules_list:
        raise IOError(f'No rules in {rules_path}')
    for rulefile in rules_list:
        with open(os.path.join(rules_path, rulefile), 'r') as f:
            rules[rulefile[:rulefile.index('.')]] = yaml.safe_load(f)

    # Filter out feeds to big.
    full_list = [f for f in os.listdir(options.gtfs)
                 if f.endswith('.gtfs.zip')]
    if options.max and options.max > 0:
        max_bytes = options.max * 1024 * 1024
        full_list = [f for f in full_list if os.stat(
            os.path.join(options.gtfs, f)).st_size <= max_bytes]

    # Read list of gtfs files
    if options.list:
        gtfs_list: list[str] = []
        with open(options.list, 'r') as f:
            for line in f:
                filename = line.strip()
                if filename not in full_list:
                    logging.warning(
                        f'File {filename} is missing in the full list')
                else:
                    gtfs_list.append(filename)
    else:
        gtfs_list = full_list

    for language, feeds in rules.items():
        lprefix = language + '_'
        to_process = set(f for f in gtfs_list if f.startswith(lprefix))
        if not to_process:
            continue

        grules = feeds.get('_agencies', {})

        used_for_splitting = set[str]()
        for feed, frules in feeds.items():
            if feed.startswith('_'):
                continue
            feedfile = f'{lprefix}{feed}.gtfs.zip'
            feedpath = os.path.join(options.gtfs, feedfile)
            rules = merge_rules(grules, frules)
            inline_info(rules, rules_path)

            if 'merge' in frules:
                if frules['merge'] == 'all':
                    to_merge = [f for f in full_list if f.startswith(lprefix)]
                else:
                    to_merge = [
                        f'{lprefix}{f}.gtfs.zip' for f in frules['merge']]
                    if any(f not in full_list for f in to_merge):
                        raise Exception(
                            'Some of the files to merge not found '
                            f'for {language}_{feed}')

                if any(f in gtfs_list for f in to_merge):
                    logging.debug(
                        'Merging %s feeds into %s', len(to_merge), feedfile)
                    merge_feeds(to_merge, feedpath)
                    convert_feed(feedpath, rules, options.output)
                    os.remove(feedpath)
                    to_process.difference_update(to_merge)

            elif 'split' in frules:
                source = f'{lprefix}{frules["source"]}.gtfs.zip'
                if source in gtfs_list:
                    logging.debug('Splitting %s from %s', feedfile, source)
                    splitpath = os.path.join(options.gtfs, source)
                    split_feed(splitpath, frules, rules_path, feedpath)
                    convert_feed(feedpath, rules, options.output)
                    os.remove(feedpath)
                    used_for_splitting.add(source)

            elif frules.get('skip'):
                logging.debug('Skipping %s', feedfile)
                to_process.discard(feedfile)

            else:
                if feedfile in to_process:
                    # Simple conversion with added metadata
                    logging.debug('Converting feed %s', feedfile)
                    convert_feed(feedpath, rules, options.output)
                    to_process.remove(feedfile)

        to_process -= used_for_splitting
        for feedfile in to_process:
            # Converting the rest of the feeds with no metadata
            logging.debug('Converting feed %s without metadata', feedfile)
            convert_feed(
                os.path.join(options.gtfs, feedfile), {}, options.output)
