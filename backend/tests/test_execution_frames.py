from types import SimpleNamespace
import uuid

import pytest

from backend.services.agent.execution_frames import (
    FRAME_METADATA_KEY,
    active_resource_context,
    augment_message_with_frame_context,
    build_inputs_from_frame,
    capture_result_frame,
    find_entity_reference,
    promote_active_resource,
    preserve_selected_entity,
)
from backend.services.agent import rest_operator
from backend.services.agent.state_variables import remember_resource_id_variable


def test_execution_frame_captures_catalog_entities_from_read_result():
    frame = capture_result_frame(
        message="what products do we have",
        tool=SimpleNamespace(name="listProducts"),
        action=SimpleNamespace(method="GET", path="/store/products", name="listProducts"),
        result={
            "body": {
                "products": [
                    {
                        "id": "prod_1",
                        "title": "Medusa T-Shirt",
                        "handle": "t-shirt",
                        "variants": [{"id": "var_l", "title": "Large", "options": {"Size": "L"}}],
                    }
                ]
            }
        },
    )

    assert frame is not None
    assert frame["kind"] == "result_context"
    assert frame["entities"][0]["entity_type"] == "products"
    assert frame["entities"][0]["id"] == "prod_1"
    assert "medusa t shirt" in frame["entities"][0]["aliases"]


def test_execution_frame_resolves_named_product_variant_and_default_quantity():
    frame = {
        "kind": "result_context",
        "entities": [
            {
                "entity_type": "products",
                "id": "prod_1",
                "label": "Medusa T-Shirt",
                "aliases": ["medusa t shirt", "t-shirt"],
                "raw": {
                    "id": "prod_1",
                    "title": "Medusa T-Shirt",
                    "variants": [
                        {"id": "var_s", "title": "Small", "options": {"Size": "S"}},
                        {"id": "var_l", "title": "Large", "options": {"Size": "L"}},
                    ],
                },
            }
        ],
    }
    action = SimpleNamespace(parameters=[])
    tool = SimpleNamespace(
        function_schema={
            "parameters": {
                "type": "object",
                "properties": {"variant_id": {"type": "string"}, "quantity": {"type": "integer"}},
                "required": ["variant_id", "quantity"],
            }
        }
    )

    entity = find_entity_reference("add the L size to cart", frame)
    inputs, missing = build_inputs_from_frame(
        message="add the L size to cart",
        action=action,
        tool=tool,
        frame=frame,
        base_inputs={},
    )

    assert entity is not None
    assert entity["id"] == "prod_1"
    assert inputs == {"variant_id": "var_l", "quantity": 1}
    assert missing == []


def test_execution_frame_prefers_requested_size_over_product_tokens_in_sku():
    frame = {
        "kind": "result_context",
        "entities": [
            {
                "entity_type": "products",
                "id": "prod_1",
                "label": "Medusa Sweatshirt",
                "aliases": ["medusa sweatshirt", "sweatshirt"],
                "raw": {
                    "id": "prod_1",
                    "title": "Medusa Sweatshirt",
                    "handle": "sweatshirt",
                    "variants": [
                        {"id": "var_s", "title": "S", "sku": "SWEATSHIRT-S", "options": [{"value": "S"}]},
                        {"id": "var_m", "title": "M", "sku": "SWEATSHIRT-M", "options": [{"value": "M"}]},
                    ],
                },
            }
        ],
    }
    action = SimpleNamespace(parameters=[])
    tool = SimpleNamespace(
        function_schema={
            "parameters": {
                "type": "object",
                "properties": {"variant_id": {"type": "string"}, "quantity": {"type": "integer"}},
                "required": ["variant_id", "quantity"],
            }
        }
    )

    inputs, missing = build_inputs_from_frame(
        message="add one Medusa Sweatshirt in size M to my cart",
        action=action,
        tool=tool,
        frame=frame,
        base_inputs={},
    )

    assert inputs == {"variant_id": "var_m", "quantity": 1}
    assert missing == []


def test_execution_frame_fills_shipping_option_id_from_selected_option_entity():
    frame = promote_active_resource(
        {
            "kind": "result_context",
            "entities": [
                {
                    "entity_type": "shipping_options",
                    "id": "so_standard",
                    "label": "Standard Shipping",
                    "aliases": ["standard shipping"],
                    "raw": {"id": "so_standard", "name": "Standard Shipping"},
                }
            ],
        },
        collection_path="/store/carts",
        resource_id="cart_123",
        source_action_path="/store/carts/{id}/line-items",
    )
    action = SimpleNamespace(path="/store/carts/{id}/shipping-methods", parameters=[])
    tool = SimpleNamespace(
        function_schema={
            "parameters": {
                "type": "object",
                "properties": {"id": {"type": "string"}, "option_id": {"type": "string"}},
                "required": ["id", "option_id"],
            }
        }
    )

    entity = find_entity_reference("Standard Shipping", frame)
    inputs, missing = build_inputs_from_frame(
        message="Standard Shipping",
        action=action,
        tool=tool,
        frame=frame,
        base_inputs={},
    )

    assert entity is not None
    assert inputs == {"id": "cart_123", "option_id": "so_standard"}
    assert missing == []


def test_execution_frame_fills_cart_id_from_resource_variable_without_active_resource():
    frame = remember_resource_id_variable(
        {"kind": "result_context"},
        collection_path="/store/carts",
        resource_id="cart_123",
    )
    action = SimpleNamespace(path="/store/shipping-options", parameters=[])
    tool = SimpleNamespace(
        function_schema={
            "parameters": {
                "type": "object",
                "properties": {"cart_id": {"type": "string"}},
                "required": ["cart_id"],
            }
        }
    )

    frame.pop("active_resource", None)
    inputs, missing = build_inputs_from_frame(
        message="What shipping options do I have?",
        action=action,
        tool=tool,
        frame=frame,
        base_inputs={},
    )

    assert inputs == {"cart_id": "cart_123"}
    assert missing == []


def test_execution_frame_augments_natural_pay_question_with_active_cart_not_last_shipping_read():
    frame = {
        "source": {
            "tool_name": "getshippingoptions",
            "action_name": "GetShippingOptions",
            "method": "GET",
            "path": "/store/shipping-options",
        },
        "active_resource": {
            "collection_path": "/store/carts",
            "id": "cart_123",
            "source_action_path": "/store/carts/{id}/shipping-methods",
        },
    }

    routed = augment_message_with_frame_context("How can I pay?", {}, frame)

    assert "Active resource collection /store/carts" in routed
    assert "/store/shipping-options" not in routed


def test_execution_frame_explicit_entity_switch_beats_previous_selection():
    frame = {
        "kind": "result_context",
        "selected_entity": {
            "entity_type": "products",
            "id": "prod_1",
            "label": "Medusa T-Shirt",
            "aliases": ["medusa t shirt", "t-shirt"],
            "raw": {"id": "prod_1", "title": "Medusa T-Shirt"},
        },
        "entities": [
            {
                "entity_type": "products",
                "id": "prod_1",
                "label": "Medusa T-Shirt",
                "aliases": ["medusa t shirt", "t-shirt"],
                "raw": {"id": "prod_1", "title": "Medusa T-Shirt"},
            },
            {
                "entity_type": "products",
                "id": "prod_2",
                "label": "Medusa Sweatshirt",
                "aliases": ["medusa sweatshirt", "sweatshirt"],
                "raw": {"id": "prod_2", "title": "Medusa Sweatshirt"},
            },
        ],
    }

    entity = find_entity_reference("buy the sweatshirt", frame)

    assert entity is not None
    assert entity["id"] == "prod_2"


def test_execution_frame_fills_product_identifier_without_hardcoded_product_name():
    frame = {
        "kind": "result_context",
        "entities": [
            {
                "entity_type": "items",
                "id": "item_42",
                "label": "Starter Plan",
                "aliases": ["starter plan"],
                "raw": {"id": "item_42", "name": "Starter Plan"},
            }
        ],
    }
    action = SimpleNamespace(parameters=[])
    tool = SimpleNamespace(
        function_schema={
            "parameters": {
                "type": "object",
                "properties": {"product_id": {"type": "string"}, "qty": {"type": "integer"}},
                "required": ["product_id", "qty"],
            }
        }
    )

    inputs, missing = build_inputs_from_frame(
        message="buy starter plan",
        action=action,
        tool=tool,
        frame=frame,
        base_inputs={},
    )

    assert inputs == {"product_id": "item_42", "qty": 1}
    assert missing == []


def test_execution_frame_does_not_use_product_id_as_unrelated_cart_path_id():
    frame = {
        "kind": "result_context",
        "entities": [
            {
                "entity_type": "products",
                "id": "prod_1",
                "label": "Medusa T-Shirt",
                "aliases": ["medusa t shirt"],
                "raw": {
                    "id": "prod_1",
                    "title": "Medusa T-Shirt",
                    "variants": [{"id": "var_l", "options": {"Size": "L"}}],
                },
            }
        ],
    }
    action = SimpleNamespace(path="/store/carts/{id}/line-items", parameters=[])
    tool = SimpleNamespace(
        function_schema={
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "variant_id": {"type": "string"},
                    "quantity": {"type": "integer"},
                },
                "required": ["id", "variant_id", "quantity"],
            }
        }
    )

    inputs, missing = build_inputs_from_frame(
        message="add the L size to cart",
        action=action,
        tool=tool,
        frame=frame,
        base_inputs={},
    )

    assert inputs == {"variant_id": "var_l", "quantity": 1}
    assert missing == ["id"]


def test_execution_frame_preserves_selected_entity_after_followup_read():
    frame = {"kind": "result_context", "entities": []}
    selected = {"id": "prod_1", "label": "Medusa T-Shirt"}

    updated = preserve_selected_entity(frame, selected)

    assert updated["selected_entity"] == selected
    assert "selected_entity" not in frame


def test_execution_frame_remembers_selected_variant_for_affirmative_cart_followup():
    frame = {"kind": "result_context", "entities": []}
    selected = {
        "entity_type": "products",
        "id": "prod_1",
        "label": "Medusa Sweatshirt",
        "aliases": ["medusa sweatshirt", "sweatshirt"],
        "raw": {
            "id": "prod_1",
            "title": "Medusa Sweatshirt",
            "variants": [
                {"id": "var_s", "title": "S", "sku": "SWEATSHIRT-S"},
                {"id": "var_m", "title": "M", "sku": "SWEATSHIRT-M"},
                {"id": "var_l", "title": "L", "sku": "SWEATSHIRT-L"},
            ],
        },
    }
    frame = preserve_selected_entity(frame, selected, message="I'll take a medium.")
    frame = promote_active_resource(
        frame,
        collection_path="/store/carts",
        resource_id="cart_123",
        source_action_path="/store/carts/{id}/line-items",
    )
    action = SimpleNamespace(path="/store/carts/{id}/line-items", parameters=[])
    tool = SimpleNamespace(
        function_schema={
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "variant_id": {"type": "string"},
                    "quantity": {"type": "integer"},
                },
                "required": ["id", "variant_id", "quantity"],
            }
        }
    )

    inputs, missing = build_inputs_from_frame(
        message="Yes, please add it to my cart.",
        action=action,
        tool=tool,
        frame=frame,
        base_inputs={"quantity": 1},
    )

    assert inputs == {"id": "cart_123", "variant_id": "var_m", "quantity": 1}
    assert missing == []


def test_execution_frame_augments_slot_only_reply_with_pending_operation_context():
    frame = {
        "kind": "operation_context",
        "source": {"tool_name": "addCartItem", "action_name": "addCartItem", "method": "POST", "path": "/cart/items"},
        "selected_entity": {
            "entity_type": "products",
            "id": "prod_1",
            "label": "Medusa T-Shirt",
            "aliases": ["medusa t shirt"],
            "raw": {"id": "prod_1", "title": "Medusa T-Shirt"},
        },
    }

    routed_message = augment_message_with_frame_context("L", frame["selected_entity"], frame)

    assert "Medusa T-Shirt" in routed_message
    assert "addCartItem" in routed_message
    assert "/cart/items" in routed_message


def test_execution_frame_promotes_internal_dependency_as_active_resource():
    frame = {
        "kind": "result_context",
        "selected_entity": {"entity_type": "items", "id": "item_1", "label": "Starter Plan"},
    }

    updated = promote_active_resource(
        frame,
        collection_path="/api/accounts",
        resource_id="acct_1",
        source_action_path="/api/accounts/{id}/subscriptions",
    )

    assert active_resource_context(updated) == {
        "collection_path": "/api/accounts",
        "id": "acct_1",
        "source_action_path": "/api/accounts/{id}/subscriptions",
        "reason": "internal_dependency_used_successfully",
    }
    assert updated["selected_entity"]["id"] == "item_1"
    assert "active_resource" not in frame


def test_execution_frame_augments_workflow_message_with_active_resource_not_selected_entity():
    frame = promote_active_resource(
        {
            "kind": "result_context",
            "source": {"tool_name": "getItems", "action_name": "getItems", "method": "GET", "path": "/api/items/{id}"},
            "selected_entity": {
                "entity_type": "items",
                "id": "item_1",
                "label": "Starter Plan",
                "aliases": ["starter plan"],
                "raw": {"id": "item_1", "name": "Starter Plan"},
            },
        },
        collection_path="/api/accounts",
        resource_id="acct_1",
        source_action_path="/api/accounts/{id}/subscriptions",
    )

    routed_message = augment_message_with_frame_context("checkout", frame["selected_entity"], frame)

    assert "Active resource collection /api/accounts" in routed_message
    assert "Active resource id available internally" in routed_message
    assert "Starter Plan" not in routed_message
    assert "item_1" not in routed_message
    assert "/api/items/{id}" not in routed_message


def test_execution_frame_fills_active_resource_id_for_workflow_action():
    frame = promote_active_resource(
        {"kind": "result_context"},
        collection_path="/api/accounts",
        resource_id="acct_1",
        source_action_path="/api/accounts/{id}/subscriptions",
    )
    action = SimpleNamespace(path="/api/accounts/{id}/complete", parameters=[])
    tool = SimpleNamespace(
        function_schema={
            "parameters": {
                "type": "object",
                "properties": {"id": {"type": "string"}},
                "required": ["id"],
            }
        }
    )

    inputs, missing = build_inputs_from_frame(
        message="checkout",
        action=action,
        tool=tool,
        frame=frame,
        base_inputs={},
    )

    assert inputs == {"id": "acct_1"}
    assert missing == []


def test_execution_frame_ignores_unrelated_followup():
    frame = {
        "kind": "result_context",
        "entities": [
            {
                "entity_type": "products",
                "id": "prod_1",
                "label": "Medusa T-Shirt",
                "aliases": ["medusa t shirt"],
                "raw": {"id": "prod_1", "title": "Medusa T-Shirt"},
            }
        ],
    }

    assert find_entity_reference("what can you do?", frame) is None


@pytest.mark.asyncio
async def test_rest_operator_resumes_active_frame_before_fresh_routing(monkeypatch):
    frame = {
        "kind": "result_context",
        "entities": [
            {
                "entity_type": "products",
                "id": "prod_1",
                "label": "Medusa T-Shirt",
                "aliases": ["medusa t shirt"],
                "raw": {"id": "prod_1", "title": "Medusa T-Shirt"},
            }
        ],
    }
    session = SimpleNamespace(metadata_={FRAME_METADATA_KEY: frame})
    saas_agent_id = uuid.uuid4()
    executed_inputs = {}

    action = SimpleNamespace(method="POST", path="/cart/items", name="addCartItem", parameters=[])
    tool = SimpleNamespace(
        name="addCartItem",
        risk_level="read",
        requires_approval=False,
        function_schema={
            "parameters": {
                "type": "object",
                "properties": {"product_id": {"type": "string"}, "quantity": {"type": "integer"}},
                "required": ["product_id", "quantity"],
            }
        },
    )
    candidate = rest_operator.ToolCandidate(
        tool=tool,
        action=action,
        connection=SimpleNamespace(id=uuid.uuid4(), name="Store API"),
        score=6,
        reason="cart",
    )

    async def fake_find_tool_candidates(*, message, saas_agent_id, db, limit=5):
        assert "prod_1" in message
        return [candidate]

    async def fake_create_execution_trace(**kwargs):
        assert kwargs["inputs"] == {"product_id": "prod_1", "quantity": 1}
        assert kwargs["status"] == "executing"
        return SimpleNamespace(id=uuid.uuid4())

    async def fake_execute_rest_tool(candidate, inputs, db):
        executed_inputs.update(inputs)
        return {"status_code": 200, "body": {"ok": True}, "duration_ms": 1, "error": None}

    async def fake_finalize_execution_trace(trace, result, db):
        return None

    class FakeDb:
        async def commit(self):
            return None

    async def emit(_event_name, _payload):
        return None

    monkeypatch.setattr(rest_operator, "find_tool_candidates", fake_find_tool_candidates)
    monkeypatch.setattr(rest_operator, "create_execution_trace", fake_create_execution_trace)
    monkeypatch.setattr(rest_operator, "execute_rest_tool", fake_execute_rest_tool)
    monkeypatch.setattr(rest_operator, "finalize_execution_trace", fake_finalize_execution_trace)

    content = await rest_operator.run_rest_operator_turn(
        message="add it to cart",
        saas_agent_id=saas_agent_id,
        session_id=uuid.uuid4(),
        session=session,
        user_id=None,
        db=FakeDb(),
        emit=emit,
        public_response=True,
    )

    assert executed_inputs == {"product_id": "prod_1", "quantity": 1}
    assert content == "Done. I handled that for you."
    assert session.metadata_[FRAME_METADATA_KEY]["selected_entity"]["id"] == "prod_1"
