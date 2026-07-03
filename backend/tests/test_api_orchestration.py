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
)
from backend.services.agent.state_variables import (
    fill_inputs_from_pending_choice_variables,
    get_variable_value,
    pending_choice_prompt,
    pending_choice_target_path_for_message,
    remember_choice_variable,
    remember_resource_result_variables,
    remember_resource_id_variable,
    resolve_dependency_id_from_variables,
    resolve_input_from_variables,
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


def test_opaque_variant_id_is_internal_not_public_missing_field():
    action = _action(path="/store/carts/{id}/line-items")

    classified = classify_missing_inputs(["variant_id"], action=action)

    assert [item.name for item in classified.internal] == ["variant_id"]
    assert classified.user_facing == []


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
    next_frame = remember_resource_id_variable(frame, collection_path="/store/carts", resource_id="cart_123")

    assert resolve_dependency_id_from_variables(next_frame, "/store/carts") == "cart_123"
    assert frame == {"kind": "result_context"}


@pytest.mark.asyncio
async def test_public_generic_capability_greeting_does_not_route_rest_operator(monkeypatch):
    saas_agent_id = uuid.uuid4()
    session_id = uuid.uuid4()
    product_list = _candidate(method="GET", path="/store/products", name="listProducts", risk="read", required=[])

    async def fake_find_tool_candidates(*, message, saas_agent_id, db, limit=5):
        return [product_list]

    async def fake_route_and_maybe_execute(**kwargs):
        raise AssertionError("generic public greeting should stay in normal chat")

    monkeypatch.setattr(rest_operator, "find_tool_candidates", fake_find_tool_candidates)
    monkeypatch.setattr(rest_operator, "_route_and_maybe_execute", fake_route_and_maybe_execute)

    async def emit(_event_name, _payload):
        return None

    content = await rest_operator.run_rest_operator_turn(
        message="Hi, what can you help me with?",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=None,
        session=SimpleNamespace(metadata_={}),
        db=FakeDb(),
        emit=emit,
        public_response=True,
    )

    assert content is None


@pytest.mark.asyncio
async def test_public_product_catalog_question_still_routes_rest_operator(monkeypatch):
    saas_agent_id = uuid.uuid4()
    session_id = uuid.uuid4()
    product_list = _candidate(method="GET", path="/store/products", name="listProducts", risk="read", required=[])
    routed = {}

    async def fake_find_tool_candidates(*, message, saas_agent_id, db, limit=5):
        return [product_list]

    async def fake_route_and_maybe_execute(**kwargs):
        routed["message"] = kwargs["message"]
        routed["candidate_path"] = kwargs["candidates"][0].action.path
        return "Here are products."

    monkeypatch.setattr(rest_operator, "find_tool_candidates", fake_find_tool_candidates)
    monkeypatch.setattr(rest_operator, "_route_and_maybe_execute", fake_route_and_maybe_execute)

    async def emit(_event_name, _payload):
        return None

    content = await rest_operator.run_rest_operator_turn(
        message="What products do you have?",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=None,
        session=SimpleNamespace(metadata_={}),
        db=FakeDb(),
        emit=emit,
        public_response=True,
    )

    assert content == "Here are products."
    assert routed == {"message": "What products do you have?", "candidate_path": "/store/products"}


def test_dependency_result_stores_scalar_fields_for_later_internal_resolution():
    frame = {"kind": "result_context"}
    result = {
        "status_code": 200,
        "body": {
            "cart": {
                "id": "cart_123",
                "region_id": "region_123",
                "currency_code": "usd",
                "items": [{"id": "line_1"}],
                "shipping_address": {"city": "Austin"},
            }
        },
        "error": None,
    }

    next_frame = remember_resource_result_variables(frame, collection_path="/store/carts", result=result)

    assert resolve_dependency_id_from_variables(next_frame, "/store/carts") == "cart_123"
    assert get_variable_value(next_frame, "resource./store/carts.currency_code") == "usd"
    assert get_variable_value(next_frame, "resource./store/carts.id") == "cart_123"
    assert get_variable_value(next_frame, "resource./store/carts.region_id") == "region_123"
    assert get_variable_value(next_frame, "resource./store/carts.items") is None
    assert get_variable_value(next_frame, "resource./store/carts.shipping_address") is None
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
async def test_public_internal_gap_without_parent_still_creates_policy_candidate(monkeypatch):
    saas_agent_id = uuid.uuid4()
    session_id = uuid.uuid4()
    trace_id = uuid.uuid4()
    target = _candidate(path="/store/carts/{id}/line-items", required=["variant_id"])
    proposed = {}

    async def fake_create_execution_trace(**kwargs):
        assert kwargs["status"] == "needs_input"
        assert kwargs["missing"] == ["variant_id"]
        return SimpleNamespace(
            id=trace_id,
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            tool_name=target.tool.name,
            path=target.action.path,
            risk_level="write",
        )

    class FakeLearningService:
        async def approved_domain_policy(self, *, saas_agent_id, action_paths, db):
            raise AssertionError("no dependency parent should not look up policy first")

        async def propose_domain_policy_gap(self, **kwargs):
            proposed.update(kwargs)
            return SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr(rest_operator, "create_execution_trace", fake_create_execution_trace)
    monkeypatch.setattr(rest_operator, "learning_service", FakeLearningService())

    async def emit(_event_name, _payload):
        return None

    content = await rest_operator._route_and_maybe_execute(
        message="add this to cart",
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
    assert "variant_id" not in content
    assert proposed["dependency_candidate"] is None
    assert proposed["missing_internal_inputs"] == ["variant_id"]


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


@pytest.mark.asyncio
async def test_approved_public_policy_executes_prepared_financial_target(monkeypatch):
    saas_agent_id = uuid.uuid4()
    target = _candidate(
        path="/store/payment-collections/{id}/payment-sessions",
        name="createPaymentSession",
        risk="financial",
        required=["id", "provider_id"],
    )
    frame = remember_resource_id_variable(
        {"kind": "result_context"},
        collection_path="/store/payment-collections",
        resource_id="pay_col_123",
    )
    executed = {}

    async def fake_create_execution_trace(**kwargs):
        assert kwargs["inputs"] == {"id": "pay_col_123", "provider_id": "pp_system_default"}
        assert kwargs["missing"] == []
        assert kwargs["approval_state"] == "approved_by_policy"
        return SimpleNamespace(id=uuid.uuid4())

    class FakeLearningService:
        async def approved_domain_policy(self, *, saas_agent_id, action_paths, db):
            assert action_paths == ["/store/payment-collections/{id}/payment-sessions"]
            return SimpleNamespace(id=uuid.uuid4())

        async def propose_domain_policy_gap(self, **kwargs):
            raise AssertionError("approved target policy should not create a policy gap")

    async def fake_execute_rest_tool(candidate, inputs, db):
        executed.update(inputs)
        return {"status_code": 200, "body": {"payment_session": {"id": "pay_sess_123"}}, "duration_ms": 1, "error": None}

    async def fake_finalize_execution_trace(trace, result, db):
        return None

    monkeypatch.setattr(rest_operator, "create_execution_trace", fake_create_execution_trace)
    monkeypatch.setattr(rest_operator, "learning_service", FakeLearningService())
    monkeypatch.setattr(rest_operator, "execute_rest_tool", fake_execute_rest_tool)
    monkeypatch.setattr(rest_operator, "finalize_execution_trace", fake_finalize_execution_trace)

    async def emit(_event_name, _payload):
        return None

    content = await rest_operator._route_and_maybe_execute(
        message="Create a payment session for the current payment collection using provider_id=pp_system_default.",
        candidates=[target],
        saas_agent_id=saas_agent_id,
        session_id=uuid.uuid4(),
        user_id=None,
        session=SimpleNamespace(metadata_={"execution_frame_v1": frame}),
        db=FakeDb(),
        emit=emit,
        public_response=True,
        frame=frame,
    )

    assert executed == {"id": "pay_col_123", "provider_id": "pp_system_default"}
    assert "Done" in content
    assert "pay_col_123" not in content


@pytest.mark.asyncio
async def test_exact_order_lookup_bypasses_active_cart_frame(monkeypatch):
    saas_agent_id = uuid.uuid4()
    order_candidate = _candidate(
        method="GET",
        path="/store/orders/{id}",
        name="getOrder",
        risk="read",
        required=["id"],
    )
    frame = {
        "kind": "result_context",
        "active_resource": {
            "collection_path": "/store/carts",
            "id": "cart_123",
            "source_action_path": "/store/carts/{id}/complete",
            "reason": "checkout_completed",
        },
    }
    captured = {}

    async def fake_find_candidate_for_action_path(*, saas_agent_id, db, action_path, allowed_methods=None):
        assert action_path == "/store/orders/{id}"
        assert allowed_methods == {"GET"}
        return order_candidate

    async def fake_route_and_maybe_execute(**kwargs):
        captured.update(kwargs)
        return "Order #8 (order_123)"

    monkeypatch.setattr(rest_operator, "find_candidate_for_action_path", fake_find_candidate_for_action_path)
    monkeypatch.setattr(rest_operator, "_route_and_maybe_execute", fake_route_and_maybe_execute)

    async def emit(_event_name, _payload):
        return None

    content = await rest_operator._maybe_resume_execution_frame(
        message="Show order order_123.",
        saas_agent_id=saas_agent_id,
        session_id=uuid.uuid4(),
        user_id=None,
        session=SimpleNamespace(metadata_={"execution_frame_v1": frame}),
        db=FakeDb(),
        emit=emit,
        public_response=True,
    )

    assert content == "Order #8 (order_123)"
    assert captured["candidates"] == [order_candidate]
    assert captured["frame"] == frame


@pytest.mark.asyncio
async def test_active_order_read_uses_stored_order_id_without_user_repeating_id(monkeypatch):
    saas_agent_id = uuid.uuid4()
    order_candidate = _candidate(
        method="GET",
        path="/store/orders/{id}",
        name="getOrder",
        risk="read",
        required=["id"],
    )
    frame = remember_resource_id_variable(
        {"kind": "result_context"},
        collection_path="/store/orders",
        resource_id="order_123",
        origin={"source_action_path": "/store/carts/{id}/complete"},
    )
    frame["active_resource"] = {
        "collection_path": "/store/orders",
        "id": "order_123",
        "source_action_path": "/store/carts/{id}/complete",
        "reason": "workflow_result",
    }
    captured = {}

    async def fake_find_tool_candidates(*, message, saas_agent_id, db, limit=5):
        captured["routed_message"] = message
        return [
            _candidate(method="GET", path="/store/orders", name="listOrders", risk="read", required=[]),
            order_candidate,
        ]

    async def fake_create_execution_trace(**kwargs):
        captured["trace_inputs"] = dict(kwargs["inputs"])
        captured["trace_path"] = kwargs["candidate"].action.path
        return SimpleNamespace(id=uuid.uuid4(), inputs=kwargs["inputs"])

    async def fake_execute_rest_tool(candidate, inputs, db):
        captured["executed"] = (candidate.action.path, dict(inputs))
        return {
            "status_code": 200,
            "body": {"order": {"id": inputs["id"], "display_id": 8, "status": "placed"}},
            "duration_ms": 1,
            "error": None,
        }

    async def fake_finalize_execution_trace(trace, result, db):
        return None

    monkeypatch.setattr(rest_operator, "find_tool_candidates", fake_find_tool_candidates)
    monkeypatch.setattr(rest_operator, "create_execution_trace", fake_create_execution_trace)
    monkeypatch.setattr(rest_operator, "execute_rest_tool", fake_execute_rest_tool)
    monkeypatch.setattr(rest_operator, "finalize_execution_trace", fake_finalize_execution_trace)

    async def emit(_event_name, _payload):
        return None

    content = await rest_operator._maybe_resume_execution_frame(
        message="Can you show my order?",
        saas_agent_id=saas_agent_id,
        session_id=uuid.uuid4(),
        user_id=None,
        session=SimpleNamespace(metadata_={"execution_frame_v1": frame}),
        db=FakeDb(),
        emit=emit,
        public_response=True,
    )

    assert captured["trace_path"] == "/store/orders/{id}"
    assert captured["trace_inputs"] == {"id": "order_123"}
    assert captured["executed"] == ("/store/orders/{id}", {"id": "order_123"})
    assert "Order #8" in content


@pytest.mark.asyncio
async def test_workflow_continuation_uses_active_resource_and_creates_policy_gap(monkeypatch):
    saas_agent_id = uuid.uuid4()
    session_id = uuid.uuid4()
    trace_id = uuid.uuid4()
    frame = {
        "kind": "result_context",
        "selected_entity": {
            "entity_type": "items",
            "id": "item_1",
            "label": "Starter Plan",
            "aliases": ["starter plan"],
            "raw": {"id": "item_1", "name": "Starter Plan"},
        },
        "active_resource": {
            "collection_path": "/api/accounts",
            "id": "acct_1",
            "source_action_path": "/api/accounts/{id}/subscriptions",
            "reason": "internal_dependency_used_successfully",
        },
    }
    frame = remember_resource_id_variable(frame, collection_path="/api/accounts", resource_id="acct_1")
    session = SimpleNamespace(metadata_={"execution_frame_v1": frame})
    complete = _candidate(path="/api/accounts/{id}/complete", name="completeAccount", required=["id"])
    add_item = _candidate(path="/api/accounts/{id}/items", name="addItem", required=["id", "item_id"])
    proposed = {}

    async def fake_find_tool_candidates(*, message, saas_agent_id, db, limit=5):
        assert "Active resource collection /api/accounts" in message
        assert "Starter Plan" not in message
        return [add_item, complete]

    async def fake_create_execution_trace(**kwargs):
        assert kwargs["candidate"].action.path == complete.action.path
        assert kwargs["inputs"] == {"id": "acct_1"}
        assert kwargs["missing"] == ["id"]
        return SimpleNamespace(
            id=trace_id,
            saas_agent_id=saas_agent_id,
            session_id=session_id,
            tool_name=complete.tool.name,
            path=complete.action.path,
            risk_level="write",
        )

    class FakeLearningService:
        async def approved_domain_policy(self, *, saas_agent_id, action_paths, db):
            assert action_paths == ["/api/accounts/{id}/complete"]
            return None

        async def propose_domain_policy_gap(self, **kwargs):
            proposed.update(kwargs)
            return SimpleNamespace(id=uuid.uuid4())

    monkeypatch.setattr(rest_operator, "find_tool_candidates", fake_find_tool_candidates)
    monkeypatch.setattr(rest_operator, "create_execution_trace", fake_create_execution_trace)
    monkeypatch.setattr(rest_operator, "learning_service", FakeLearningService())

    async def emit(_event_name, _payload):
        return None

    content = await rest_operator.run_rest_operator_turn(
        message="checkout",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=None,
        session=session,
        db=FakeDb(),
        emit=emit,
        public_response=True,
    )

    assert "owner-approved" in content
    assert "acct_1" not in content
    assert proposed["target_candidate"].action.path == complete.action.path
    assert proposed["dependency_candidate"] is None


def test_checkout_workflow_rerank_prefers_completion_action_over_other_resource_actions():
    frame = {
        "kind": "result_context",
        "active_resource": {
            "collection_path": "/api/accounts",
            "id": "acct_1",
            "source_action_path": "/api/accounts/{id}/items",
            "reason": "internal_dependency_used_successfully",
        },
    }
    taxes = _candidate(path="/api/accounts/{id}/taxes", name="calculateTaxes", required=["id"])
    details = _candidate(method="GET", path="/api/accounts/{id}", name="getAccount", risk="read", required=["id"])
    details.score = 40
    complete = _candidate(path="/api/accounts/{id}/complete", name="completeAccount", required=["id"])

    ranked = rest_operator._rerank_candidates_for_frame(
        message="checkout",
        candidates=[taxes, details, complete],
        frame=frame,
    )

    assert ranked[0].action.path == complete.action.path
    assert ranked[0].score > ranked[1].score
    assert ranked[0].score > next(row.score for row in ranked if row.action.path == details.action.path)


@pytest.mark.asyncio
async def test_read_refinement_uses_last_result_collection_context(monkeypatch):
    saas_agent_id = uuid.uuid4()
    session_id = uuid.uuid4()
    frame = {
        "kind": "result_context",
        "source": {
            "tool_name": "getproducts",
            "action_name": "GetProducts",
            "method": "GET",
            "path": "/store/products",
        },
        "entities": [
            {
                "entity_type": "products",
                "id": "prod_1",
                "label": "Medusa Sweatshirt",
                "aliases": ["medusa sweatshirt", "sweatshirt"],
                "raw": {"id": "prod_1", "title": "Medusa Sweatshirt"},
            }
        ],
        "last_user_message": "search for sweatshirt",
    }
    session = SimpleNamespace(metadata_={"execution_frame_v1": frame})

    def read_candidate(name: str, path: str):
        action = SimpleNamespace(
            id=uuid.uuid4(),
            name=name,
            method="GET",
            path=path,
            description=f"Retrieve a list from {path}.",
            parameters=[
                {"name": "q", "in": "query", "required": False, "schema": {"type": "string"}},
                {"name": "limit", "in": "query", "required": False, "schema": {"type": "integer"}},
            ],
        )
        tool = SimpleNamespace(
            id=uuid.uuid4(),
            name=name.lower(),
            risk_level="read",
            requires_approval=False,
            function_schema={
                "parameters": {
                    "type": "object",
                    "properties": {"q": {"type": "string"}, "limit": {"type": "integer"}},
                    "required": [],
                }
            },
        )
        return rest_operator.ToolCandidate(
            tool=tool,
            action=action,
            connection=SimpleNamespace(id=uuid.uuid4(), name="Store API"),
            score=53,
            reason="fusion",
        )

    collections = read_candidate("GetCollections", "/store/collections")
    products = read_candidate("GetProducts", "/store/products")
    executed = {}
    calls = []

    async def fake_find_tool_candidates(*, message, saas_agent_id, db, limit=5):
        calls.append((message, limit))
        return [collections, products]

    async def fake_create_execution_trace(**kwargs):
        assert kwargs["candidate"].action.path == "/store/products"
        assert kwargs["inputs"] == {"q": "shorts", "limit": 5}
        assert kwargs["status"] == "executing"
        return SimpleNamespace(id=uuid.uuid4())

    async def fake_execute_rest_tool(candidate, inputs, db):
        executed.update({"path": candidate.action.path, "inputs": dict(inputs)})
        return {
            "status_code": 200,
            "body": {"products": [{"id": "prod_2", "title": "Medusa Shorts"}]},
            "duration_ms": 1,
            "error": None,
        }

    async def fake_finalize_execution_trace(trace, result, db):
        return None

    monkeypatch.setattr(rest_operator, "find_tool_candidates", fake_find_tool_candidates)
    monkeypatch.setattr(rest_operator, "create_execution_trace", fake_create_execution_trace)
    monkeypatch.setattr(rest_operator, "execute_rest_tool", fake_execute_rest_tool)
    monkeypatch.setattr(rest_operator, "finalize_execution_trace", fake_finalize_execution_trace)

    async def emit(_event_name, _payload):
        return None

    content = await rest_operator.run_rest_operator_turn(
        message="filter for shorts",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=None,
        session=session,
        db=FakeDb(),
        emit=emit,
        public_response=True,
    )

    assert calls and calls[0][1] == 50
    assert executed == {"path": "/store/products", "inputs": {"q": "shorts", "limit": 5}}
    assert "Medusa Shorts" in content


def test_recovery_rerank_prefers_existing_dependency_child_over_recreating_collection():
    frame = remember_resource_id_variable(
        {
        "kind": "result_context",
        "active_resource": {
            "collection_path": "/api/accounts",
            "id": "acct_1",
            "source_action_path": "/api/accounts/{id}/items",
            "reason": "internal_dependency_used_successfully",
        },
        },
        collection_path="/api/accounts",
        resource_id="acct_1",
    )
    frame = remember_resource_id_variable(frame, collection_path="/api/billing-batches", resource_id="batch_1")
    recreate_batch = _candidate(path="/api/billing-batches", name="createBillingBatch", required=["account_id"])
    recreate_batch.score = 80
    create_session = _candidate(
        path="/api/billing-batches/{id}/settlement-sessions",
        name="createSettlementSession",
        required=["id", "provider_id"],
    )
    create_session.score = 20

    ranked = rest_operator._rerank_recovery_candidates(
        message="checkout",
        error_detail="Settlement sessions are required to complete account",
        candidates=[recreate_batch, create_session],
        frame=frame,
    )

    assert ranked[0].action.path == "/api/billing-batches/{id}/settlement-sessions"
    assert ranked[0].score > next(row.score for row in ranked if row.action.path == "/api/billing-batches")


def test_pending_choice_reply_fills_internal_option_without_exposing_id():
    frame = remember_choice_variable(
        {"kind": "result_context"},
        input_name="option_id",
        target_action_path="/api/accounts/{id}/options",
        items=[
            {"id": "opt_fast", "label": "Fast Delivery"},
            {"id": "opt_slow", "label": "Slow Delivery"},
        ],
    )

    inputs, missing = fill_inputs_from_pending_choice_variables(
        message="use fast delivery",
        inputs={"id": "acct_1"},
        missing=["option_id"],
        frame=frame,
    )
    prompt = pending_choice_prompt(frame, ["option_id"])
    target_path = pending_choice_target_path_for_message(frame, "use fast delivery")

    assert inputs == {"id": "acct_1", "option_id": "opt_fast"}
    assert missing == []
    assert target_path == "/api/accounts/{id}/options"
    assert "Fast Delivery" in prompt
    assert "Slow Delivery" in prompt
    assert "opt_fast" not in prompt
    assert "option_id" not in prompt


@pytest.mark.asyncio
async def test_approved_workflow_policy_executes_active_resource_action(monkeypatch):
    saas_agent_id = uuid.uuid4()
    session_id = uuid.uuid4()
    frame = {
        "kind": "result_context",
        "active_resource": {
            "collection_path": "/api/accounts",
            "id": "acct_1",
            "source_action_path": "/api/accounts/{id}/items",
            "reason": "internal_dependency_used_successfully",
        },
    }
    session = SimpleNamespace(metadata_={"execution_frame_v1": frame})
    complete = _candidate(path="/api/accounts/{id}/complete", name="completeAccount", required=["id"])
    executed = {}

    async def fake_find_tool_candidates(*, message, saas_agent_id, db, limit=5):
        return [complete]

    async def fake_create_execution_trace(**kwargs):
        assert kwargs["inputs"] == {"id": "acct_1"}
        assert kwargs["missing"] == []
        assert kwargs["approval_state"] == "approved_by_policy"
        return SimpleNamespace(id=uuid.uuid4())

    class FakeLearningService:
        async def approved_domain_policy(self, *, saas_agent_id, action_paths, db):
            assert action_paths == ["/api/accounts/{id}/complete"]
            return SimpleNamespace(id=uuid.uuid4())

        async def propose_domain_policy_gap(self, **kwargs):
            raise AssertionError("approved workflow policy should not create a policy gap")

    async def fake_execute_rest_tool(candidate, inputs, db):
        executed.update(inputs)
        return {"status_code": 200, "body": {"ok": True}, "duration_ms": 1, "error": None}

    async def fake_finalize_execution_trace(trace, result, db):
        return None

    monkeypatch.setattr(rest_operator, "find_tool_candidates", fake_find_tool_candidates)
    monkeypatch.setattr(rest_operator, "create_execution_trace", fake_create_execution_trace)
    monkeypatch.setattr(rest_operator, "learning_service", FakeLearningService())
    monkeypatch.setattr(rest_operator, "execute_rest_tool", fake_execute_rest_tool)
    monkeypatch.setattr(rest_operator, "finalize_execution_trace", fake_finalize_execution_trace)

    async def emit(_event_name, _payload):
        return None

    content = await rest_operator.run_rest_operator_turn(
        message="checkout",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=None,
        session=session,
        db=FakeDb(),
        emit=emit,
        public_response=True,
    )

    assert executed == {"id": "acct_1"}
    assert "Done" in content
    assert "acct_1" not in content


@pytest.mark.asyncio
async def test_successful_active_resource_write_refreshes_frame_fields(monkeypatch):
    saas_agent_id = uuid.uuid4()
    session_id = uuid.uuid4()
    frame = {
        "kind": "result_context",
        "active_resource": {
            "collection_path": "/api/accounts",
            "id": "acct_1",
            "source_action_path": "/api/accounts/{id}/items",
            "reason": "internal_dependency_used_successfully",
        },
    }
    frame = remember_resource_id_variable(frame, collection_path="/api/accounts", resource_id="acct_1")
    session = SimpleNamespace(metadata_={"execution_frame_v1": frame})
    complete = _candidate(path="/api/accounts/{id}/complete", name="completeAccount", required=["id"])

    async def fake_find_tool_candidates(*, message, saas_agent_id, db, limit=5):
        return [complete]

    async def fake_create_execution_trace(**kwargs):
        return SimpleNamespace(id=uuid.uuid4())

    class FakeLearningService:
        async def approved_domain_policy(self, *, saas_agent_id, action_paths, db):
            return SimpleNamespace(id=uuid.uuid4())

        async def propose_domain_policy_gap(self, **kwargs):
            raise AssertionError("approved workflow policy should not create a policy gap")

    async def fake_execute_rest_tool(candidate, inputs, db):
        return {
            "status_code": 200,
            "body": {
                "account": {
                    "id": "acct_1",
                    "region_id": "region_1",
                    "currency_code": "usd",
                    "items": [{"id": "item_1"}],
                }
            },
            "duration_ms": 1,
            "error": None,
        }

    async def fake_finalize_execution_trace(trace, result, db):
        return None

    monkeypatch.setattr(rest_operator, "find_tool_candidates", fake_find_tool_candidates)
    monkeypatch.setattr(rest_operator, "create_execution_trace", fake_create_execution_trace)
    monkeypatch.setattr(rest_operator, "learning_service", FakeLearningService())
    monkeypatch.setattr(rest_operator, "execute_rest_tool", fake_execute_rest_tool)
    monkeypatch.setattr(rest_operator, "finalize_execution_trace", fake_finalize_execution_trace)

    async def emit(_event_name, _payload):
        return None

    await rest_operator.run_rest_operator_turn(
        message="checkout",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=None,
        session=session,
        db=FakeDb(),
        emit=emit,
        public_response=True,
    )

    variables = session.metadata_["execution_frame_v1"]["variables"]
    assert variables["resource./api/accounts.id"]["value"] == "acct_1"
    assert variables["resource./api/accounts.region_id"]["value"] == "region_1"
    assert variables["resource./api/accounts.currency_code"]["value"] == "usd"
    assert "resource./api/accounts.items" not in variables


def test_purchase_intent_populates_generic_search_query():
    action = SimpleNamespace(parameters=[])
    tool = SimpleNamespace(
        function_schema={
            "parameters": {
                "type": "object",
                "properties": {"q": {"type": "string"}},
                "required": [],
            }
        }
    )

    inputs, missing = rest_operator._build_inputs("i want to buy Graph Notebook", action, tool)

    assert inputs == {"q": "Graph Notebook"}
    assert missing == []


def test_input_resolution_reads_variable_store():
    frame = {
        "kind": "result_context",
        "active_resource_ref": "resource./api/accounts.id",
        "variables": {
            "resource./api/accounts.id": {
                "name": "resource./api/accounts.id",
                "value": "acct_1",
                "aliases": ["id", "account_id"],
                "resource": {"collection_path": "/api/accounts", "resource_id": "acct_1"},
            },
            "resource./api/accounts.region_id": {
                "name": "resource./api/accounts.region_id",
                "value": "region_1",
                "aliases": ["region_id"],
                "resource": {"collection_path": "/api/accounts", "resource_id": "acct_1"},
            },
        },
    }

    assert resolve_input_from_variables(frame, "region_id", action=SimpleNamespace(path="")) == "region_1"


@pytest.mark.asyncio
async def test_public_execution_failure_creates_policy_gap_for_recovery_action(monkeypatch):
    saas_agent_id = uuid.uuid4()
    session_id = uuid.uuid4()
    frame = {
        "kind": "result_context",
        "active_resource": {
            "collection_path": "/api/accounts",
            "id": "acct_1",
            "source_action_path": "/api/accounts/{id}/items",
            "reason": "internal_dependency_used_successfully",
        },
    }
    session = SimpleNamespace(metadata_={"execution_frame_v1": frame})
    complete = _candidate(path="/api/accounts/{id}/complete", name="completeAccount", required=["id"])
    create_invoice = _candidate(path="/api/invoices", name="createInvoice", required=["account_id"])
    read_account = _candidate(method="GET", path="/api/accounts/{id}", name="readAccount", risk="read", required=["id"])
    update_account = _candidate(path="/api/accounts/{id}", name="updateAccount", required=["id"])
    update_account.score = 40
    proposed = {}

    async def fake_find_tool_candidates(*, message, saas_agent_id, db, limit=5):
        if "invoice has not been initiated" not in message.lower():
            return [complete]
        assert "Active resource collection /api/accounts" in message
        return [read_account, update_account, create_invoice]

    async def fake_create_execution_trace(**kwargs):
        return SimpleNamespace(
            id=uuid.uuid4(),
            saas_agent_id=kwargs["saas_agent_id"],
            session_id=kwargs["session_id"],
            tool_name=kwargs["candidate"].tool.name,
            path=kwargs["candidate"].action.path,
            risk_level="write",
        )

    class FakeLearningService:
        async def approved_domain_policy(self, *, saas_agent_id, action_paths, db):
            if action_paths == ["/api/accounts/{id}/complete"]:
                return SimpleNamespace(id=uuid.uuid4())
            assert action_paths == ["/api/invoices"]
            return None

        async def propose_domain_policy_gap(self, **kwargs):
            proposed.update(kwargs)
            return SimpleNamespace(id=uuid.uuid4())

    async def fake_execute_rest_tool(candidate, inputs, db):
        assert candidate.action.path == complete.action.path
        assert inputs == {"id": "acct_1"}
        return {
            "status_code": 400,
            "body": {"message": "Invoice has not been initiated for account", "type": "invalid_data"},
            "duration_ms": 1,
            "error": "HTTP 400",
        }

    async def fake_finalize_execution_trace(trace, result, db):
        return None

    monkeypatch.setattr(rest_operator, "find_tool_candidates", fake_find_tool_candidates)
    monkeypatch.setattr(rest_operator, "create_execution_trace", fake_create_execution_trace)
    monkeypatch.setattr(rest_operator, "learning_service", FakeLearningService())
    monkeypatch.setattr(rest_operator, "execute_rest_tool", fake_execute_rest_tool)
    monkeypatch.setattr(rest_operator, "finalize_execution_trace", fake_finalize_execution_trace)

    async def emit(_event_name, _payload):
        return None

    content = await rest_operator.run_rest_operator_turn(
        message="checkout",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=None,
        session=session,
        db=FakeDb(),
        emit=emit,
        public_response=True,
    )

    assert "owner-approved" in content
    assert "acct_1" not in content
    assert "/api" not in content
    assert proposed["target_candidate"].action.path == create_invoice.action.path
    assert proposed["dependency_candidate"] is None
    assert proposed["missing_internal_inputs"] == ["account_id"]


@pytest.mark.asyncio
async def test_public_failure_recovery_can_chain_to_next_policy_gap(monkeypatch):
    saas_agent_id = uuid.uuid4()
    session_id = uuid.uuid4()
    frame = {
        "kind": "result_context",
        "active_resource": {
            "collection_path": "/api/accounts",
            "id": "acct_1",
            "source_action_path": "/api/accounts/{id}/items",
            "reason": "internal_dependency_used_successfully",
        },
    }
    session = SimpleNamespace(metadata_={"execution_frame_v1": frame})
    complete = _candidate(path="/api/accounts/{id}/complete", name="completeAccount", required=["id"])
    create_invoice = _candidate(path="/api/invoices", name="createInvoice", required=["account_id"])
    create_invoice_session = _candidate(path="/api/invoices/{id}/sessions", name="createInvoiceSession", required=["id"])
    proposed = {}
    complete_attempts = 0

    async def fake_find_tool_candidates(*, message, saas_agent_id, db, limit=5):
        lowered = message.lower()
        if "settlement sessions are required" in lowered:
            return [create_invoice_session]
        if "invoice has not been initiated" in lowered:
            return [create_invoice]
        return [complete]

    async def fake_create_execution_trace(**kwargs):
        return SimpleNamespace(
            id=uuid.uuid4(),
            saas_agent_id=kwargs["saas_agent_id"],
            session_id=kwargs["session_id"],
            tool_name=kwargs["candidate"].tool.name,
            path=kwargs["candidate"].action.path,
            risk_level="write",
            inputs=kwargs["inputs"],
            missing_inputs=kwargs["missing"],
            status=kwargs["status"],
            approval_state=kwargs["approval_state"],
            route_node=kwargs["route_node"],
        )

    class FakeLearningService:
        async def approved_domain_policy(self, *, saas_agent_id, action_paths, db):
            if action_paths in (["/api/accounts/{id}/complete"], ["/api/invoices"]):
                return SimpleNamespace(id=uuid.uuid4())
            assert action_paths == ["/api/invoices/{id}/sessions"]
            return None

        async def propose_domain_policy_gap(self, **kwargs):
            proposed.update(kwargs)
            return SimpleNamespace(id=uuid.uuid4())

    async def fake_execute_rest_tool(candidate, inputs, db):
        nonlocal complete_attempts
        if candidate.action.path == complete.action.path:
            complete_attempts += 1
            assert inputs == {"id": "acct_1"}
            if complete_attempts == 1:
                return {
                    "status_code": 400,
                    "body": {"message": "Invoice has not been initiated for account"},
                    "duration_ms": 1,
                    "error": "HTTP 400",
                }
            return {
                "status_code": 400,
                "body": {"message": "Settlement sessions are required to complete account"},
                "duration_ms": 1,
                "error": "HTTP 400",
            }
        assert candidate.action.path == create_invoice.action.path
        assert inputs == {"account_id": "acct_1"}
        return {"status_code": 200, "body": {"invoice": {"id": "inv_1"}}, "duration_ms": 1, "error": None}

    async def fake_finalize_execution_trace(trace, result, db):
        return None

    monkeypatch.setattr(rest_operator, "find_tool_candidates", fake_find_tool_candidates)
    monkeypatch.setattr(rest_operator, "create_execution_trace", fake_create_execution_trace)
    monkeypatch.setattr(rest_operator, "learning_service", FakeLearningService())
    monkeypatch.setattr(rest_operator, "execute_rest_tool", fake_execute_rest_tool)
    monkeypatch.setattr(rest_operator, "finalize_execution_trace", fake_finalize_execution_trace)

    async def emit(_event_name, _payload):
        return None

    content = await rest_operator.run_rest_operator_turn(
        message="checkout",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=None,
        session=session,
        db=FakeDb(),
        emit=emit,
        public_response=True,
    )

    assert "owner-approved" in content
    assert complete_attempts == 2
    assert proposed["target_candidate"].action.path == create_invoice_session.action.path
    assert proposed["dependency_candidate"] is None
    assert proposed["missing_internal_inputs"] == ["id"]


@pytest.mark.asyncio
async def test_recovery_resolves_provider_id_from_generated_read_action(monkeypatch):
    saas_agent_id = uuid.uuid4()
    session_id = uuid.uuid4()
    frame = remember_resource_result_variables(
        {
        "kind": "result_context",
        "active_resource": {
            "collection_path": "/api/accounts",
            "id": "acct_1",
            "source_action_path": "/api/accounts/{id}/items",
            "reason": "internal_dependency_used_successfully",
        },
        },
        collection_path="/api/accounts",
        result={"body": {"account": {"id": "acct_1", "region_id": "region_1"}}, "error": None},
    )
    frame = remember_resource_id_variable(frame, collection_path="/api/payment-collections", resource_id="paycol_1")
    session = SimpleNamespace(metadata_={"execution_frame_v1": frame})
    complete = _candidate(path="/api/accounts/{id}/complete", name="completeAccount", required=["id"])
    create_session = _candidate(
        path="/api/payment-collections/{id}/payment-sessions",
        name="createPaymentSession",
        required=["id", "provider_id"],
    )
    list_providers = _candidate(
        method="GET",
        path="/api/payment-providers",
        name="listPaymentProviders",
        risk="read",
        required=["region_id"],
    )
    executed = []

    async def fake_find_tool_candidates(*, message, saas_agent_id, db, limit=5):
        lowered = message.lower()
        if "payment sessions are required" in lowered:
            return [create_session]
        if "provider_id" in lowered or "provider id" in lowered:
            return [list_providers]
        return [complete]

    async def fake_create_execution_trace(**kwargs):
        return SimpleNamespace(
            id=uuid.uuid4(),
            saas_agent_id=kwargs["saas_agent_id"],
            session_id=kwargs["session_id"],
            tool_name=kwargs["candidate"].tool.name,
            path=kwargs["candidate"].action.path,
            risk_level="write",
            inputs=kwargs["inputs"],
        )

    class FakeLearningService:
        async def approved_domain_policy(self, *, saas_agent_id, action_paths, db):
            assert action_paths in (["/api/accounts/{id}/complete"], ["/api/payment-collections/{id}/payment-sessions"])
            return SimpleNamespace(id=uuid.uuid4())

        async def propose_domain_policy_gap(self, **kwargs):
            raise AssertionError("approved recovery policy should not create a policy gap")

    async def fake_execute_rest_tool(candidate, inputs, db):
        executed.append((candidate.action.path, dict(inputs)))
        if candidate.action.path == complete.action.path:
            return {
                "status_code": 400,
                "body": {"message": "Payment sessions are required to complete account"},
                "duration_ms": 1,
                "error": "HTTP 400",
            }
        if candidate.action.path == list_providers.action.path:
            assert inputs == {"region_id": "region_1"}
            return {
                "status_code": 200,
                "body": {"payment_providers": [{"id": "provider_1", "name": "Default provider"}]},
                "duration_ms": 1,
                "error": None,
            }
        assert candidate.action.path == create_session.action.path
        assert inputs == {"id": "paycol_1", "provider_id": "provider_1"}
        return {
            "status_code": 200,
            "body": {"payment_session": {"id": "session_1"}},
            "duration_ms": 1,
            "error": None,
        }

    async def fake_finalize_execution_trace(trace, result, db):
        return None

    monkeypatch.setattr(rest_operator, "find_tool_candidates", fake_find_tool_candidates)
    monkeypatch.setattr(rest_operator, "create_execution_trace", fake_create_execution_trace)
    monkeypatch.setattr(rest_operator, "learning_service", FakeLearningService())
    monkeypatch.setattr(rest_operator, "execute_rest_tool", fake_execute_rest_tool)
    monkeypatch.setattr(rest_operator, "finalize_execution_trace", fake_finalize_execution_trace)

    async def emit(_event_name, _payload):
        return None

    content = await rest_operator.run_rest_operator_turn(
        message="checkout",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=None,
        session=session,
        db=FakeDb(),
        emit=emit,
        public_response=True,
    )

    assert executed == [
        ("/api/accounts/{id}/complete", {"id": "acct_1"}),
        ("/api/payment-providers", {"region_id": "region_1"}),
        ("/api/payment-collections/{id}/payment-sessions", {"id": "paycol_1", "provider_id": "provider_1"}),
        ("/api/accounts/{id}/complete", {"id": "acct_1"}),
    ]
    assert "connected API returned an error" in content
    assert "provider_1" not in content


@pytest.mark.asyncio
async def test_recovery_uses_lexical_read_resolver_when_fusion_misses_provider(monkeypatch):
    saas_agent_id = uuid.uuid4()
    session_id = uuid.uuid4()
    frame = remember_resource_result_variables(
        {
        "kind": "result_context",
        "active_resource": {
            "collection_path": "/api/accounts",
            "id": "acct_1",
            "source_action_path": "/api/accounts/{id}/items",
            "reason": "internal_dependency_used_successfully",
        },
        },
        collection_path="/api/accounts",
        result={"body": {"account": {"id": "acct_1", "region_id": "region_1"}}, "error": None},
    )
    frame = remember_resource_id_variable(frame, collection_path="/api/payment-collections", resource_id="paycol_1")
    session = SimpleNamespace(metadata_={"execution_frame_v1": frame})
    complete = _candidate(path="/api/accounts/{id}/complete", name="completeAccount", required=["id"])
    create_session = _candidate(
        path="/api/payment-collections/{id}/payment-sessions",
        name="createPaymentSession",
        required=["id", "provider_id"],
    )
    wrong_read = _candidate(method="GET", path="/api/products", name="listProducts", risk="read", required=[])
    list_providers = _candidate(
        method="GET",
        path="/api/payment-providers",
        name="listPaymentProviders",
        risk="read",
        required=["region_id"],
    )
    executed = []

    async def fake_find_tool_candidates(*, message, saas_agent_id, db, limit=5):
        lowered = message.lower()
        if "payment sessions are required" in lowered:
            return [create_session]
        if "provider_id" in lowered or "provider id" in lowered:
            return [wrong_read]
        return [complete]

    async def fake_find_read_resolver_candidates_by_noun(*, input_name, noun, saas_agent_id, db, limit=50):
        assert input_name == "provider_id"
        assert noun == "provider"
        return [list_providers]

    async def fake_create_execution_trace(**kwargs):
        return SimpleNamespace(
            id=uuid.uuid4(),
            saas_agent_id=kwargs["saas_agent_id"],
            session_id=kwargs["session_id"],
            tool_name=kwargs["candidate"].tool.name,
            path=kwargs["candidate"].action.path,
            risk_level="write",
            inputs=kwargs["inputs"],
        )

    class FakeLearningService:
        async def approved_domain_policy(self, *, saas_agent_id, action_paths, db):
            assert action_paths in (["/api/accounts/{id}/complete"], ["/api/payment-collections/{id}/payment-sessions"])
            return SimpleNamespace(id=uuid.uuid4())

        async def propose_domain_policy_gap(self, **kwargs):
            raise AssertionError("approved recovery policy should not create a policy gap")

    async def fake_execute_rest_tool(candidate, inputs, db):
        executed.append((candidate.action.path, dict(inputs)))
        if candidate.action.path == complete.action.path:
            return {
                "status_code": 400,
                "body": {"message": "Payment sessions are required to complete account"},
                "duration_ms": 1,
                "error": "HTTP 400",
            }
        if candidate.action.path == wrong_read.action.path:
            return {"status_code": 200, "body": {"products": [{"id": "prod_wrong"}]}, "duration_ms": 1, "error": None}
        if candidate.action.path == list_providers.action.path:
            assert inputs == {"region_id": "region_1"}
            return {
                "status_code": 200,
                "body": {"payment_providers": [{"id": "provider_1", "name": "Default provider"}]},
                "duration_ms": 1,
                "error": None,
            }
        assert candidate.action.path == create_session.action.path
        assert inputs == {"id": "paycol_1", "provider_id": "provider_1"}
        return {
            "status_code": 200,
            "body": {"payment_session": {"id": "session_1"}},
            "duration_ms": 1,
            "error": None,
        }

    async def fake_finalize_execution_trace(trace, result, db):
        return None

    monkeypatch.setattr(rest_operator, "find_tool_candidates", fake_find_tool_candidates)
    monkeypatch.setattr(rest_operator, "_find_read_resolver_candidates_by_noun", fake_find_read_resolver_candidates_by_noun, raising=False)
    monkeypatch.setattr(rest_operator, "create_execution_trace", fake_create_execution_trace)
    monkeypatch.setattr(rest_operator, "learning_service", FakeLearningService())
    monkeypatch.setattr(rest_operator, "execute_rest_tool", fake_execute_rest_tool)
    monkeypatch.setattr(rest_operator, "finalize_execution_trace", fake_finalize_execution_trace)

    async def emit(_event_name, _payload):
        return None

    content = await rest_operator.run_rest_operator_turn(
        message="checkout",
        saas_agent_id=saas_agent_id,
        session_id=session_id,
        user_id=None,
        session=session,
        db=FakeDb(),
        emit=emit,
        public_response=True,
    )

    assert executed == [
        ("/api/accounts/{id}/complete", {"id": "acct_1"}),
        ("/api/payment-providers", {"region_id": "region_1"}),
        ("/api/payment-collections/{id}/payment-sessions", {"id": "paycol_1", "provider_id": "provider_1"}),
        ("/api/accounts/{id}/complete", {"id": "acct_1"}),
    ]
    assert all(path != "/api/products" for path, _inputs in executed)
    assert "connected API returned an error" in content
    assert "provider_1" not in content
