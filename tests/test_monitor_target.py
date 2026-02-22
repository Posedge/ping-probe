import asyncio

import pytest
import unittest.mock

import pingprobe


@pytest.mark.asyncio
async def test_monitor_target_with_mocked_ping():
    target = pingprobe.Target('ping', 'custom.example.com', timeout_millis=1000, interval_millis=5000)
    mock_ping_result = pingprobe.PingResult('custom.example.com', success=True, rtt_ms=12.3, status='success')
    with unittest.mock.patch('pingprobe.ping', return_value=mock_ping_result), \
         unittest.mock.patch('pingprobe.export') as mock_export:
        task = asyncio.create_task(pingprobe.monitor_target(target))
        await asyncio.wait_for(task, timeout=0.1)
        task.cancel()
        mock_export.assert_called_with(mock_ping_result)
        
