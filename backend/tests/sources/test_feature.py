from __future__ import annotations

from routedeck_core.contracts.navigation import DeepLinkPolicy

from corpus.composition import compile_corpus_app
from corpus.features.sources.policies import CONTRACT_REVISION_TRUTH


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
        "sources.open_api_source",
        "sources.return_to_home",
    }
    api_node = contract.nodes["sources.api"]
    assert api_node.title == "API Source"
    assert api_node.route_template == "/sources/api"
    assert api_node.surfaces.active == "sources.api"
    assert contract.surfaces["sources.api"].component == "sources.api"
    assert set(api_node.operation_ids) == {
        "agents.open_create",
        "sources.accept_staged_api",
        "agents.attach_created_source",
        "agents.return_from_source",
        "workspace.open_agents",
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
            "sources.test_routed_api_read",
            "sources.test_routed_api_write",
    }
    assert {
        (transition.source, transition.operation_id, transition.target)
        for transition in contract.transitions
    } >= {
        ("sources.api", "workspace.open_agents", "agents.home"),
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
        and action.operation_id == "sources.prepare_routed_api_test"
        and not action.arguments
        for action in compiled.nodes["sources.api"].suggested_actions
    )
    assert api_node.surfaces.review == (
        "sources.contract_revision_review",
        "sources.routed_api_write_review",
    )
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
