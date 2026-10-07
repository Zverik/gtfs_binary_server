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
