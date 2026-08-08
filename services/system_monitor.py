from __future__ import annotations

import shutil
import subprocess
import time
from dataclasses import dataclass

import psutil


@dataclass
class SystemSnapshot:
    cpu: float
    memory: float
    disk: float
    net_up_mbs: float
    net_down_mbs: float
    gpu: float | None


class SystemMonitor:
    def __init__(self) -> None:
        self._prev_net = psutil.net_io_counters()
        self._prev_ts = time.time()
        psutil.cpu_percent(interval=None)

    def snapshot(self) -> SystemSnapshot:
        now = time.time()
        elapsed = max(now - self._prev_ts, 0.001)
        net = psutil.net_io_counters()
        up = (net.bytes_sent - self._prev_net.bytes_sent) / elapsed / (1024 * 1024)
        down = (net.bytes_recv - self._prev_net.bytes_recv) / elapsed / (1024 * 1024)
        self._prev_net = net
        self._prev_ts = now

        usage = shutil.disk_usage("C:\\")
        disk_pct = (usage.used / usage.total) * 100 if usage.total else 0.0

        return SystemSnapshot(
            cpu=float(psutil.cpu_percent(interval=None)),
            memory=float(psutil.virtual_memory().percent),
            disk=float(disk_pct),
            net_up_mbs=max(up, 0.0),
            net_down_mbs=max(down, 0.0),
            gpu=self._gpu_percent(),
        )

    def _gpu_percent(self) -> float | None:
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=1.5,
                check=False,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return None
            return float(result.stdout.strip().splitlines()[0])
        except Exception:
            return None
