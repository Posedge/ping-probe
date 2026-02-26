import asyncio

import pytest
import unittest.mock

import pingprobe


@pytest.mark.asyncio
async def test_monitor_target_with_mocked_ping():
    target = pingprobe.Target('ping', 'custom.example.com', timeout_millis=1000, interval_millis=5000)
    mock_result = pingprobe.PingResult(target=target, success=True, rtt_ms=12.3, status='success')
    exporter = pingprobe.Exporter(set())
    with unittest.mock.patch('pingprobe.ping', return_value=mock_result), \
         unittest.mock.patch.object(exporter.probe_counter, 'labels') as mock_probe_labels, \
         unittest.mock.patch.object(exporter.latency_histogram, 'labels') as mock_latency_labels:
        task = asyncio.create_task(pingprobe.monitor_target(exporter, target))
        await asyncio.wait_for(task, timeout=0.1)
        task.cancel()
        mock_probe_labels.assert_called_with(address='custom.example.com', status='success')
        mock_latency_labels.assert_called_with(address='custom.example.com')
        
