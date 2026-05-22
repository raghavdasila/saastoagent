from types import SimpleNamespace

from backend.services.deployed_agents import (
    build_deployed_handoff_context,
    deployment_requires_login,
    deployment_policy_state,
)
from backend.services.deployed_agent_events import public_agent_message_event_payload
from backend.main import app


def test_inherited_deployment_access_allows_anonymous_for_no_auth_connections():
    deployment = SimpleNamespace(visitor_auth_mode="inherit_from_connection")
    connections = [SimpleNamespace(auth_type="none")]

    assert deployment_requires_login(deployment, connections) is False


def test_inherited_deployment_access_requires_login_for_credentialed_connections():
    deployment = SimpleNamespace(visitor_auth_mode="inherit_from_connection")
    connections = [SimpleNamespace(auth_type="none"), SimpleNamespace(auth_type="bearer")]

    assert deployment_requires_login(deployment, connections) is True


def test_explicit_deployment_access_policy_overrides_connection_auth():
    connections = [SimpleNamespace(auth_type="bearer")]

    assert deployment_requires_login(SimpleNamespace(visitor_auth_mode="anonymous"), connections) is False
    assert deployment_requires_login(SimpleNamespace(visitor_auth_mode="login_required"), []) is True


def test_deployed_chat_handoff_context_marks_public_channel_and_policy_snapshot():
    context = build_deployed_handoff_context(
        slug="storefront-agent",
        auth_required=False,
        visitor_auth_mode="inherit_from_connection",
        execution_mode="sandbox",
        default_write_policy="confirm",
    )

    assert context["channel"] == "deployed_web"
    assert context["deployment_slug"] == "storefront-agent"
    assert context["policy_snapshot"] == {
        "auth_required": False,
        "visitor_auth_mode": "inherit_from_connection",
        "execution_mode": "sandbox",
        "default_write_policy": "confirm",
        "policy_state": "allowed_read",
    }


def test_deployed_policy_states_are_explicit_for_public_contract():
    assert deployment_policy_state(enabled=False, auth_required=False) == "blocked"
    assert deployment_policy_state(enabled=True, auth_required=True) == "needs_visitor_auth"
    assert deployment_policy_state(enabled=True, auth_required=False) == "allowed_read"


def test_deployed_agent_public_routes_are_registered():
    paths = {route.path for route in app.routes}

    assert "/api/deployed-agents/{slug}" in paths
    assert "/api/deployed-agents/{slug}/chat" in paths
    assert "/api/deployed-agents/{slug}/sessions/{session_id}/events" in paths


def test_public_approval_event_payload_hides_internal_router_metadata():
    payload = public_agent_message_event_payload(
        message_id="message-1",
        session_id="session-1",
        content="The approved request ran successfully.",
        metadata={
            "approval_trace_id": "trace-1",
            "tool_name": "createProduct",
            "path": "/admin/products",
            "score": 5,
        },
    )

    assert payload == {
        "message_id": "message-1",
        "session_id": "session-1",
        "role": "assistant",
        "content": "The approved request ran successfully.",
    }


def test_owner_approval_routes_are_registered_on_builder_api():
    paths = {route.path for route in app.routes}

    assert "/api/saas-agents/{saas_agent_id}/approvals/pending" in paths
    assert "/api/saas-agents/{saas_agent_id}/approvals/{trace_id}/approve" in paths
    assert "/api/saas-agents/{saas_agent_id}/approvals/{trace_id}/cancel" in paths
