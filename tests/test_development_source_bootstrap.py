from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT
    / "contracts"
    / "dependency-provenance"
    / "development-source-checkouts.json"
)
SCRIPT = ROOT / "scripts" / "clone-development-dependencies.ps1"


def test_development_source_manifest_pins_exact_canonical_repositories() -> None:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    dependencies = {item["directory"]: item for item in payload["dependencies"]}

    assert payload["schema_version"] == 1
    assert set(dependencies) == {
        "routedeck",
        "agent-execution-runtime",
        "agent-delivery-runtime",
    }
    for directory, dependency in dependencies.items():
        assert dependency["repository"] == (
            f"https://github.com/saastoagent/{directory}.git"
        )
        assert re.fullmatch(r"[0-9a-f]{40}", dependency["commit"])

    assert dependencies["routedeck"]["visibility"] == "public"
    assert dependencies["agent-execution-runtime"]["package_version"] == "0.1.0"
    assert dependencies["agent-delivery-runtime"]["package_version"] == "0.1.0"
    assert dependencies["agent-execution-runtime"]["visibility"] == "private"
    assert dependencies["agent-delivery-runtime"]["visibility"] == "private"


def test_bootstrap_is_pinned_and_refuses_existing_dependency_directories() -> None:
    script = SCRIPT.read_text(encoding="utf-8")

    assert "git clone --no-checkout" in script
    assert "checkout --detach $Commit" in script
    assert "Dependency target already exists; refusing to modify it" in script
    assert "rev-parse HEAD" in script
    assert "Remove-Item" not in script
