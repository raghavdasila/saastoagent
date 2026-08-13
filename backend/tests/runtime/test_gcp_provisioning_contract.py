from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def test_gcp_provisioning_is_single_vm_and_project_scoped() -> None:
    script = (ROOT / "deploy" / "provision-gcp.ps1").read_text(encoding="utf-8")

    assert '"saastoagent"' in script
    assert "n2-standard-2" in script
    assert "160GB" in script
    assert "pd-balanced" in script
    assert "corpus-vm@saastoagent.iam.gserviceaccount.com" in script
    assert "--service-account" in script
    assert "--no-service-account" not in script
    assert "keys create" not in script
    assert "--shielded-secure-boot" in script
    assert "--shielded-vtpm" in script
    assert "--shielded-integrity-monitoring" in script
    assert "--deletion-protection" in script
    assert "enable-oslogin=TRUE" in script
    assert "block-project-ssh-keys=TRUE" in script


def test_firewall_contract_exposes_only_web_and_iap_ssh() -> None:
    script = (ROOT / "deploy" / "provision-gcp.ps1").read_text(encoding="utf-8")

    assert "tcp:80,tcp:443" in script
    assert "35.235.240.0/20" in script
    assert "tcp:22" in script
    assert "corpus-deny-public-admin" in script
    assert "--action=DENY" in script
    assert "tcp:22,tcp:3389" in script
    for forbidden in ("8099", "5199", "8771", "8782", "11434", "2375", "2376"):
        assert forbidden not in script


def test_vm_bootstrap_creates_owned_runtime_paths_without_git() -> None:
    script = (ROOT / "deploy" / "install-vm.sh").read_text(encoding="utf-8")

    assert "/srv/corpus/state" in script
    assert "/srv/corpus/data" in script
    assert "/srv/corpus/deploy" in script
    assert "/run/corpus" in script
    assert "docker-ce" in script
    assert "docker-compose-plugin" in script
    assert "git clone" not in script
    assert "git pull" not in script
