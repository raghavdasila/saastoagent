from __future__ import annotations

from backend.core.schemas import (
    AppGraphContextLens,
    AppGraphNavigationLocation,
    AppGraphRequest,
    AppGraphResponse,
    AppGraphState,
    EntryActionCard,
    EntryActionField,
    EntryGraphManifest,
    EntryGraphMessage,
    EntryRouteDeckRuntimeSnapshot,
    EntryUIArtifact,
)
from backend.core.schemas.entry import EntryGraphManifestAction, EntryGraphManifestEdge, EntryGraphManifestNode
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
    assert issubclass(AppGraphNavigationLocation, RouteDeckGraphNavigationLocation)
    assert issubclass(AppGraphState, RouteDeckGraphState)
    assert issubclass(AppGraphRequest, RouteDeckGraphRequest)
    assert issubclass(AppGraphContextLens, RouteDeckContextLens)
    assert issubclass(AppGraphResponse, RouteDeckGraphResponse)

    assert "saas_agents" not in RouteDeckGraphResponse.model_fields
    assert "saas_agents" in AppGraphResponse.model_fields
    assert "selected_saas_agent_id" not in RouteDeckContextLens.model_fields
    assert "selected_saas_agent_id" in AppGraphContextLens.model_fields


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
