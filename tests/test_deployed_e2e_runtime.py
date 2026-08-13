from __future__ import annotations

import pytest

from scripts.deployed_e2e_runtime import GcpJourneyRuntime
from scripts.run_api_connection_check_journey import _expected_final_sha256
from scripts.run_horizontal_product_journey import arguments


def test_gcp_runtime_requires_private_medusa_target() -> None:
    with pytest.raises(ValueError, match="private IPv4"):
        GcpJourneyRuntime(
            project="saastoagent",
            corpus_vm="corpus-vm-1",
            corpus_zone="asia-south1-a",
            medusa_vm="medusa-test-vm-1",
            medusa_zone="us-west1-a",
            medusa_base_url="http://127.0.0.1:9000",
        )


def test_gcp_runtime_rejects_target_paths_and_missing_vm_identity() -> None:
    with pytest.raises(ValueError, match="origin only"):
        GcpJourneyRuntime(
            project="saastoagent",
            corpus_vm="corpus-vm-1",
            corpus_zone="asia-south1-a",
            medusa_vm="medusa-test-vm-1",
            medusa_zone="us-west1-a",
            medusa_base_url="http://10.138.0.2:9100/store/products",
        )
    with pytest.raises(ValueError, match="required"):
        GcpJourneyRuntime(
            project="saastoagent",
            corpus_vm="",
            corpus_zone="asia-south1-a",
            medusa_vm="medusa-test-vm-1",
            medusa_zone="us-west1-a",
            medusa_base_url="http://10.138.0.2:9100",
        )


def test_production_review_keeps_the_exact_accepted_hash_chain() -> None:
    proposal = {
        "repaired_parent_sha256": "bc1b4b2456eefab4684a07ffa6e63f652118f5a705dd13eba5d77e74ab965c6e",
        "final_canonical_sha256": "c0b9c6bf1b149a0e458de9fbda4f7bad3cf6f9f7eb4ff383bded3b09d23e50ef",
        "patches": [{}] * 12,
    }

    assert _expected_final_sha256(proposal, runtime_mode="gcp-production") == proposal["final_canonical_sha256"]

    proposal["final_canonical_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="exact reviewed correction"):
        _expected_final_sha256(proposal, runtime_mode="gcp-production")


def test_horizontal_runner_exposes_explicit_production_target_arguments(monkeypatch) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_horizontal_product_journey.py",
            "--runtime-mode", "gcp-production",
            "--medusa-base-url", "http://10.138.0.2:9100",
            "--mode", "surface",
        ],
    )

    parsed = arguments()

    assert parsed.runtime_mode == "gcp-production"
    assert parsed.medusa_base_url == "http://10.138.0.2:9100"
