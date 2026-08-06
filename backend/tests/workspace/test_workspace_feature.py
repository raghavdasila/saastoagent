from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from routedeck_core.contracts.operations import DeliveryPhase, OperationSource
from routedeck_core.contracts.session import SessionSnapshot

from corpus.bindings import bind_corpus_app
from corpus.auth.credential_transition import AccountOperationRequest
from corpus.auth.contracts import OwnerRouteContext
from corpus.composition import (
    AGENTS_FEATURE,
    CORPUS_APP,
    LOUNGE_FEATURE,
    WORKSPACE_FEATURE,
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
    REQUEST_PASSWORD_RESET,
    REQUEST_VERIFICATION_DELIVERY,
)
from corpus.features.agents.declarations import (
    CANCEL_CREATE,
    CREATE_AGENT,
    OPEN_CREATE,
    RETURN_TO_WORKSPACE,
    SAVE_AGENT_CHANGES,
)
from corpus.features.workspace.declarations import OPEN_AGENTS, OPEN_SOURCES
from corpus.features.sources.declarations import RETURN_TO_HOME
from corpus.features.sources.feature import SOURCES_FEATURE
from corpus.session import create_guest_session, initialize_guest_session


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


def test_composition_selects_workspace_and_sources_and_enters_the_lounge() -> None:
    compiled = compile_corpus_app()

    assert CORPUS_APP.features == (
        LOUNGE_FEATURE,
        WORKSPACE_FEATURE,
        AGENTS_FEATURE,
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
        "sources.home",
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


def test_lounge_and_workspace_own_their_operations_transitions_and_surfaces() -> None:
    contract = compile_corpus_app().frontend_contract

    assert set(contract.nodes["lounge.home"].operation_ids) == {
        "lounge.open_product_help",
        "lounge.arrival.open_sign_in",
        "lounge.arrival.open_registration",
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
    assert contract.nodes["sources.home"].surfaces.active == "sources.debug"
    assert set(contract.nodes["workspace.home"].operation_ids) == {
        "workspace.open_agents",
        "workspace.open_sources",
        "workspace.open_verification",
    }
    assert set(contract.nodes["sources.home"].operation_ids) == {
        "sources.return_to_home"
    }
    expected = {
        ("lounge.home", "lounge.open_product_help", "lounge.product_help"),
        ("lounge.home", "lounge.arrival.open_sign_in", "lounge.sign_in"),
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
        ("workspace.home", "workspace.open_verification", "lounge.verification_pending"),
        ("lounge.verification_pending", "lounge.verification_delivery.return_to_workspace", "workspace.home"),
        ("sources.home", "sources.return_to_home", "workspace.home"),
    }
    assert expected.issubset(
        {
            (transition.source, transition.operation_id, transition.target)
            for transition in contract.transitions
        }
    )


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
        "workspace.open_sources": surface_only,
        "workspace.open_agents": agent_and_surface,
        "workspace.open_verification": surface_only,
        "agents.open_create": agent_and_surface,
        "agents.return_to_workspace": agent_and_surface,
        "agents.create_agent": agent_and_surface,
        "agents.save_changes": agent_and_surface,
        "agents.cancel_create": agent_and_surface,
        "sources.return_to_home": surface_only,
    }

    assert set(compiled.operations) == set(expected)
    assert {
        operation_id: operation.allowed_sources
        for operation_id, operation in compiled.operations.items()
    } == expected


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
        workspace_service=object(),
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
        workspace_service=object(),
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
    initialized = await initialize_guest_session(
        None,  # type: ignore[arg-type]
        SessionSnapshot(state=session),
    )
    assert initialized.state is session
