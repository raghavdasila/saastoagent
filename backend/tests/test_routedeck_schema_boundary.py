from __future__ import annotations

from pathlib import Path

from backend.core.schemas import (
    CorpusContextLens,
    CorpusGraphNavigationLocation,
    CorpusGraphRequest,
    CorpusGraphResponse,
    CorpusGraphState,
    EntryActionCard,
    EntryActionField,
    EntryGraphManifest,
    EntryGraphMessage,
    EntryRouteDeckRuntimeSnapshot,
    EntryUIArtifact,
)
from backend.core.schemas.corpus import EntryGraphManifestAction, EntryGraphManifestEdge, EntryGraphManifestNode
from routedeck_core import (
    RouteDeckActionCard,
    RouteDeckActionField,
    RouteDeckContextLens,
    RouteDeckGraphManifest,
    RouteDeckGraphManifestAction,
    RouteDeckGraphManifestEdge,
    RouteDeckGraphManifestNode,
    RouteDeckGraphMessage,
    RouteDeckGraphNavigationLocation,
    RouteDeckGraphRequest,
    RouteDeckGraphResponse,
    RouteDeckGraphState,
    RouteDeckRuntimeSnapshot,
    RouteDeckUIArtifact,
)


def test_corpus_app_graph_schemas_extend_routedeck_foundation_models():
    assert issubclass(CorpusGraphNavigationLocation, RouteDeckGraphNavigationLocation)
    assert issubclass(CorpusGraphState, RouteDeckGraphState)
    assert issubclass(CorpusGraphRequest, RouteDeckGraphRequest)
    assert issubclass(CorpusContextLens, RouteDeckContextLens)
    assert issubclass(CorpusGraphResponse, RouteDeckGraphResponse)

    assert "saas_agents" not in RouteDeckGraphResponse.model_fields
    assert "saas_agents" in CorpusGraphResponse.model_fields
    assert "selected_saas_agent_id" not in RouteDeckContextLens.model_fields
    assert "selected_saas_agent_id" in CorpusContextLens.model_fields


def test_corpus_schema_module_owns_product_graph_contracts():
    schema_root = Path(__file__).parents[1] / "core" / "schemas"

    assert (schema_root / "corpus.py").exists()
    assert not (schema_root / "app_graph.py").exists()
    assert not (schema_root / "entry.py").exists()


def test_entry_contract_schemas_are_routedeck_foundation_models_with_legacy_names():
    assert issubclass(EntryActionField, RouteDeckActionField)
    assert issubclass(EntryActionCard, RouteDeckActionCard)
    assert issubclass(EntryUIArtifact, RouteDeckUIArtifact)
    assert issubclass(EntryGraphMessage, RouteDeckGraphMessage)
    assert issubclass(EntryGraphManifestNode, RouteDeckGraphManifestNode)
    assert issubclass(EntryGraphManifestEdge, RouteDeckGraphManifestEdge)
    assert issubclass(EntryGraphManifestAction, RouteDeckGraphManifestAction)
    assert issubclass(EntryGraphManifest, RouteDeckGraphManifest)
    assert issubclass(EntryRouteDeckRuntimeSnapshot, RouteDeckRuntimeSnapshot)
