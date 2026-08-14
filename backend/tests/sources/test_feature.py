from __future__ import annotations

from types import SimpleNamespace

import pytest
from routedeck_core.contracts.navigation import DeepLinkPolicy
from routedeck_core.contracts.projection import FrozenJson, FrozenJsonObject, PublicValue

from corpus.composition import compile_corpus_app
from corpus.features.sources.declarations import (
    APPROVE_CONTRACT_REVISION,
    SELECTED_API_SOURCE_PROVIDER,
)
from corpus.features.sources.operations import _selected_source_handoff_context
from corpus.features.sources.policies import CONTRACT_REVISION_TRUTH
from corpus.features.sources.providers import SelectedApiSourceProvider


@pytest.mark.asyncio
async def test_selected_source_context_exposes_an_exact_agent_pin_update() -> None:
    class SourceService:
        def __init__(self) -> None:
            self.request = None

        def get_source(self, **request):
            self.request = request
            return SimpleNamespace(
                display_name="Store API",
                revision=SimpleNamespace(state=SimpleNamespace(value="ready")),
            )

    class OwnerScope:
        async def organization_id_for_route(self, session_id: str):
            assert session_id == "route-session-001"
            return "owner-001"

    service = SourceService()
    provider = SelectedApiSourceProvider(service, OwnerScope())
    result = await provider(
        SimpleNamespace(
            session=SimpleNamespace(
                session_id="route-session-001",
                public_state=SimpleNamespace(
                    surface_state=(
                        SimpleNamespace(
                            surface_id="sources.api",
                            values=(
                                PublicValue(name="selected_source_id", value=FrozenJson("sourceopaque0001")),
                                PublicValue(name="selected_source_revision_id", value=FrozenJson("currentrevision1")),
                            ),
                        ),
                    ),
                    entity_handles=(
                        SimpleNamespace(
                            entity_kind="agent",
                            handle="agent-canonical-001",
                            values=(
                                PublicValue(name="attached_source_id", value=FrozenJson("sourceopaque0001")),
                                PublicValue(name="attached_source_revision_id", value=FrozenJson("attachedrev00001")),
                            ),
                        ),
                    ),
                )
            )
        )
    )

    assert result.values.to_dict() == {
        "source_id": "sourceopaque0001",
        "source_revision_id": "currentrevision1",
        "display_name": "Store API",
        "processing_state": "ready",
        "return_agent_ref": "agent-canonical-001",
        "agent_handoff_mode": "inspect",
        "attached_source_revision_id": "attachedrev00001",
        "return_context": "agent",
        "attachment_update_available": True,
    }
    assert service.request == {
        "owner_key": "owner-001",
        "source_id": "sourceopaque0001",
        "revision_id": "currentrevision1",
    }


def test_contract_approval_handoff_preserves_the_attached_agent_revision() -> None:
    assert SELECTED_API_SOURCE_PROVIDER.ref.id in {
        provider.id for provider in APPROVE_CONTRACT_REVISION.provider_refs
    }
    context = _selected_source_handoff_context(
        FrozenJsonObject(
            {
                "sources.selected_api_source": {
                    "return_agent_ref": "agent-canonical-001",
                    "agent_handoff_mode": "inspect",
                    "attached_source_revision_id": "attachedrev00001",
                    "return_context": "agent",
                    "initial_workspace": "operations",
                    "selected_source_revision_id": "currentrevision1",
                }
            }
        ),
        selected_revision_id="approvedrevision1",
    )

    assert context == {
        "return_agent_ref": "agent-canonical-001",
        "agent_handoff_mode": "inspect",
        "attached_source_revision_id": "attachedrev00001",
        "attachment_update_available": True,
        "return_context": "agent",
        "initial_workspace": "operations",
    }

    compiled = compile_corpus_app()
    source_surface_schema = compiled.surfaces["sources.api"].public_props_schema_value()
    assert source_surface_schema["properties"]["attachment_update_available"] == {
        "type": "boolean"
    }


def test_sources_exposes_inventory_intake_and_retry_through_routedeck() -> None:
    compiled = compile_corpus_app()
    contract = compiled.frontend_contract
    node = contract.nodes["sources.home"]

    assert node.title == "Sources"
    assert node.route_template == "/sources"
    assert node.deep_link_policy == DeepLinkPolicy.SESSION_BOUND.value
    assert node.surfaces.active == "sources.home"
    assert contract.surfaces["sources.home"].component == "sources.home"
    assert set(node.operation_ids) == {
        "agents.attach_created_source",
        "agents.return_from_source",
        "sources.open_api_creation",
        "sources.open_api_description",
        "sources.open_api_source",
        "sources.return_to_home",
    }
    intake_node = contract.nodes["sources.api_intake"]
    assert intake_node.title == "New API Source"
    assert intake_node.route_template == "/sources/api/new"
    assert intake_node.surfaces.active == "sources.api_intake"
    assert contract.surfaces["sources.api_intake"].component == "sources.api_intake"
    assert set(intake_node.operation_ids) == {
        "agents.return_from_source",
        "sources.accept_staged_api",
        "sources.return_to_source_hub",
    }
    api_node = contract.nodes["sources.api"]
    assert api_node.title == "API Source"
    assert api_node.route_template == "/sources/api"
    assert api_node.surfaces.active == "sources.api"
    assert contract.surfaces["sources.api"].component == "sources.api"
    assert {
        provider.id for provider in compiled.nodes["sources.api"].context_providers
    } == {"corpus.owner_context", "sources.selected_api_source"}
    assert {
        provider.id
        for provider in compiled.operations["sources.inspect_current_api"].provider_refs
    } == {"corpus.owner_context", "sources.selected_api_source"}
    assert set(api_node.operation_ids) == {
            "agents.open_create",
            "agents.choose_existing_for_source",
            "agents.attach_created_source",
            "agents.open_builds",
            "agents.return_from_source",
        "sources.process_api",
        "sources.inspect_current_api",
        "sources.retry_processing",
        "sources.return_to_source_hub",
        "sources.select_graph_stage",
        "sources.save_api_connection",
        "sources.propose_contract_revision",
        "sources.approve_contract_revision",
        "sources.test_api_connection",
            "sources.save_api_operation_curation",
                "sources.prepare_routed_api_test",
                "sources.create_api_route_plan",
                "sources.continue_api_route_plan",
                "sources.test_routed_api_read",
            "sources.test_routed_api_write",
            "sources.open_api_description",
            "sources.save_api_description",
            "sources.delete_api_source",
    }
    assert {
        (transition.source, transition.operation_id, transition.target)
        for transition in contract.transitions
    } >= {
        ("sources.home", "sources.open_api_creation", "sources.api_intake"),
        ("sources.home", "sources.open_api_source", "sources.api"),
        ("sources.api_intake", "sources.accept_staged_api", "sources.api"),
            ("sources.api", "agents.choose_existing_for_source", "agents.home"),
        ("sources.api", "agents.open_create", "agents.create"),
    }
    assert api_node.surfaces.detail == (
        "sources.contract_revision_proposal",
        "sources.api_operation_test",
    )
    assert contract.surfaces["sources.api_operation_test"].component == (
        "sources.api_operation_test"
    )
    assert any(
        action.id == "api-test-operation"
        and action.label == "Try an API request"
        and action.operation_id == "sources.prepare_routed_api_test"
        and not action.arguments
        for action in compiled.nodes["sources.api"].suggested_actions
    )
    assert api_node.surfaces.review == (
        "sources.contract_revision_review",
        "sources.routed_api_write_review",
        "sources.delete_review",
    )
    delete_source = compiled.operations["sources.delete_api_source"]
    assert delete_source.safety_class.value == "destructive"
    assert delete_source.review_policy.value == "required"
    assert {item.value for item in delete_source.allowed_sources} == {
        "agent",
        "surface",
    }
    assert {guard.id for guard in delete_source.guard_refs} == {
        "sources.source_delete_current",
    }
    assert compiled.operations["sources.approve_contract_revision"].review_policy.value == "required"
    proposal = compiled.operations["sources.propose_contract_revision"]
    assert proposal.outcome_schemas.to_python()["proposed"] == {
        "type": "object",
        "properties": {
            "proposal_state": {"const": "proposal_prepared"},
            "review_staged": {"const": False},
            "next_owner_decision": {"const": "request_owner_review"},
        },
        "required": [
            "proposal_state",
            "review_staged",
            "next_owner_decision",
        ],
        "additionalProperties": False,
    }
    assert "Asking what the proposal changes or what its consequences are is read-only" in (
        CONTRACT_REVISION_TRUTH.instruction
    )
    assert "Only an explicit request to begin or open the owner review stages it" in (
        CONTRACT_REVISION_TRUTH.instruction
    )
    safe_check = compiled.operations["sources.test_api_connection"]
    assert safe_check.safety_class.value == "read_external"
    assert safe_check.review_policy.value == "none"
    curation = compiled.operations["sources.save_api_operation_curation"]
    assert curation.safety_class.value == "draft"
    assert curation.review_policy.value == "none"
    assert {item.value for item in curation.allowed_sources} == {"agent", "surface"}
    assert curation.outcomes == ("saved",)
    assert "pass only included_operation_ids" in curation.description
    assert "sources.api_operation_curation_current" in {
        item.id for item in curation.guard_refs
    }
    assert safe_check.allowed_sources == frozenset({"agent", "surface"})
    assert safe_check.outcomes == ("checked",)
