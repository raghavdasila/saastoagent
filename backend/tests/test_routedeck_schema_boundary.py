from __future__ import annotations

import importlib
from pathlib import Path

from routedeck_core import (
    RouteDeckContextLens,
    RouteDeckGraphNavigationLocation,
    RouteDeckGraphRequest,
    RouteDeckGraphResponse,
    RouteDeckGraphState,
)


def test_corpus_app_graph_schemas_extend_routedeck_foundation_models():
    schemas = importlib.import_module("backend.corpus.schemas")

    CorpusContextLens = schemas.CorpusContextLens
    CorpusGraphNavigationLocation = schemas.CorpusGraphNavigationLocation
    CorpusGraphRequest = schemas.CorpusGraphRequest
    CorpusGraphResponse = schemas.CorpusGraphResponse
    CorpusGraphState = schemas.CorpusGraphState

    assert issubclass(CorpusGraphNavigationLocation, RouteDeckGraphNavigationLocation)
    assert issubclass(CorpusGraphState, RouteDeckGraphState)
    assert issubclass(CorpusGraphRequest, RouteDeckGraphRequest)
    assert issubclass(CorpusContextLens, RouteDeckContextLens)
    assert issubclass(CorpusGraphResponse, RouteDeckGraphResponse)

    assert "saas_agents" not in RouteDeckGraphResponse.model_fields
    assert "saas_agents" in CorpusGraphResponse.model_fields
    assert "selected_saas_agent_id" not in RouteDeckContextLens.model_fields
    assert "selected_saas_agent_id" in CorpusContextLens.model_fields


def test_framework_context_lens_preserves_product_extension_values():
    lens = RouteDeckContextLens.model_validate(
        {
            "current_node": "catalog",
            "working_on": "Catalog",
            "selected_saas_agent_id": "agent-1",
            "ready_connection_count": 1,
        }
    )

    assert "selected_saas_agent_id" not in RouteDeckContextLens.model_fields
    assert lens.model_dump()["selected_saas_agent_id"] == "agent-1"
    assert lens.model_dump()["ready_connection_count"] == 1


def test_corpus_schemas_do_not_reintroduce_legacy_entry_contract_layer():
    schema_root = Path(__file__).parents[1] / "corpus" / "schemas"
    legacy_schema_root = Path(__file__).parents[1] / "core" / "schemas"
    corpus_source = (schema_root / "graph.py").read_text(encoding="utf-8")
    init_source = (schema_root / "__init__.py").read_text(encoding="utf-8")

    assert (schema_root / "graph.py").exists()
    assert not (schema_root / "entry.py").exists()
    assert not (legacy_schema_root / "corpus.py").exists()
    assert not (legacy_schema_root / "entry.py").exists()
    assert not (legacy_schema_root / "app_graph.py").exists()
    assert "class CorpusGraphState(" in corpus_source
    assert "class CorpusContextLens(" in corpus_source
    assert "class Entry" not in corpus_source
    assert "Entry" not in init_source
    assert "from .entry import" not in init_source


def test_legacy_entry_persistence_models_are_not_active_corpus_models():
    corpus_model_root = Path(__file__).parents[1] / "corpus" / "models"
    core_models_source = (
        Path(__file__).parents[1] / "core" / "models" / "__init__.py"
    ).read_text(encoding="utf-8")

    assert not (corpus_model_root / "entry.py").exists()
    assert "EntrySession" not in core_models_source
    assert "EntryRun" not in core_models_source


def test_corpus_uses_routedeck_contract_models_directly_without_entry_aliases():
    schemas = importlib.import_module("backend.corpus.schemas")

    for legacy_name in [
        "EntryActionCard",
        "EntryActionField",
        "EntryGraphManifest",
        "EntryGraphMessage",
        "EntryRouteDeckRuntimeSnapshot",
        "EntryUIArtifact",
    ]:
        assert not hasattr(schemas, legacy_name)
