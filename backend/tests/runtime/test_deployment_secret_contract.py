from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SECRET_NAMES = {
    "corpus-openai-api-key",
    "corpus-smtp-app-password",
    "corpus-routedeck-state-encryption-key",
    "corpus-credential-vault-key",
    "corpus-reset-secret",
    "corpus-verification-secret",
}


def test_operator_secret_ingestion_declares_the_complete_inventory() -> None:
    script = (ROOT / "deploy" / "fetch-secrets.ps1").read_text(encoding="utf-8")

    for name in SECRET_NAMES:
        assert name in script
    assert "saastoagent" in script
    assert "Write-Output $value" not in script
    assert "echo $value" not in script
    assert ".runtime/deployment" in script.replace("\\", "/")
    assert "Remove-Item" in script


def test_vm_secret_fetch_is_atomic_root_only_and_value_silent() -> None:
    script = (ROOT / "deploy" / "fetch-runtime-secrets.sh").read_text(
        encoding="utf-8"
    )

    for name in SECRET_NAMES:
        assert name in script
    assert "umask 077" in script
    assert "chmod 600" in script
    assert "runtime.env.tmp" in script
    assert "mv " in script
    assert "echo \"$value\"" not in script
    assert "printf '%s=%s\\n'" in script
