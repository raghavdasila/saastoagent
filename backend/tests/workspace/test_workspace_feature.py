from __future__ import annotations

from dataclasses import replace
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
from routedeck_core.app import compile_app
from routedeck_core.contracts.operations import DeliveryPhase, OperationSource
from routedeck_core.contracts.session import SessionSnapshot
from routedeck_core.state.session import navgraph_version

from corpus.bindings import bind_corpus_app
from corpus.auth.credential_transition import AccountOperationRequest
from corpus.auth.contracts import OwnerRouteContext
from corpus.composition import (
    AGENTS_FEATURE,
    BUILDER_SANDBOX_FEATURE,
    CHANNELS_FEATURE,
    CORPUS_APP,
    DESIGNER_FEATURE,
    EVALUATION_FEATURE,
    LOUNGE_FEATURE,
    OPERATIONS_FEATURE,
    WORKSPACE_FEATURE,
    _stable_unordered_contract_arrays,
    compile_corpus_app,
)
from corpus.features.lounge.declarations import (
    ARRIVAL_OPEN_REGISTRATION,
    ARRIVAL_OPEN_SIGN_IN,
    AUTHENTICATE_OWNER,
    CHANGE_OWNER_PASSWORD,
    CONFIRM_OWNER_EMAIL,
    CREATE_OWNER_ACCOUNT,
    HELP_RETURN_TO_LOUNGE,
    LOUNGE_CONTINUE_TO_WORKSPACE,
    REQUEST_PASSWORD_RESET,
    REQUEST_VERIFICATION_DELIVERY,
)
from corpus.features.lounge.operations import AuthenticatedLoungeNavigationHandler
from corpus.features.lounge.ports import LoungeSessionUnavailable
from corpus.features.agents.declarations import (
    CANCEL_CREATE,
    CREATE_AGENT,
    OPEN_CREATE,
    RETURN_TO_WORKSPACE,
    SAVE_AGENT_CHANGES,
)
from corpus.features.deployment.declarations import DEPLOY_AGENT, RETRY_DEPLOYMENT
from corpus.features.workspace.declarations import OPEN_AGENTS, OPEN_SOURCES
from corpus.features.workspace.policies import FILE_FIRST_TASK_ROUTING
from corpus.features.sources.declarations import OPEN_API_CREATION, RETURN_TO_HOME
from corpus.features.sources.feature import SOURCES_FEATURE
from corpus.session import create_guest_session, initialize_guest_session


def test_open_agent_creation_is_only_for_an_unfinished_distinct_create_request() -> None:
    assert OPEN_CREATE.description == (
        "Begin a distinct new-Agent configuration only when the owner's current "
        "request still needs a new Agent. This navigation creates nothing and must "
        "not follow a successful agent creation for that same request."
    )


def test_workspace_routes_attached_api_setup_through_sources_before_agent_choice() -> None:
    assert OPEN_SOURCES.description == (
        "Open Sources for work owned by a Source. When the current request includes "
        "a staged API definition to add, analyze, or use in broader setup, open "
        "Sources first so that exact file becomes an identifiable Source before "
        "choosing or creating an Agent."
    )
    assert OPEN_AGENTS.description == (
        "Open Agents for explicit Agent inventory or configuration work, or after "
        "the Source prerequisite in an ongoing file-first setup has begun. Do not "
        "skip an attached API definition that the current request still needs added "
        "and analyzed."
    )
    assert FILE_FIRST_TASK_ROUTING.instruction == (
        "When the current owner request includes a staged API definition and asks "
        "Corpus to use it in broader Agent setup, route to Sources first and continue "
        "the authorized add-and-analyze work before asking which Agent to use or "
        "create. Do not treat opening Agents as progress on an unaccepted staged file."
    )


def test_compiled_navgraph_version_is_stable_across_python_hash_seeds() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    command = (
        "from corpus.composition import compile_corpus_app; "
        "from routedeck_core.state.session import navgraph_version; "
        "print(navgraph_version(compile_corpus_app()))"
    )

    versions = []
    for seed in ("1", "2"):
        environment = os.environ.copy()
        environment["PYTHONHASHSEED"] = seed
        environment["PYTHONPATH"] = str(repository_root / "backend" / "src")
        versions.append(
            subprocess.check_output(
                [sys.executable, "-c", command],
                cwd=repository_root,
                env=environment,
                text=True,
            ).strip()
        )

    assert len(set(versions)) == 1


def test_stable_navgraph_document_changes_only_unordered_source_order() -> None:
    raw = json.loads(compile_app(CORPUS_APP).contract_documents()["compiled-navgraph.json"])
    stable = json.loads(
        compile_corpus_app().contract_documents()["compiled-navgraph.json"]
    )

    for node in raw["nodes"]:
        for operation in node["operations"]:
            operation["allowed_sources"] = sorted(operation["allowed_sources"])

    assert stable == raw


def test_contract_stabilization_ignores_reversed_source_registration_only() -> None:
    first = {
        "allowed_sources": ["agent", "surface"],
        "outcomes": ["second", "first"],
    }
    reversed_sources = {
        "allowed_sources": ["surface", "agent"],
        "outcomes": ["second", "first"],
    }

    assert _stable_unordered_contract_arrays(
        first
    ) == _stable_unordered_contract_arrays(reversed_sources)
    assert _stable_unordered_contract_arrays(first)["outcomes"] == [
        "second",
        "first",
    ]


def test_stable_navgraph_version_still_changes_for_a_real_contract_change() -> None:
    compiled = compile_corpus_app()
    changed = replace(
        compiled,
        graph=compiled.graph.model_copy(update={"name": "corpus-changed"}),
    )

    assert navgraph_version(changed) != navgraph_version(compiled)


class OwnerContextProbe:
    async def owner_context_for_route(self, route_session_id: str):
        del route_session_id
        return OwnerRouteContext(
            display_name="Owner",
            organization_name="Owner's Workspace",
            organization_slug="owner-workspace",
            role="owner",
            is_verified=False,
        )


class CredentialTransitionProbe:
    def current_request(self) -> AccountOperationRequest | None:
        return None

    def publish_issued_tokens(self, tokens) -> None:
        raise AssertionError(f"Unexpected issued tokens: {tokens!r}")

    def publish_revocation(self) -> None:
        raise AssertionError("Unexpected credential revocation")


class LoungeOwnerGuardProbe:
    def __init__(self, *, authenticated: bool) -> None:
        self.authenticated = authenticated
        self.route_session_ids: list[str] = []

    async def require_owner_for_route(self, route_session_id: str) -> None:
        self.route_session_ids.append(route_session_id)
        if not self.authenticated:
            raise LoungeSessionUnavailable("Owner context unavailable")


def test_composition_selects_workspace_and_sources_and_enters_the_lounge() -> None:
    compiled = compile_corpus_app()

    assert CORPUS_APP.features == (
        LOUNGE_FEATURE,
        WORKSPACE_FEATURE,
        AGENTS_FEATURE,
        DESIGNER_FEATURE,
        BUILDER_SANDBOX_FEATURE,
        EVALUATION_FEATURE,
        CHANNELS_FEATURE,
        OPERATIONS_FEATURE,
        SOURCES_FEATURE,
    )
    assert compiled.frontend_contract.entry_node_id == "lounge.home"
    assert set(compiled.frontend_contract.nodes) == {
        "lounge.home",
        "lounge.product_help",
        "lounge.sign_in",
        "lounge.register",
        "lounge.forgot_password",
        "lounge.reset_password",
        "lounge.verify_email",
        "lounge.verification_pending",
        "workspace.home",
        "agents.home",
        "agents.create",
        "designer.home",
        "builder.home",
        "sandbox.home",
        "evaluation.home",
        "channels.home",
        "operations.home",
        "sources.home",
        "sources.api_intake",
        "sources.api",
    }


def test_checked_in_frontend_contract_matches_compiled_product_contract() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    checked_in = json.loads(
        (
            repository_root
            / "frontend"
            / "src"
            / "routedeck"
            / "corpus-frontend-contract.generated.json"
        ).read_text(encoding="utf-8")
    )

    assert checked_in == compile_corpus_app().frontend_contract.model_dump(mode="json")


def test_agents_home_exposes_exact_lifecycle_affordances() -> None:
    surface = compile_corpus_app().frontend_contract.surfaces["agents.home"]
    affordances = {
        affordance.id: affordance.operation.id
        for affordance in surface.affordances
    }
    assert affordances["archive_agent"] == "agents.archive_agent"
    assert affordances["delete_agent"] == "agents.delete_agent"


def test_deployment_operations_target_their_exact_review_surfaces() -> None:
    assert DEPLOY_AGENT.public_metadata_value() == {
        "review_surface_id": "deployment.deploy_review"
    }
    assert RETRY_DEPLOYMENT.public_metadata_value() == {
        "review_surface_id": "deployment.retry_review"
    }


def test_selected_agent_work_areas_expose_guided_navigation_without_mutation() -> None:
    contract = compile_corpus_app().frontend_contract
    expected = {
        "designer.home": ("continue_to_builds", "agents.open_builds", "builder.home"),
        "builder.home": ("continue_to_sandbox", "agents.open_sandbox", "sandbox.home"),
        "sandbox.home": ("continue_to_evaluation", "agents.open_evaluation", "evaluation.home"),
        "evaluation.home": ("continue_to_channels", "agents.open_channels", "channels.home"),
        "channels.home": ("continue_to_operations", "agents.open_operations", "operations.home"),
    }
    transitions = {
        (transition.source, transition.operation_id, transition.target)
        for transition in contract.transitions
    }

    for node_id, (affordance_id, operation_id, target_id) in expected.items():
        surface_id = contract.nodes[node_id].surfaces.active
        affordances = {
            affordance.id: affordance.operation.id
            for affordance in contract.surfaces[surface_id].affordances
        }
        assert affordances[affordance_id] == operation_id
        assert operation_id in contract.nodes[node_id].operation_ids
        assert (node_id, operation_id, target_id) in transitions

    channels_affordances = {
        affordance.id: affordance.operation.id
        for affordance in contract.surfaces["channels.home"].affordances
    }
    assert channels_affordances["continue_to_evaluation"] == "agents.open_evaluation"
    assert "agents.open_evaluation" in contract.nodes["channels.home"].operation_ids
    assert ("channels.home", "agents.open_evaluation", "evaluation.home") in transitions

    evaluation_affordances = {
        affordance.id: affordance.operation.id
        for affordance in contract.surfaces["evaluation.home"].affordances
    }
    assert evaluation_affordances["continue_to_builds"] == "agents.open_builds"
    assert "agents.open_builds" in contract.nodes["evaluation.home"].operation_ids
    assert ("evaluation.home", "agents.open_builds", "builder.home") in transitions


def test_lounge_and_workspace_own_their_operations_transitions_and_surfaces() -> None:
    contract = compile_corpus_app().frontend_contract

    assert set(contract.nodes["lounge.home"].operation_ids) == {
        "lounge.open_product_help",
        "lounge.arrival.open_sign_in",
        "lounge.arrival.open_registration",
        "lounge.continue_to_workspace",
    }
    assert contract.nodes["lounge.home"].surfaces.active == "lounge.home"
    assert contract.nodes["lounge.sign_in"].surfaces.active == "lounge.sign_in"
    assert contract.nodes["lounge.register"].surfaces.active == "lounge.register"
    for node_id in (
        "lounge.sign_in",
        "lounge.register",
        "lounge.forgot_password",
        "lounge.reset_password",
        "lounge.verify_email",
    ):
        policy = contract.nodes[node_id].conversation_input
        assert policy.enabled is False
        assert policy.disabled_message == (
            "Chat is disabled while entering private account information."
        )
    assert contract.nodes["workspace.home"].conversation_input.enabled is True
    assert contract.nodes["sources.home"].surfaces.active == "sources.home"
    assert set(contract.nodes["workspace.home"].operation_ids) == {
        "workspace.open_agents",
        "workspace.open_sources",
        "workspace.open_verification",
    }
    assert set(contract.nodes["sources.home"].operation_ids) == {
        "agents.attach_created_source",
        "agents.return_from_source",
            "sources.open_api_creation",
            "sources.open_api_description",
            "sources.open_api_source",
        "sources.return_to_home",
    }
    assert contract.nodes["sources.api_intake"].surfaces.active == "sources.api_intake"
    assert set(contract.nodes["sources.api_intake"].operation_ids) == {
        "agents.return_from_source",
        "sources.accept_staged_api",
        "sources.return_to_source_hub",
    }
    assert contract.nodes["sources.api"].surfaces.active == "sources.api"
    assert set(contract.nodes["sources.api"].operation_ids) == {
        "agents.open_create",
        "agents.attach_created_source",
        "agents.open_builds",
        "agents.return_from_source",
        "agents.choose_existing_for_source",
            "sources.process_api",
            "sources.inspect_current_api",
            "sources.retry_processing",
            "sources.return_to_source_hub",
            "sources.open_api_description",
            "sources.save_api_description",
            "sources.delete_api_source",
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
    }
    expected = {
        ("lounge.home", "lounge.open_product_help", "lounge.product_help"),
        ("lounge.home", "lounge.arrival.open_sign_in", "lounge.sign_in"),
        ("lounge.home", "lounge.continue_to_workspace", "workspace.home"),
        (
            "lounge.home",
            "lounge.arrival.open_registration",
            "lounge.register",
        ),
        ("lounge.sign_in", "lounge.sign_in.return_to_lounge", "lounge.home"),
        ("lounge.register", "lounge.registration.return_to_lounge", "lounge.home"),
        ("lounge.sign_in", "lounge.sign_in.open_password_recovery", "lounge.forgot_password"),
        ("lounge.sign_in", "lounge.authenticate_owner_account", "workspace.home"),
        ("lounge.register", "lounge.create_owner_account", "workspace.home"),
        ("lounge.forgot_password", "lounge.request_password_reset.return_to_lounge", "lounge.home"),
        ("lounge.reset_password", "lounge.change_password.return_to_lounge", "lounge.home"),
        ("lounge.verify_email", "lounge.confirm_email.return_to_lounge", "lounge.home"),
        ("workspace.home", "workspace.open_sources", "sources.home"),
        ("workspace.home", "workspace.open_agents", "agents.home"),
        ("agents.home", "agents.open_create", "agents.create"),
        ("agents.create", "agents.create_agent", "agents.home"),
        ("agents.create", "agents.cancel_create", "agents.home"),
        ("agents.home", "agents.save_changes", "agents.home"),
        ("agents.home", "agents.return_to_workspace", "workspace.home"),
        ("agents.home", "agents.select_agent", "agents.home"),
        ("agents.home", "agents.attach_source", "agents.home"),
        ("agents.home", "agents.open_source_creation", "sources.api_intake"),
        ("agents.home", "agents.open_attached_source", "sources.api"),
        ("agents.home", "agents.open_build_source_revision", "sources.api"),
        ("workspace.home", "workspace.open_verification", "lounge.verification_pending"),
        ("lounge.verification_pending", "lounge.verification_delivery.return_to_workspace", "workspace.home"),
        ("sources.home", "sources.return_to_home", "workspace.home"),
        ("sources.home", "sources.open_api_creation", "sources.api_intake"),
        ("sources.home", "sources.open_api_source", "sources.api"),
        ("sources.api_intake", "sources.accept_staged_api", "sources.api"),
        ("sources.api_intake", "sources.return_to_source_hub", "sources.home"),
        ("sources.api", "sources.process_api", "sources.api"),
        ("sources.api", "sources.retry_processing", "sources.api"),
        ("sources.api", "sources.return_to_source_hub", "sources.home"),
        ("sources.api", "agents.open_builds", "builder.home"),
        ("builder.home", "agents.open_attached_source", "sources.api"),
        ("sources.api", "agents.choose_existing_for_source", "agents.home"),
        ("sources.api", "agents.open_create", "agents.create"),
        ("sources.home", "agents.attach_created_source", "agents.home"),
        ("sources.home", "agents.return_from_source", "agents.home"),
    }
    assert expected.issubset(
        {
            (transition.source, transition.operation_id, transition.target)
            for transition in contract.transitions
        }
    )


@pytest.mark.asyncio
async def test_lounge_workspace_continuation_is_guarded_by_the_same_route_session() -> None:
    context = SimpleNamespace(
        source=OperationSource.SURFACE,
        session_id="historical-lounge-session",
        attempt_id="attempt-lounge-owner",
        request_id="request-lounge-owner",
    )
    anonymous = LoungeOwnerGuardProbe(authenticated=False)
    anonymous_outcome = await AuthenticatedLoungeNavigationHandler(
        anonymous,  # type: ignore[arg-type]
        LOUNGE_CONTINUE_TO_WORKSPACE.id,
    )({}, context)  # type: ignore[arg-type]

    assert anonymous.route_session_ids == ["historical-lounge-session"]
    assert anonymous_outcome.failure is not None
    assert anonymous_outcome.failure.code == "authentication_required"
    assert anonymous_outcome.failure.safe_details.http_status == 401

    owner = LoungeOwnerGuardProbe(authenticated=True)
    owner_outcome = await AuthenticatedLoungeNavigationHandler(
        owner,  # type: ignore[arg-type]
        LOUNGE_CONTINUE_TO_WORKSPACE.id,
    )({}, context)  # type: ignore[arg-type]

    assert owner.route_session_ids == ["historical-lounge-session"]
    assert owner_outcome.outcome == "opened"
    assert owner_outcome.failure is None


def test_operations_allow_only_the_designed_invocation_sources() -> None:
    compiled = compile_corpus_app()
    agent_and_surface = frozenset(
        {OperationSource.AGENT, OperationSource.SURFACE}
    )
    agent_only = frozenset({OperationSource.AGENT})
    surface_only = frozenset({OperationSource.SURFACE})

    expected = {
        "lounge.open_product_help": agent_and_surface,
        "lounge.arrival.open_registration": agent_and_surface,
        "lounge.arrival.open_sign_in": agent_and_surface,
        "lounge.continue_to_workspace": surface_only,
        "lounge.product_help.return_to_lounge": agent_only,
        "lounge.product_help.open_registration": agent_and_surface,
        "lounge.product_help.open_sign_in": agent_and_surface,
        "lounge.create_owner_account": surface_only,
        "lounge.registration.continue_to_workspace": surface_only,
        "lounge.registration.return_to_lounge": surface_only,
        "lounge.authenticate_owner_account": surface_only,
        "lounge.sign_in.continue_to_workspace": surface_only,
        "lounge.sign_in.open_password_recovery": agent_and_surface,
        "lounge.sign_in.return_to_lounge": surface_only,
        "lounge.request_password_reset": surface_only,
        "lounge.request_password_reset.return_to_lounge": surface_only,
        "lounge.change_owner_password": surface_only,
        "lounge.change_password.return_to_lounge": surface_only,
        "lounge.request_verification_delivery": surface_only,
        "lounge.verification_delivery.return_to_workspace": surface_only,
        "lounge.confirm_owner_email": surface_only,
        "lounge.confirm_email.return_to_lounge": surface_only,
        "workspace.open_sources": agent_and_surface,
        "workspace.open_agents": agent_and_surface,
        "workspace.open_verification": agent_and_surface,
        "agents.open_create": agent_and_surface,
        "agents.choose_existing_for_source": agent_and_surface,
        "agents.return_to_workspace": agent_and_surface,
        "agents.return_to_hub": agent_and_surface,
        "agents.create_agent": agent_and_surface,
        "agents.save_changes": agent_and_surface,
        "agents.cancel_create": agent_and_surface,
        "agents.select_agent": agent_and_surface,
            "agents.attach_source": agent_and_surface,
            "agents.detach_source": agent_and_surface,
        "agents.open_source_creation": agent_and_surface,
        "agents.attach_created_source": agent_and_surface,
        "agents.open_attached_source": agent_and_surface,
        "agents.return_from_source": agent_and_surface,
        "agents.archive_agent": agent_and_surface,
        "agents.delete_agent": agent_and_surface,
        "agents.open_build_source_revision": agent_and_surface,
        "agents.open_builds": agent_and_surface,
        "agents.open_channels": agent_and_surface,
        "agents.open_designer": agent_and_surface,
        "agents.open_evaluation": agent_and_surface,
        "agents.open_operations": agent_and_surface,
            "agents.open_sandbox": agent_and_surface,
                "builder.assemble": agent_and_surface,
                "builder.run": agent_and_surface,
                "builder.pause": agent_and_surface,
                "builder.stop": agent_and_surface,
            "builder.delete": agent_and_surface,
        "channels.create": agent_and_surface,
        "channels.set_enabled": agent_and_surface,
            "deployment.deploy": agent_and_surface,
            "deployment.retry": agent_and_surface,
            "deployment.rollback": agent_and_surface,
        "designer.approve": agent_and_surface,
        "designer.customize": agent_and_surface,
        "designer.generate_feature": agent_and_surface,
        "designer.propose": agent_and_surface,
        "designer.request_build": agent_and_surface,
        "designer.return_to_agent": agent_and_surface,
            "evaluation.create_case": agent_and_surface,
            "evaluation.generate_set": agent_and_surface,
            "evaluation.retry_generation": agent_and_surface,
            "evaluation.edit_case": agent_and_surface,
                "evaluation.delete_case": agent_and_surface,
                "evaluation.run_case": agent_and_surface,
                "evaluation.retry_case_run": agent_and_surface,
        "operations.promote_evaluation_case": agent_and_surface,
            "sandbox.start": agent_and_surface,
            "sandbox.resume": agent_and_surface,
        "sources.return_to_home": agent_and_surface,
        "sources.accept_staged_api": agent_and_surface,
        "sources.open_api_creation": agent_and_surface,
        "sources.open_api_source": agent_and_surface,
            "sources.return_to_source_hub": agent_and_surface,
            "sources.open_api_description": agent_and_surface,
            "sources.save_api_description": agent_and_surface,
            "sources.delete_api_source": agent_and_surface,
            "sources.process_api": agent_and_surface,
        "sources.inspect_current_api": agent_only,
        "sources.retry_processing": agent_and_surface,
            "sources.select_graph_stage": agent_and_surface,
            "sources.save_api_connection": surface_only,
            "sources.propose_contract_revision": agent_and_surface,
                "sources.approve_contract_revision": agent_and_surface,
                "sources.test_api_connection": agent_and_surface,
                    "sources.save_api_operation_curation": agent_and_surface,
                            "sources.prepare_routed_api_test": agent_and_surface,
                            "sources.create_api_route_plan": agent_and_surface,
                            "sources.continue_api_route_plan": agent_and_surface,
                            "sources.test_routed_api_read": agent_and_surface,
                        "sources.test_routed_api_write": agent_and_surface,
    }

    assert set(compiled.operations) == set(expected)
    assert {
        operation_id: operation.allowed_sources
        for operation_id, operation in compiled.operations.items()
    } == expected


def test_open_source_creation_describes_the_owner_intent_not_the_ui() -> None:
    operation = compile_corpus_app().operations["agents.open_source_creation"]

    assert operation.description == (
        "Begin intake for a new API definition the owner wants to add to the selected "
        "Agent, retaining that Agent and making no attachment yet."
    )
    assert "Source Hub" not in operation.description


def test_lounge_policies_are_compiled_as_routedeck_agent_policies() -> None:
    compiled = compile_corpus_app()

    lounge = next(
        feature
        for feature in compiled.application.features
        if feature.namespace == "lounge"
    )
    lounge_home = next(node for node in lounge.nodes if node.id == "lounge.home")
    assert lounge_home.entry_turn is not None
    assert lounge_home.entry_turn.id == "welcome"
    assert {ref.id for ref in lounge.policy_refs} == {
        "lounge.feature.public_context_only",
        "lounge.feature.account_access_boundary",
        "lounge.feature.chrome_boundary",
        "lounge.feature.prompt",
        "lounge.feature.task_boundary",
        "lounge.feature.task_redirection",
        "lounge.feature.user_facing_language",
    }
    assert (
        compiled.agent_policies["lounge.feature.prompt"].instruction
        == "You are Corpus in the public Lounge, an unauthenticated helpdesk about "
        "Corpus only. Answer questions about Corpus, its current features, and how "
        "the product works. Do not design, plan, troubleshoot, or perform the "
        "visitor's task in Lounge. When a visitor starts describing work they want "
        "Corpus to do, briefly explain that work happens in a private Workspace and "
        "ask them to sign in or sign up through the available product surfaces. "
        "Never collect credentials in chat. On an assistant-initiated Lounge turn, "
        "briefly establish that the visitor is in the Lounge, explain that you can "
        "answer questions about Corpus, and invite a question about the product."
    )
    assert len(compiled.agent_policies) >= 40


@pytest.mark.asyncio
async def test_workspace_navigation_bindings_return_only_declared_outcomes() -> None:
    compiled = compile_corpus_app()
    credential_transition = CredentialTransitionProbe()
    bound = bind_corpus_app(
        compiled,
        OwnerContextProbe(),
        auth_service=object(),
        auth_limiter=object(),
        auth_mail=object(),
        auth_settings=SimpleNamespace(public_frontend_url="http://corpus.test"),
        private_form_store=object(),
        private_form_codec=object(),
        credential_transition=credential_transition,
        agent_service=object(),
        designer_service=object(),
        builder_service=object(),
        sandbox_service=object(),
        evaluation_service=object(),
        channel_service=object(),
        deployment_service=object(),
        operations_service=object(),
        workspace_service=object(),
            source_service=object(),
            source_graph_presenter=object(),
            source_connection_service=object(),
                source_contract_revision_service=object(),
                    source_connection_check_service=object(),
                    source_operation_curation_service=object(),
    )

    for operation in (
        CREATE_OWNER_ACCOUNT,
        AUTHENTICATE_OWNER,
        REQUEST_PASSWORD_RESET,
        CHANGE_OWNER_PASSWORD,
        REQUEST_VERIFICATION_DELIVERY,
        CONFIRM_OWNER_EMAIL,
    ):
        handler = bound.bindings.handlers[operation.ref]
        assert handler.credential_transition.transition is credential_transition

    for operation in (
        ARRIVAL_OPEN_SIGN_IN,
        ARRIVAL_OPEN_REGISTRATION,
        HELP_RETURN_TO_LOUNGE,
        OPEN_SOURCES,
        OPEN_AGENTS,
        OPEN_CREATE,
        CANCEL_CREATE,
        RETURN_TO_WORKSPACE,
        RETURN_TO_HOME,
        OPEN_API_CREATION,
    ):
        outcome = await bound.bindings.handlers[operation.ref](
            {}, None  # type: ignore[arg-type]
        )
        assert outcome.outcome == "opened"
        assert outcome.delivery_phase is DeliveryPhase.RESPONSE_RECEIVED
        assert outcome.failure is None


@pytest.mark.asyncio
async def test_account_operations_fail_explicitly_without_a_request_context() -> None:
    compiled = compile_corpus_app()
    bound = bind_corpus_app(
        compiled,
        OwnerContextProbe(),
        auth_service=object(),
        auth_limiter=object(),
        auth_mail=object(),
        auth_settings=SimpleNamespace(public_frontend_url="http://corpus.test"),
        private_form_store=object(),
        private_form_codec=object(),
        credential_transition=CredentialTransitionProbe(),
        agent_service=object(),
        designer_service=object(),
        builder_service=object(),
        sandbox_service=object(),
        evaluation_service=object(),
        channel_service=object(),
        deployment_service=object(),
        operations_service=object(),
        workspace_service=object(),
            source_service=object(),
            source_graph_presenter=object(),
            source_connection_service=object(),
                source_contract_revision_service=object(),
                    source_connection_check_service=object(),
                    source_operation_curation_service=object(),
    )
    context = SimpleNamespace(
        source=OperationSource.SURFACE,
        attempt_id="attempt-context-required",
        request_id="request-context-required",
    )

    for operation in (
        CREATE_OWNER_ACCOUNT,
        AUTHENTICATE_OWNER,
        REQUEST_PASSWORD_RESET,
        CHANGE_OWNER_PASSWORD,
        REQUEST_VERIFICATION_DELIVERY,
        CONFIRM_OWNER_EMAIL,
    ):
        outcome = await bound.bindings.handlers[operation.ref](
            {}, context  # type: ignore[arg-type]
        )

        assert outcome.failure is not None
        assert outcome.failure.code == "http_request_context_required"
        assert outcome.failure.phase == "request_context"


@pytest.mark.asyncio
async def test_guest_session_has_no_invented_principal_or_authentication_state() -> None:
    compiled = compile_corpus_app()
    session = create_guest_session(compiled, "guest-contract")

    assert session.current.node_id == "lounge.home"
    assert session.private_state.configurations == ()
    assert session.public_state.status_code == "ready"
    source_surface = next(
        state
        for state in session.public_state.surface_state
        if state.surface_id == "sources.api"
    )
    assert source_surface.values[0].name == "form_handle"
    assert source_surface.values[0].value.to_python() == "sources-api-connection"
    initialized = await initialize_guest_session(
        None,  # type: ignore[arg-type]
        SessionSnapshot(state=session),
    )
    assert initialized.state is session


def test_designer_to_builder_chat_context_continues_the_user_task() -> None:
    from corpus.features.agents.declarations import OPEN_AGENT_BUILDS, OPEN_AGENT_DESIGNER
    from corpus.features.builder.declarations import ASSEMBLE_BUILD
    from corpus.features.designer.declarations import RETURN_TO_AGENT

    assert any(
        "use the available legal navigation and continue the same conversation"
        in policy.instruction
        for policy in DESIGNER_FEATURE.agent_policies
    )
    assert "reaching the hub is not task completion" in RETURN_TO_AGENT.description
    assert "reaching Builds is not task completion" in OPEN_AGENT_BUILDS.description
    assert "do not use it to assemble a build whose request already exists" in (
        OPEN_AGENT_DESIGNER.description
    )
    assert "completing the owner's explicit request" in ASSEMBLE_BUILD.description
    assert any(
        "belongs in Builds, not Designer" in policy.instruction
        for policy in AGENTS_FEATURE.agent_policies
    )


def test_attached_api_setup_uses_existing_supervised_operations_without_manual_reupload() -> None:
    compiled = compile_corpus_app()

    assert "without asking the owner to upload or select the same file again" in (
        compiled.agent_policies["sources.staged_setup_continuation"].instruction
    )
    source_continuation = compiled.agent_policies[
        "sources.staged_setup_continuation"
    ].instruction
    assert "ask immediately whether the owner wants to use an existing Agent" in (
        source_continuation
    )
    assert "do not promise automatic continuation" in source_continuation
    assert "API version rather than a Source revision" in source_continuation
    assert (
        "ask only for missing agent choice, goal, responsibilities, or operation-selection intent"
        in compiled.agent_policies["agents.capability.setup_continuation"].instruction.lower()
    )
    setup_continuation = compiled.agent_policies[
        "agents.capability.setup_continuation"
    ].instruction.lower()
    assert "derive a concise display name from that exact role phrase" in setup_continuation
    assert "do not ask another question solely for a name" in setup_continuation
    assert "do not invent capabilities" in setup_continuation
    create_description = compiled.operations["agents.create_agent"].description.lower()
    assert "ongoing file-first setup" in create_description
    assert "clear role phrase and responsibilities" in create_description
    assert "derive a concise display name from the owner's exact role phrase" in create_description
    attachment_policy = compiled.agent_policies[
        "agents.capability.attachment_eligibility"
    ].instruction.lower()
    assert "keep one attachment per source" in attachment_policy
    assert "advance only that source's pinned revision" in attachment_policy
    attach_description = compiled.operations["agents.attach_source"].description.lower()
    assert "repeating the same current version is idempotent" in attach_description
    assert "newer reviewed ready api version" in attach_description
    assert "without changing historical build lineage" in attach_description
    return_description = compiled.operations["agents.return_from_source"].description.lower()
    assert "explicitly asks to leave the current api setup" in return_description
    assert "asks to remain with the current api" in return_description
    assert "do not use this operation" in return_description
    active_api_continuation = compiled.agent_policies[
        "sources.active_api_continuation"
    ].instruction.lower()
    assert "explicitly asks to update that attachment or continue agent setup" in (
        active_api_continuation
    )
    assert "asks to remain with the current api" in active_api_continuation
    assert "current request has already authorized creating and analyzing" in (
        compiled.operations["sources.open_api_creation"].description
    )
    assert "current request still needs a new Agent" in (
        compiled.operations["agents.open_create"].description
    )
