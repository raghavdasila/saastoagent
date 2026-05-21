from types import SimpleNamespace

from backend.services.deployed_agents import (
    build_deployed_handoff_context,
    deployment_requires_login,
)
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
    }


def test_deployed_agent_public_routes_are_registered():
    paths = {route.path for route in app.routes}

    assert "/api/deployed-agents/{slug}" in paths
    assert "/api/deployed-agents/{slug}/chat" in paths
