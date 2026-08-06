from __future__ import annotations

from pathlib import Path

from scripts.check_architecture_boundaries import find_architecture_violations


REPOSITORY = Path(__file__).resolve().parents[1]


def test_current_corpus_architecture_boundaries() -> None:
    assert find_architecture_violations(REPOSITORY) == []


def test_backend_cross_feature_imports_require_contracts(tmp_path: Path) -> None:
    feature = tmp_path / "backend/src/corpus/features/agents"
    feature.mkdir(parents=True)
    (feature / "service.py").write_text(
        "from corpus.features.workspace.feature import WORKSPACE_FEATURE\n",
        encoding="utf-8",
    )

    violations = find_architecture_violations(tmp_path)

    assert len(violations) == 1
    assert "only through contracts" not in violations[0].message
    assert "cannot import" in violations[0].message


def test_frontend_feature_cannot_import_another_feature_store(
    tmp_path: Path,
) -> None:
    feature = tmp_path / "frontend/src/features/agents"
    feature.mkdir(parents=True)
    (feature / "AgentList.tsx").write_text(
        'import { workspaceStore } from "../workspace/store";\n',
        encoding="utf-8",
    )

    violations = find_architecture_violations(tmp_path)

    assert len(violations) == 1
    assert "only through contracts" in violations[0].message
