from __future__ import annotations

import subprocess
from unittest.mock import patch

from scripts.collect_gcp_vm_telemetry import _remote_snapshot, summarize


def test_remote_timeout_becomes_an_error_sample() -> None:
    with patch(
        "scripts.collect_gcp_vm_telemetry.subprocess.run",
        side_effect=subprocess.TimeoutExpired(["gcloud"], 90),
    ):
        result = _remote_snapshot("project", "vm", "zone")

    assert result["vm"] == "vm"
    assert result["zone"] == "zone"
    assert result["error"] == "telemetry SSH timed out after 90 seconds"


def test_summary_reports_capacity_peaks_and_ooms() -> None:
    samples = [
        {
            "vm": "medusa-test-vm-1",
            "memory": {"total_bytes": 1_000, "available_bytes": 400},
            "swap": {"total_bytes": 2_000, "free_bytes": 1_900},
            "load": {"one": 0.5, "five": 0.25, "fifteen": 0.1},
            "cpu": {"utilization_percent": 24.5},
            "disk": {"total_bytes": 10_000, "free_bytes": 7_000},
            "containers": [{"Name": "medusa", "CPUPerc": "11.25%"}],
            "oom_kills": 0,
        },
        {
            "vm": "medusa-test-vm-1",
            "memory": {"total_bytes": 1_000, "available_bytes": 100},
            "swap": {"total_bytes": 2_000, "free_bytes": 1_200},
            "load": {"one": 1.75, "five": 1.0, "fifteen": 0.5},
            "cpu": {"utilization_percent": 87.5},
            "disk": {"total_bytes": 10_000, "free_bytes": 6_000},
            "containers": [{"Name": "medusa", "CPUPerc": "73.50%"}],
            "oom_kills": 1,
        },
    ]

    result = summarize(samples)

    assert result["medusa-test-vm-1"]["peak_memory_used_bytes"] == 900
    assert result["medusa-test-vm-1"]["peak_swap_used_bytes"] == 800
    assert result["medusa-test-vm-1"]["peak_load_one"] == 1.75
    assert result["medusa-test-vm-1"]["peak_host_cpu_percent"] == 87.5
    assert result["medusa-test-vm-1"]["average_host_cpu_percent"] == 56.0
    assert result["medusa-test-vm-1"]["peak_container_cpu_percent"]["medusa"] == 73.5
    assert result["medusa-test-vm-1"]["minimum_disk_free_bytes"] == 6_000
    assert result["medusa-test-vm-1"]["max_oom_kills"] == 1


def test_summary_keeps_vms_independent() -> None:
    samples = [
        {
            "vm": name,
            "memory": {"total_bytes": total, "available_bytes": total // 2},
            "swap": {"total_bytes": 0, "free_bytes": 0},
            "load": {"one": 0.1, "five": 0.1, "fifteen": 0.1},
            "cpu": {"utilization_percent": 2.0},
            "disk": {"total_bytes": 20_000, "free_bytes": 10_000},
            "containers": [],
            "oom_kills": 0,
        }
        for name, total in (("corpus-vm-1", 16_000), ("medusa-test-vm-1", 1_000))
    ]

    result = summarize(samples)

    assert set(result) == {"corpus-vm-1", "medusa-test-vm-1"}
    assert result["corpus-vm-1"]["peak_memory_used_bytes"] == 8_000
    assert result["medusa-test-vm-1"]["peak_memory_used_bytes"] == 500
