from pathlib import Path

from backend.services.saas_agent_route_deck import (
    ROUTE_DECK_VERSION,
    SaaSAgentRouteDeckFacts,
    SaaSAgentRouteNodeIds,
    build_saas_agent_route_deck_manifest,
    infer_current_node,
    validate_saas_agent_route_deck_manifest,
)


def test_saas_agent_route_deck_imports_routedeck_core_directly():
    source = Path("backend/services/saas_agent_route_deck.py").read_text(encoding="utf-8")

    assert "from .route_deck.models import" not in source
    assert "from routedeck_core import" in source


def test_saas_agent_route_deck_manifest_is_valid():
    assert validate_saas_agent_route_deck_manifest() == []
    manifest = build_saas_agent_route_deck_manifest()

    assert manifest.version == ROUTE_DECK_VERSION
    assert {node.id for node in manifest.nodes} >= {
        SaaSAgentRouteNodeIds.NEEDS_CONNECTION,
        SaaSAgentRouteNodeIds.SCHEMA_PREVIEW,
        SaaSAgentRouteNodeIds.CATALOG_READY,
        SaaSAgentRouteNodeIds.EXECUTION_PLANNING,
        SaaSAgentRouteNodeIds.LEARNING_REVIEW,
    }
    assert all("workspace" not in node.id.lower() for node in manifest.nodes)


def test_saas_agent_route_deck_infers_setup_state_from_catalog_facts():
    assert (
        infer_current_node(
            SaaSAgentRouteDeckFacts(
                connection_count=1,
                ready_connection_count=1,
                action_count=8,
                tool_count=8,
                latest_execution_status="approval_required",
                latest_execution_approval_state="pending",
            )
        )
        == SaaSAgentRouteNodeIds.APPROVAL_REQUIRED
    )
    assert (
        infer_current_node(
            SaaSAgentRouteDeckFacts(
                connection_count=1,
                ready_connection_count=1,
                action_count=8,
                tool_count=8,
                latest_execution_status="succeeded",
            )
        )
        == SaaSAgentRouteNodeIds.RESULT_REVIEW
    )
    assert (
        infer_current_node(
            SaaSAgentRouteDeckFacts(
                connection_count=0,
                ready_connection_count=0,
                action_count=0,
                tool_count=0,
            )
        )
        == SaaSAgentRouteNodeIds.NEEDS_CONNECTION
    )
    assert (
        infer_current_node(
            SaaSAgentRouteDeckFacts(
                connection_count=1,
                ready_connection_count=0,
                action_count=0,
                tool_count=0,
            )
        )
        == SaaSAgentRouteNodeIds.SCHEMA_PREVIEW
    )
    assert (
        infer_current_node(
            SaaSAgentRouteDeckFacts(
                connection_count=1,
                ready_connection_count=0,
                action_count=8,
                tool_count=0,
                latest_activation_status="running",
            )
        )
        == SaaSAgentRouteNodeIds.CATALOG_ACTIVATION
    )
    assert (
        infer_current_node(
            SaaSAgentRouteDeckFacts(
                connection_count=1,
                ready_connection_count=1,
                action_count=8,
                tool_count=8,
                latest_activation_status="ready",
            )
        )
        == SaaSAgentRouteNodeIds.CATALOG_READY
    )
