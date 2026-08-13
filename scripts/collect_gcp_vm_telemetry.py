from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Mapping


GCLOUD = "gcloud.cmd" if os.name == "nt" else "gcloud"


REMOTE_SNAPSHOT = r'''import json, os, shutil, subprocess, time
def cpu_counters():
    with open('/proc/stat', encoding='utf-8') as handle:
        fields = [int(value) for value in handle.readline().split()[1:]]
    idle = fields[3] + (fields[4] if len(fields) > 4 else 0)
    return sum(fields), idle
def meminfo():
    values = {}
    with open('/proc/meminfo', encoding='utf-8') as handle:
        for line in handle:
            key, raw = line.split(':', 1)
            values[key] = int(raw.strip().split()[0]) * 1024
    return values
memory = meminfo()
cpu_total_before, cpu_idle_before = cpu_counters()
time.sleep(0.25)
cpu_total_after, cpu_idle_after = cpu_counters()
cpu_total_delta = cpu_total_after - cpu_total_before
cpu_idle_delta = cpu_idle_after - cpu_idle_before
cpu_utilization = 0.0 if cpu_total_delta <= 0 else 100.0 * (1.0 - cpu_idle_delta / cpu_total_delta)
state_path = '/var/lib/medusa-acceptance' if os.path.exists('/var/lib/medusa-acceptance') else '/srv/corpus'
disk = shutil.disk_usage(state_path if os.path.exists(state_path) else '/')
try:
    containers = subprocess.run(
        ['docker', 'stats', '--no-stream', '--format', '{{json .}}'],
        text=True, capture_output=True, timeout=20, check=False,
    ).stdout.splitlines()
    containers = [json.loads(line) for line in containers if line.strip()]
except Exception:
    containers = []
try:
    kernel = subprocess.run(
        ['dmesg', '--color=never'], text=True, capture_output=True,
        timeout=20, check=False,
    ).stdout.casefold()
except Exception:
    kernel = ''
loads = os.getloadavg()
print(json.dumps({
    'captured_at': time.time(),
    'memory': {'total_bytes': memory['MemTotal'], 'available_bytes': memory['MemAvailable']},
    'swap': {'total_bytes': memory['SwapTotal'], 'free_bytes': memory['SwapFree']},
    'cpu': {'utilization_percent': round(cpu_utilization, 3)},
    'load': {'one': loads[0], 'five': loads[1], 'fifteen': loads[2]},
    'disk': {'path': state_path, 'total_bytes': disk.total, 'free_bytes': disk.free},
    'containers': containers,
    'oom_kills': kernel.count('out of memory: killed process') + kernel.count('oom-kill:'),
}))
'''


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect secret-free VM capacity telemetry through IAP.")
    parser.add_argument("--project", default="saastoagent")
    parser.add_argument("--vm", action="append", required=True, metavar="NAME:ZONE")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--interval-seconds", type=float, default=15.0)
    parser.add_argument("--duration-seconds", type=float, default=7200.0)
    parser.add_argument("--stop-file", type=Path)
    return parser.parse_args()


def _remote_snapshot(project: str, vm: str, zone: str) -> dict[str, object]:
    encoded = base64.b64encode(REMOTE_SNAPSHOT.encode("utf-8")).decode("ascii")
    command = f"echo {encoded} | base64 -d | sudo python3 -"
    try:
        completed = subprocess.run(
            [
                GCLOUD, "compute", "ssh", vm,
                f"--zone={zone}", f"--project={project}",
                "--tunnel-through-iap", "--quiet", "--command", command,
            ],
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "captured_at": datetime.now(UTC).isoformat(),
            "vm": vm,
            "zone": zone,
            "error": "telemetry SSH timed out after 90 seconds",
        }
    if completed.returncode != 0:
        return {
            "captured_at": datetime.now(UTC).isoformat(),
            "vm": vm,
            "zone": zone,
            "error": (completed.stderr.strip() or completed.stdout.strip())[-1000:],
        }
    try:
        value = json.loads(completed.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as error:
        return {
            "captured_at": datetime.now(UTC).isoformat(),
            "vm": vm,
            "zone": zone,
            "error": f"telemetry JSON unavailable: {error}",
        }
    value.update(vm=vm, zone=zone)
    return value


def summarize(samples: Iterable[Mapping[str, object]]) -> dict[str, dict[str, object]]:
    grouped: dict[str, list[Mapping[str, object]]] = defaultdict(list)
    for sample in samples:
        if isinstance(sample.get("vm"), str) and "error" not in sample:
            grouped[str(sample["vm"])].append(sample)
    result: dict[str, dict[str, object]] = {}
    for vm, values in grouped.items():
        memory_used = [
            int(item["memory"]["total_bytes"]) - int(item["memory"]["available_bytes"])
            for item in values
        ]
        swap_used = [
            int(item["swap"]["total_bytes"]) - int(item["swap"]["free_bytes"])
            for item in values
        ]
        host_cpu = [float(item["cpu"]["utilization_percent"]) for item in values]
        container_cpu: dict[str, float] = {}
        for item in values:
            for container in item.get("containers", []):
                if not isinstance(container, Mapping):
                    continue
                name = str(container.get("Name") or container.get("Container") or "unknown")
                raw_percent = str(container.get("CPUPerc", "0")).strip().removesuffix("%")
                try:
                    percent = float(raw_percent)
                except ValueError:
                    continue
                container_cpu[name] = max(container_cpu.get(name, 0.0), percent)
        result[vm] = {
            "samples": len(values),
            "peak_memory_used_bytes": max(memory_used),
            "peak_swap_used_bytes": max(swap_used),
            "peak_load_one": max(float(item["load"]["one"]) for item in values),
            "peak_load_five": max(float(item["load"]["five"]) for item in values),
            "peak_host_cpu_percent": max(host_cpu),
            "average_host_cpu_percent": sum(host_cpu) / len(host_cpu),
            "peak_container_cpu_percent": dict(sorted(container_cpu.items())),
            "minimum_disk_free_bytes": min(int(item["disk"]["free_bytes"]) for item in values),
            "max_oom_kills": max(int(item.get("oom_kills", 0)) for item in values),
        }
    return result


def main() -> None:
    args = arguments()
    identities: list[tuple[str, str]] = []
    for raw in args.vm:
        if raw.count(":") != 1 or not all(part.strip() for part in raw.split(":", 1)):
            raise SystemExit(f"Invalid --vm identity: {raw}")
        identities.append(tuple(raw.split(":", 1)))  # type: ignore[arg-type]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    samples: list[dict[str, object]] = []
    deadline = time.monotonic() + args.duration_seconds
    with args.output.open("a", encoding="utf-8") as handle:
        while time.monotonic() < deadline:
            if args.stop_file is not None and args.stop_file.exists():
                break
            started = time.monotonic()
            for vm, zone in identities:
                sample = _remote_snapshot(args.project, vm, zone)
                samples.append(sample)
                handle.write(json.dumps(sample, sort_keys=True) + "\n")
                handle.flush()
            remaining = args.interval_seconds - (time.monotonic() - started)
            if remaining > 0:
                time.sleep(remaining)
    args.summary.write_text(json.dumps(summarize(samples), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
