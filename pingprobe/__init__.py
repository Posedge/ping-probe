import sys
import pathlib
import logging
import dataclasses
import asyncio
import time
from typing import List, Dict, Set


import yaml
import icmplib
import prometheus_client as prometheus


CONFIG_PATH = pathlib.Path('config.yaml')


@dataclasses.dataclass
class Target:
    type: str
    address: str
    timeout_millis: int = 5000
    interval_millis: int = 15000
    labels: Dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class PingResult:
    target: Target
    success: bool
    status: str
    rtt_ms: float = None


class Exporter:
    probe_counter: prometheus.Counter
    latency_histogram: prometheus.Histogram
    extra_labels: Set[str]

    def __init__(self, extra_labels: Set[str]):
        self.extra_labels = extra_labels
        self.probe_counter = prometheus.Counter(
            'probes', 'Total number of probe attempts by status', self.extra_labels | {'address', 'status'})
        self.latency_histogram = prometheus.Histogram(
            'probe_latency_millis', 'Latency of successful probes in milliseconds', self.extra_labels | {'address'})

    def observe(self, result: PingResult):
        logging.debug(f'Ping {result.target.address}: {result}')
        labels = {l: "" for l in self.extra_labels} | result.target.labels
        self.probe_counter.labels(
            address=result.target.address,
            status=result.status,
            **labels
        ).inc()
        if result.success and result.rtt_ms is not None:
            self.latency_histogram.labels(
                address=result.target.address,
                **labels
            ).observe(result.rtt_ms)


async def ping(target: Target) -> PingResult:
    try:
        response = await icmplib.async_ping(
            target.address, count=1, timeout=target.timeout_millis/1000., privileged=False)
    except icmplib.NameLookupError:
        return PingResult(target=target, success=False, status='name_lookup_error')
    except icmplib.TimeoutExceeded:
        return PingResult(target=target, success=False, status='timeout')
    except icmplib.DestinationUnreachable:
        return PingResult(target=target, success=False, status='destination_unreachable')
    except Exception as e:
        logging.error(f'Unknown error pinging {target.address}', exc_info=e)
        return PingResult(target=target, success=False, status='unknown_error')

    if response.packets_received == 1:
        return PingResult(target=target, success=True, status='success', rtt_ms=response.min_rtt )
    else:
        return PingResult(target=target, success=False, status='no_response_error')


async def sleep_until(target_time):
    now = time.time()
    if target_time > now:
        await asyncio.sleep(target_time - now)


async def monitor_target(exporter, target: Target):
    logging.info('Target: %s', target)
    try:
        while True:
            interval_start = time.time()
            result = await ping(target)
            exporter.observe(result)
            await sleep_until(interval_start + target.interval_millis/1000.)
    except asyncio.CancelledError:
        logging.debug('Stopped monitoring %s', target.address)


async def monitor(exporter, *targets: List[Target]):
    tasks = [asyncio.create_task(monitor_target(exporter, t)) for t in targets]
    await asyncio.gather(*tasks)


def read_config(config_path=CONFIG_PATH) -> dict:
    if not config_path.exists():
        logging.error(f'{config_path} not found. See {config_path}.example for an example.')
        sys.exit(1)
    with config_path.open('r') as fin:
        return yaml.safe_load(fin)


def parse_target(target_conf: dict) -> Target:
    target_conf['labels'] = {
        l['name']: l['value']
        for l in target_conf.get('labels', [])
    }
    return Target(**target_conf)


def main():
    config = read_config()
    log_level = config.get('logging', {}).get('level', 'DEBUG')
    logging.basicConfig(level=log_level, format='%(asctime)s [%(levelname)s] %(message)s')

    targets = [parse_target(t) for t in config.get('targets', [])]
    if not targets:
        logging.error('No targets found in config. Exiting.')
        return

    all_labels = {
        k
        for t in targets
        for k in t.labels.keys()
    }
    exporter = Exporter(all_labels)

    prom_port = config.get('monitoring', {}).get('prometheus', {}).get('port', 8000)
    logging.info(f'Starting Prometheus server on port {prom_port}')
    server, server_thread = prometheus.start_http_server(prom_port)
    try:
        asyncio.run(monitor(exporter, *targets))
    except KeyboardInterrupt:
        logging.info('Keyboard interrupt received, exiting...')
    server.shutdown()
    server.server_close()
    server_thread.join()


if __name__ == '__main__':
    main()
