import sys
import pathlib
import logging
import dataclasses
import asyncio
import time
from typing import List


import yaml
import icmplib


CONFIG_PATH = pathlib.Path('config.yaml')


@dataclasses.dataclass
class Target:
    type: str
    address: str
    timeout_millis: int = 5000
    interval_millis: int = 15000


async def ping(target: Target):
    try:
        result = await icmplib.async_ping(
            target.address, count=1, timeout=target.timeout_millis/1000., privileged=False)
    except icmplib.ICMPError:
        logging.warning('Failed to ping %s', target.address)
    else:
        logging.debug(f'Ping {target.address}: rtt ms={result.min_rtt}, '
                      f'response received={'yes' if result.packets_received == 1 else 'no'}')


async def sleep_until(target_time):
    now = time.time()
    if target_time > now:
        await asyncio.sleep(target_time - now)


async def monitor_target(target: Target):
    logging.info('Target: %s', target)
    try:
        while True:
            interval_start = time.time()
            await ping(target)
            await sleep_until(interval_start + target.interval_millis/1000.)
    except asyncio.CancelledError:
        logging.info('Stopped monitoring %s', target.address)


async def monitor(targets: List[Target]):
    tasks = [asyncio.create_task(monitor_target(t)) for t in targets]
    await asyncio.gather(*tasks)


def read_config(config_path=CONFIG_PATH):
    if not config_path.exists():
        logging.error(f'{config_path} not found. See {config_path}.example for an example.')
        sys.exit(1)
    with config_path.open('r') as fin:
        return yaml.safe_load(fin)


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
