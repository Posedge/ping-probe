import sys
import pathlib

import yaml


CONFIG_FILE = pathlib.Path('config.yaml')


def read_config(config_path=CONFIG_FILE):
    if not config_path.exists():
        print(f'{config_path} not found. See {config_path}.example for an example.')
        sys.exit(1)
    with config_path.open('r') as fin:
        return yaml.safe_load(fin)


def main():
    config = read_config()
    print(config)


if __name__ == '__main__':
    main()