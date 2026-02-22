import sys
import pathlib
import logging
import dataclasses
import asyncio


import yaml


CONFIG_PATH = pathlib.Path('config.yaml')


@dataclasses.dataclass
class Target:
    type: str
    target: str
    timeout_millis: int = 5000
    interval_millis: int = 15000


def read_config(config_path=CONFIG_PATH):
    if not config_path.exists():
        logging.error(f'{config_path} not found. See {config_path}.example for an example.')
        sys.exit(1)
    with config_path.open('r') as fin:
        return yaml.safe_load(fin)


async def monitor_target(target: Target):
    logging.info('Target: %s', target)
    try:
        while True:
            logging.debug('Monitoring %s', target.target)  # TODO
            await asyncio.sleep(target.interval_millis / 1000.)
    except asyncio.CancelledError:
        logging.info('Stopped monitoring %s', target.target)


async def monitor(targets):
    tasks = map(lambda t: asyncio.create_task(monitor_target(t)), targets)
    await asyncio.gather(*tasks)


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s')

    config = read_config()
    targets = config.get('targets', [])
    if not targets:
        logging.error('No targets found in config. Exiting.')
        return

    try:
        asyncio.run(monitor([Target(**target) for target in targets]))
    except KeyboardInterrupt:
        logging.info('Keyboard interrupt received, exiting...')


if __name__ == '__main__':
    main()
