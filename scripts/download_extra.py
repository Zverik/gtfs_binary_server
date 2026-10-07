import argparse
import logging
import requests
import yaml
import os


def read_rules(path: str | None) -> dict[str, dict]:
    rules: dict[str, dict] = {}
    rules_path = path or os.path.join(
        os.path.dirname(__file__), '..', 'feeds')
    rules_list = [f for f in os.listdir(rules_path) if f[-5:] == '.yaml']
    if not rules_list:
        raise IOError(f'No rules in {rules_path}')
    for rulefile in rules_list:
        with open(os.path.join(rules_path, rulefile), 'r') as f:
            rules[rulefile[:rulefile.index('.')]] = yaml.safe_load(f)
    return rules


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Builds GTFS Binary')
    parser.add_argument(
        '-g', '--gtfs', required=True,
        help='Path to downloaded GTFS files')
    parser.add_argument(
        '-r', '--rules',
        help='Path to feed processing rules, ../feeds by default')
    parser.add_argument(
        '-v', '--verbose', action='store_true', help='Verbose logging')
    options = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if options.verbose else logging.WARNING,
        format='%(levelname)s:%(message)s')

    rules = read_rules(options.rules)
    for language, feeds in rules.items():
        lprefix = language + '_'
        for feed, frules in feeds.items():
            download = frules.get('download')
            if not download:
                continue
            if isinstance(download, str):
                download = {'url': download}
            feedfile = f'{lprefix}{feed}.gtfs.zip'
            feedpath = os.path.join(options.gtfs, feedfile)
            logging.debug(
                'Downloading %s to %s', download['url'], feedfile)
            # https://docs.python-requests.org/en/latest/user/quickstart/#raw-response-content
            stream = requests.get(download['url'], stream=True)
            with open(feedpath, 'wb') as f:
                for chunk in stream.iter_content(chunk_size=4096):
                    f.write(chunk)
