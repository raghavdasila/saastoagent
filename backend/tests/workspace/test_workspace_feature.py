from __future__ import annotations

import json
from pathlib import Path

import pytest
from routedeck_core.contracts.operations import DeliveryPhase
from routedeck_core.contracts.session import SessionSnapshot

from corpus.bindings import bind_corpus_app
from corpus.auth.service import OwnerRouteContext
from corpus.composition import CORPUS_APP, compile_corpus_app
from corpus.features.workspace.declarations import (
    OPEN_SOURCES,
    OPEN_REGISTRATION,
    OPEN_SIGN_IN,
    RETURN_TO_LOUNGE,
)
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

    assert CORPUS_APP.features == (WORKSPACE_FEATURE, SOURCES_FEATURE)
    assert compiled.frontend_contract.entry_node_id == "workspace.lounge"
    assert set(compiled.frontend_contract.nodes) == {
        "workspace.lounge",
        "workspace.sign_in",
        "workspace.register",
        "workspace.forgot_password",
        "workspace.reset_password",
        "workspace.verify_email",
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


def test_workspace_owns_navigation_operations_transitions_and_surfaces() -> None:
    contract = compile_corpus_app().frontend_contract

    assert set(contract.nodes["workspace.lounge"].operation_ids) == {
        "workspace.open_sign_in",
        "workspace.open_registration",
        "workspace.open_reset_password",
        "workspace.open_verify_email",
    }
    assert contract.nodes["workspace.lounge"].surfaces.active == "workspace.lounge"
    assert contract.nodes["workspace.sign_in"].surfaces.active == "workspace.sign_in"
    assert contract.nodes["workspace.register"].surfaces.active == "workspace.register"
    for node_id in (
        "workspace.sign_in",
        "workspace.register",
        "workspace.forgot_password",
        "workspace.reset_password",
        "workspace.verify_email",
    ):
        policy = contract.nodes[node_id].conversation_input
        assert policy.enabled is False
        assert policy.disabled_message == (
            "Chat is disabled while entering account credentials."
        )
    assert contract.nodes["workspace.home"].conversation_input.enabled is True
    assert contract.nodes["sources.home"].surfaces.active == "sources.debug"
    assert set(contract.nodes["workspace.home"].operation_ids) == {
        "workspace.open_sources"
    }
    assert set(contract.nodes["sources.home"].operation_ids) == {
        "sources.return_to_home"
    }
    expected = {
        ("workspace.lounge", "workspace.open_sign_in", "workspace.sign_in"),
        (
            "workspace.lounge",
            "workspace.open_registration",
            "workspace.register",
        ),
        ("workspace.sign_in", "workspace.return_to_lounge", "workspace.lounge"),
        ("workspace.register", "workspace.return_to_lounge", "workspace.lounge"),
        ("workspace.sign_in", "workspace.open_forgot_password", "workspace.forgot_password"),
        ("workspace.sign_in", "workspace.authentication_completed", "workspace.home"),
        ("workspace.register", "workspace.authentication_completed", "workspace.home"),
        ("workspace.lounge", "workspace.open_reset_password", "workspace.reset_password"),
        ("workspace.lounge", "workspace.open_verify_email", "workspace.verify_email"),
        ("workspace.forgot_password", "workspace.return_to_lounge", "workspace.lounge"),
        ("workspace.reset_password", "workspace.return_to_lounge", "workspace.lounge"),
        ("workspace.verify_email", "workspace.return_to_lounge", "workspace.lounge"),
        ("workspace.home", "workspace.open_sources", "sources.home"),
        ("sources.home", "sources.return_to_home", "workspace.home"),
    }
    assert expected.issubset(
        {
            (transition.source, transition.operation_id, transition.target)
            for transition in contract.transitions
        }
    )


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

    assert session.current.node_id == "workspace.lounge"
    assert session.private_state.configurations == ()
    assert session.public_state.status_code == "ready"
    initialized = await initialize_guest_session(
        None,  # type: ignore[arg-type]
        SessionSnapshot(state=session),
    )
    assert initialized.state is session
