from __future__ import annotations

import json
from pathlib import Path

import pytest
from routedeck_core.contracts.operations import DeliveryPhase
from routedeck_core.contracts.session import SessionSnapshot

from corpus.bindings import bind_corpus_app
from corpus.auth.service import OwnerRouteContext
from corpus.composition import CORPUS_APP, compile_corpus_app
from corpus.features.lounge.declarations import (
    OPEN_REGISTRATION,
    OPEN_SIGN_IN,
    RETURN_TO_LOUNGE,
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


def test_composition_selects_workspace_and_sources_and_enters_the_lounge() -> None:
    compiled = compile_corpus_app()

    assert CORPUS_APP.features == (LOUNGE_FEATURE, WORKSPACE_FEATURE, SOURCES_FEATURE)
    assert compiled.frontend_contract.entry_node_id == "lounge.home"
    assert set(compiled.frontend_contract.nodes) == {
        "lounge.home",
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
        "lounge.open_sign_in",
        "lounge.open_registration",
        "lounge.open_reset_password",
        "lounge.open_verify_email",
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
            "Chat is disabled while entering account credentials."
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
        ("lounge.home", "lounge.open_sign_in", "lounge.sign_in"),
        (
            "lounge.home",
            "lounge.open_registration",
            "lounge.register",
        ),
        ("lounge.sign_in", "lounge.return_to_lounge", "lounge.home"),
        ("lounge.register", "lounge.return_to_lounge", "lounge.home"),
        ("lounge.sign_in", "lounge.open_forgot_password", "lounge.forgot_password"),
        ("lounge.sign_in", "lounge.authentication_completed", "workspace.home"),
        ("lounge.register", "lounge.authentication_completed", "workspace.home"),
        ("lounge.home", "lounge.open_reset_password", "lounge.reset_password"),
        ("lounge.home", "lounge.open_verify_email", "lounge.verify_email"),
        ("lounge.forgot_password", "lounge.return_to_lounge", "lounge.home"),
        ("lounge.reset_password", "lounge.return_to_lounge", "lounge.home"),
        ("lounge.verify_email", "lounge.return_to_lounge", "lounge.home"),
        ("workspace.home", "workspace.open_sources", "sources.home"),
        ("workspace.home", "workspace.open_verification", "lounge.verification_pending"),
        ("lounge.verification_pending", "lounge.return_to_workspace", "workspace.home"),
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
    assert lounge.agent_prompt is not None
    assert "public Lounge" in lounge.agent_prompt

    assert {
        "lounge.public_context_only",
        "lounge.account_access_boundary",
        "lounge.current_product_truth",
        "lounge.arrival_boundary",
        "lounge.product_help_boundary",
        "lounge.credential_privacy",
        "lounge.authorization_boundary",
        "lounge.partial_account_success",
        "lounge.account_neutral_recovery",
        "lounge.one_time_reset_token",
        "lounge.verification_delivery",
        "lounge.one_time_verification_token",
        "lounge.verification_is_advisory",
    } == set(compiled.agent_policies)


@pytest.mark.asyncio
async def test_workspace_navigation_bindings_return_only_declared_outcomes() -> None:
    compiled = compile_corpus_app()
    bound = bind_corpus_app(compiled, OwnerContextProbe())

    for operation in (
        OPEN_SIGN_IN,
        OPEN_REGISTRATION,
        RETURN_TO_LOUNGE,
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
