from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[3]
INTEGRATION_ROOT = (
    BACKEND_ROOT / "src" / "corpus" / "integrations" / "toolrouter"
)
MANIFEST_PATH = INTEGRATION_ROOT / "source_manifest.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_vendored_engine_matches_its_recorded_source_snapshot() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == 1
    assert manifest["source_repository"] == (
        r"D:\Dev\AI Projects\openapi-toolrouter-benchmark"
    )
    assert manifest["source_commit"] == "2611801e"
    assert manifest["source_worktree"] == "dirty_snapshot"
    assert manifest["files"]

    for row in manifest["files"]:
        copied = INTEGRATION_ROOT / row["vendored_path"]
        assert copied.is_file(), row
        assert _sha256(copied) == row["vendored_sha256"], row
        text = copied.read_text(encoding="utf-8")
        assert "from toolrouter" not in text
        assert "import toolrouter" not in text


def test_vendored_engine_core_modules_import_from_the_corpus_namespace() -> None:
    for module in (
        "openapi_loader",
        "semantic_graph",
        "semantic_graph_retrieval",
        "semantic_grag_router",
        "evalset_factory_experiment",
        "evalset_factory_export",
    ):
        imported = importlib.import_module(
            f"corpus.integrations.toolrouter.engine.{module}"
        )
        assert imported.__name__.startswith(
            "corpus.integrations.toolrouter.engine."
        )

