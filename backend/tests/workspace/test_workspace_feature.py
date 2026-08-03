from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from routedeck_core.contracts.operations import DeliveryPhase, OperationSource
from routedeck_core.contracts.session import SessionSnapshot

from corpus.bindings import bind_corpus_app
from corpus.auth.credential_transition import AccountOperationRequest
from corpus.auth.service import OwnerRouteContext
from corpus.composition import CORPUS_APP, compile_corpus_app
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
from corpus.features.lounge.feature import LOUNGE_FEATURE
from corpus.features.workspace.declarations import OPEN_SOURCES
from corpus.features.workspace.feature import WORKSPACE_FEATURE
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

    assert CORPUS_APP.features == (LOUNGE_FEATURE, WORKSPACE_FEATURE, SOURCES_FEATURE)
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
        "lounge.arrival.open_reset_password",
        "lounge.arrival.open_verify_email",
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
        ("lounge.home", "lounge.arrival.open_reset_password", "lounge.reset_password"),
        ("lounge.home", "lounge.arrival.open_verify_email", "lounge.verify_email"),
        ("lounge.forgot_password", "lounge.request_password_reset.return_to_lounge", "lounge.home"),
        ("lounge.reset_password", "lounge.change_password.return_to_lounge", "lounge.home"),
        ("lounge.verify_email", "lounge.confirm_email.return_to_lounge", "lounge.home"),
        ("workspace.home", "workspace.open_sources", "sources.home"),
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
        "lounge.feature.current_product_truth",
        "lounge.feature.chrome_boundary",
        "lounge.feature.prompt",
        "lounge.feature.user_facing_language",
    }
    assert (
        compiled.agent_policies["lounge.feature.prompt"].instruction
        == "You are Corpus in the Lounge, the public starting point for people who are "
        "not signed in. Help visitors understand Corpus and choose their next step. "
        "Be concise, clear, and welcoming."
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
        auth_settings=object(),
        private_form_store=object(),
        private_form_codec=object(),
        credential_transition=credential_transition,
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
        assert handler.credential_transition is credential_transition

    for operation in (
        ARRIVAL_OPEN_SIGN_IN,
        ARRIVAL_OPEN_REGISTRATION,
        HELP_RETURN_TO_LOUNGE,
        OPEN_SOURCES,
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
        auth_settings=object(),
        private_form_store=object(),
        private_form_codec=object(),
        credential_transition=CredentialTransitionProbe(),
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
