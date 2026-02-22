import sys
import pathlib
import logging
import dataclasses


import yaml


CONFIG_FILE = pathlib.Path('config.yaml')


@dataclasses.dataclass
class Target:
    type: str
    target: str
    timeout_millis: int = 5000
    interval_millis: int = 15000


def read_config(config_path=CONFIG_FILE):
    if not config_path.exists():
        logging.error(f'{config_path} not found. See {config_path}.example for an example.')
        sys.exit(1)
    with config_path.open('r') as fin:
        return yaml.safe_load(fin)


def start_monitoring(target: Target):
    logging.info('Target: %s', target)


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    config = read_config()
    targets = config.get('targets', [])
    for target_config in targets:
        start_monitoring(Target(**target_config))


if __name__ == '__main__':
    main()
