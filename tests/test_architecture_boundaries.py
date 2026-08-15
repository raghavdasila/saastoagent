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


def test_backend_discovers_every_feature_directory(tmp_path: Path) -> None:
    feature = tmp_path / "backend/src/corpus/features/new_feature"
    feature.mkdir(parents=True)
    (feature / "service.py").write_text(
        "from corpus.features.workspace.service import WorkspaceService\n",
        encoding="utf-8",
    )

    violations = find_architecture_violations(tmp_path)

    assert len(violations) == 1
    assert "feature 'new_feature'" in violations[0].message


def test_backend_context_providers_use_persisted_string_entity_identity(
    tmp_path: Path,
) -> None:
    feature = tmp_path / "backend/src/corpus/features/consumer"
    feature.mkdir(parents=True)
    (feature / "providers.py").write_text(
        "value = binding.private_id.get_secret_value()\n",
        encoding="utf-8",
    )

    violations = find_architecture_violations(tmp_path)

    assert len(violations) == 1
    assert "persisted private_id is already a string" in violations[0].message


def test_backend_allows_only_declared_public_dependencies(tmp_path: Path) -> None:
    feature = tmp_path / "backend/src/corpus/features/consumer"
    feature.mkdir(parents=True)
    (feature / "service.py").write_text(
        "\n".join(
            (
                "from corpus.features.consumer.domain import Record",
                "from corpus.shared.identifiers import StableId",
                "from corpus.persistence import CorpusDatabase",
                "from corpus.jobs import DurableJobPort",
                "from corpus.credentials import CredentialVaultPort",
                "from corpus.auth.contracts import OWNER_CONTEXT_PROVIDER",
                "from corpus.features.provider.contracts import PROVIDER_HOME_REF",
            )
        ),
        encoding="utf-8",
    )

    assert find_architecture_violations(tmp_path) == []


def test_backend_rejects_concrete_and_composition_dependencies(tmp_path: Path) -> None:
    feature = tmp_path / "backend/src/corpus/features/consumer"
    feature.mkdir(parents=True)
    forbidden = (
        "corpus.features.provider.service",
        "corpus.features.provider.repository",
        "corpus.features.provider.models",
        "corpus.features.provider.schemas",
        "corpus.features.provider.http",
        "corpus.features.provider.ports",
        "corpus.app.composition",
        "corpus.runtime.config",
        "corpus.integrations.provider",
        "corpus.jobs.repository",
    )
    (feature / "service.py").write_text(
        "\n".join(f"import {module}" for module in forbidden),
        encoding="utf-8",
    )

    violations = find_architecture_violations(tmp_path)

    assert len(violations) == len(forbidden)
    assert {value.message.rsplit("'", 2)[1] for value in violations} == set(forbidden)


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


def test_frontend_discovers_every_feature_directory(tmp_path: Path) -> None:
    feature = tmp_path / "frontend/src/features/new-feature"
    feature.mkdir(parents=True)
    (feature / "Surface.tsx").write_text(
        'import { workspaceStore } from "../workspace/store";\n',
        encoding="utf-8",
    )

    violations = find_architecture_violations(tmp_path)

    assert len(violations) == 1
    assert "frontend feature 'new-feature'" in violations[0].message


def test_frontend_allows_self_shared_components_routedeck_and_contracts(
    tmp_path: Path,
) -> None:
    feature = tmp_path / "frontend/src/features/consumer"
    feature.mkdir(parents=True)
    (feature / "Surface.tsx").write_text(
        "\n".join(
            (
                'import { local } from "./local";',
                'import { shared } from "@/shared/value";',
                'import { Button } from "@/components/ui/button";',
                'import type { Props } from "@routedeck/react";',
                'import type { ProviderView } from "../provider/contracts";',
            )
        ),
        encoding="utf-8",
    )

    assert find_architecture_violations(tmp_path) == []


def test_frontend_rejects_cross_feature_internal_and_app_imports(
    tmp_path: Path,
) -> None:
    feature = tmp_path / "frontend/src/features/consumer"
    feature.mkdir(parents=True)
    (feature / "Surface.tsx").write_text(
        "\n".join(
            (
                'import { store } from "../provider/store";',
                'import { transport } from "@/app/transports";',
            )
        ),
        encoding="utf-8",
    )

    violations = find_architecture_violations(tmp_path)

    assert len(violations) == 2
    assert any("only through contracts" in value.message for value in violations)
    assert any("cannot import app composition" in value.message for value in violations)
