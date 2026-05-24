import uuid
from types import SimpleNamespace

import pytest

from backend.services.agent import rest_operator
from backend.services.agent.api_orchestration import (
    classify_missing_inputs,
    derive_parent_collection_path,
    extract_resource_id_from_result,
    policy_allows_action_paths,
    policy_gap_payload,
    remember_dependency_id,
    resolve_dependency_id_from_frame,
)


class FakeDb:
    async def commit(self):
        return None


def _action(*, method: str = "POST", path: str = "/store/carts/{id}/line-items", parameters=None):
    return SimpleNamespace(
        id=uuid.uuid4(),
        name="action",
        method=method,
        path=path,
        parameters=parameters
        if parameters is not None
        else [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
    )


def _tool(*, name: str = "addLineItem", risk: str = "write", required=None):
    required = required if required is not None else ["id", "variant_id", "quantity"]
    return SimpleNamespace(
        id=uuid.uuid4(),
        name=name,
        risk_level=risk,
        requires_approval=False,
        function_schema={
            "parameters": {
                "type": "object",
                "properties": {item: {"type": "string"} for item in required},
                "required": required,
            }
        },
    )


def _candidate(
    *,
    method: str = "POST",
    path: str = "/store/carts/{id}/line-items",
    name: str = "addLineItem",
    risk: str = "write",
    required=None,
):
    return rest_operator.ToolCandidate(
        tool=_tool(name=name, risk=risk, required=required),
        action=_action(method=method, path=path),
        connection=SimpleNamespace(id=uuid.uuid4(), name="Store API"),
        score=10,
        reason="test",
    )


def test_missing_path_id_is_internal_for_public_orchestration():
    action = _action(path="/store/carts/{id}/line-items")

    classified = classify_missing_inputs(["id", "quantity"], action=action)

    assert [item.name for item in classified.internal] == ["id"]
    assert [item.name for item in classified.user_facing] == ["quantity"]
    assert "cart id" not in [item.public_label for item in classified.user_facing]


def test_natural_fields_remain_user_facing():
    action = _action(path="/api/projects/{id}/tasks")

    classified = classify_missing_inputs(["size", "quantity", "email"], action=action)

    assert [item.name for item in classified.internal] == []
    assert [item.public_label for item in classified.user_facing] == ["size", "quantity", "email"]


def test_parent_collection_is_derived_from_generic_openapi_path():
    assert derive_parent_collection_path("/api/projects/{id}/tasks", "id") == "/api/projects"
    assert derive_parent_collection_path("/store/carts/{cart_id}/line-items", "cart_id") == "/store/carts"


def test_dependency_id_can_be_reused_from_execution_frame():
    frame = {"kind": "result_context"}
    next_frame = remember_dependency_id(frame, "/store/carts", "cart_123")

    assert resolve_dependency_id_from_frame(next_frame, "/store/carts") == "cart_123"
    assert frame == {"kind": "result_context"}


def test_extract_created_resource_id_from_wrapped_api_result():
    result = {"status_code": 200, "body": {"cart": {"id": "cart_123", "items": []}}, "error": None}

    assert extract_resource_id_from_result(result) == "cart_123"


def test_policy_gap_payload_records_internal_dependency_write_paths():
    payload = policy_gap_payload(
        target_candidate=_candidate(path="/store/carts/{id}/line-items"),
        dependency_candidate=_candidate(path="/store/carts", name="createCart"),
        missing_internal_inputs=["id"],
        session_id=uuid.UUID("00000000-0000-0000-0000-000000000111"),
        trace_id=uuid.UUID("00000000-0000-0000-0000-000000000222"),
    )

    assert payload["trigger_type"] == "domain_policy_gap"
    assert payload["evidence"]["allowed_action_paths"] == ["/store/carts", "/store/carts/{id}/line-items"]
    assert payload["evidence"]["public_channel"] is True
    assert payload["evidence"]["missing_internal_inputs"] == ["id"]


def test_policy_allows_only_matching_generated_action_paths():
    candidate = SimpleNamespace(
        status="approved",
        trigger_type="domain_policy_gap",
        evidence={"allowed_action_paths": ["/store/carts", "/store/carts/{id}/line-items"]},
    )

    assert policy_allows_action_paths(candidate, ["/store/carts", "/store/carts/{id}/line-items"]) is True
    assert policy_allows_action_paths(candidate, ["/store/customers"]) is False


@pytest.mark.asyncio
async def test_public_internal_dependency_gap_creates_policy_candidate_without_exposing_cart_id(monkeypatch):
    saas_agent_id = uuid.uuid4()
    session_id = uuid.uuid4()
    trace_id = uuid.uuid4()
    target = _candidate(path="/store/carts/{id}/line-items", required=["id"])
    dependency = _candidate(path="/store/carts", name="createCart", required=[])
    proposed = {}

    async def fake_create_execution_trace(**kwargs):
        assert kwargs["status"] == "needs_input"
        assert kwargs["missing"] == ["id"]
        return SimpleNamespace(
            id=trace_id,
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            tool_name=target.tool.name,
            path=target.action.path,
            risk_level="write",
        )

    async def fake_find_dependency_candidate(*, saas_agent_id, db, parent_collection_path):
        assert parent_collection_path == "/store/carts"
        return dependency

    class FakeLearningService:
        async def approved_domain_policy(self, *, saas_agent_id, action_paths, db):
            return None

        async def propose_domain_policy_gap(self, **kwargs):
            proposed.update(kwargs)
            return SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr(rest_operator, "create_execution_trace", fake_create_execution_trace)
    monkeypatch.setattr(rest_operator, "find_dependency_candidate_for_path", fake_find_dependency_candidate)
    monkeypatch.setattr(rest_operator, "learning_service", FakeLearningService())

    async def emit(_event_name, _payload):
        return None

    content = await rest_operator._route_and_maybe_execute(
        message="add the L size to cart",
        candidates=[target],
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=None,
        session=SimpleNamespace(metadata_={}),
        db=FakeDb(),
        emit=emit,
        public_response=True,
    )

    assert "owner-approved" in content
    assert "cart id" not in content.lower()
    assert "id" not in content.lower()
    assert "/store" not in content
    assert proposed["dependency_candidate"] is dependency
    assert proposed["target_candidate"] is target


@pytest.mark.asyncio
async def test_approved_public_policy_executes_dependency_then_target(monkeypatch):
    saas_agent_id = uuid.uuid4()
    target = _candidate(path="/store/carts/{id}/line-items", required=["id"])
    dependency = _candidate(path="/store/carts", name="createCart", required=[])
    executed = []

    async def fake_create_execution_trace(**kwargs):
        return SimpleNamespace(id=uuid.uuid4(), inputs=kwargs["inputs"])

    async def fake_find_dependency_candidate(*, saas_agent_id, db, parent_collection_path):
        return dependency

    class FakeLearningService:
        async def approved_domain_policy(self, *, saas_agent_id, action_paths, db):
            return SimpleNamespace(id=uuid.uuid4())

        async def propose_domain_policy_gap(self, **kwargs):
            raise AssertionError("approved policy should not create a new policy gap")

    async def fake_execute_rest_tool(candidate, inputs, db):
        executed.append((candidate.action.path, dict(inputs)))
        if candidate is dependency:
            return {"status_code": 200, "body": {"cart": {"id": "cart_123"}}, "duration_ms": 1, "error": None}
        return {"status_code": 200, "body": {"cart": {"id": "cart_123", "items": [{"quantity": 1}]}}, "duration_ms": 2, "error": None}

    async def fake_finalize_execution_trace(trace, result, db):
        return None

    monkeypatch.setattr(rest_operator, "create_execution_trace", fake_create_execution_trace)
    monkeypatch.setattr(rest_operator, "find_dependency_candidate_for_path", fake_find_dependency_candidate)
    monkeypatch.setattr(rest_operator, "learning_service", FakeLearningService())
    monkeypatch.setattr(rest_operator, "execute_rest_tool", fake_execute_rest_tool)
    monkeypatch.setattr(rest_operator, "finalize_execution_trace", fake_finalize_execution_trace)

    async def emit(_event_name, _payload):
        return None

    content = await rest_operator._route_and_maybe_execute(
        message="add the L size to cart",
        candidates=[target],
        saas_agent_id=saas_agent_id,
        session_id=uuid.uuid4(),
        user_id=None,
        session=SimpleNamespace(metadata_={}),
        db=FakeDb(),
        emit=emit,
        public_response=True,
    )

    assert executed == [
        ("/store/carts", {}),
        ("/store/carts/{id}/line-items", {"id": "cart_123"}),
    ]
    assert "Done" in content
    assert "cart_123" not in content
