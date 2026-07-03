import asyncio
import json
import uuid
from contextlib import nullcontext
from types import SimpleNamespace

import pytest

from backend.core.schemas import ActionNodeRead
from backend.services.agent import rest_operator
from backend.services.agent.rest_operator import _build_inputs, _format_execution_failure, _format_missing_input_names, _format_router_decision, _maybe_handle_trace_control, _operation_intent_bonus, _parse_trace_control, _preview_body_json, _rerank_candidates_for_frame, _tokens
from backend.services.toolrouter.adapter import ToolRouterDecision, ToolRouterDecisionType
from backend.services.catalog import infer_entities, preview_openapi_spec
from backend.services.tools.generator import build_function_schema


def test_preview_openapi_spec_summarizes_methods_tags_and_samples():
    raw_spec = """
openapi: 3.0.0
info:
  title: Billing API
  version: 1.2.3
servers:
  - url: https://api.example.test
paths:
  /customers:
    get:
      operationId: listCustomers
      tags: [Customers]
      summary: List customers
      responses:
        '200':
          description: OK
  /invoices/{invoice_id}:
    get:
      operationId: getInvoice
      tags: [Invoices]
      parameters:
        - name: invoice_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: OK
"""

    preview = asyncio.run(preview_openapi_spec(spec_url=None, raw_spec=raw_spec))

    assert preview.title == "Billing API"
    assert preview.version == "1.2.3"
    assert preview.endpoint_count == 2
    assert preview.methods == {"GET": 2}
    assert preview.tags == {"Customers": 1, "Invoices": 1}
    assert preview.sample_actions[0]["name"] == "listCustomers"


def test_infer_entities_groups_by_tags_and_counts_risk():
    actions = [
        ActionNodeRead(
            id="00000000-0000-0000-0000-000000000001",
            connection_id="00000000-0000-0000-0000-000000000011",
            saas_agent_id="00000000-0000-0000-0000-000000000111",
            name="listCustomers",
            path="/customers",
            method="GET",
            risk_level="read",
            status="discovered",
            tags=["Customers"],
            created_at="2026-05-13T00:00:00Z",
            updated_at="2026-05-13T00:00:00Z",
        ),
        ActionNodeRead(
            id="00000000-0000-0000-0000-000000000002",
            connection_id="00000000-0000-0000-0000-000000000011",
            saas_agent_id="00000000-0000-0000-0000-000000000111",
            name="createCustomer",
            path="/customers",
            method="POST",
            risk_level="write",
            status="discovered",
            tags=["Customers"],
            created_at="2026-05-13T00:00:00Z",
            updated_at="2026-05-13T00:00:00Z",
        ),
    ]

    entities = infer_entities(actions)

    assert len(entities) == 1
    assert entities[0].id == "customers"
    assert entities[0].action_count == 2
    assert entities[0].read_count == 1
    assert entities[0].write_count == 1


def test_rest_operator_tokens_split_generated_openapi_names():
    tokens = set(_tokens("List available pets with findPetsByStatus from /pet/findByStatus"))

    assert {"list", "available", "pets", "pet", "find", "by", "status"} <= tokens


def test_public_json_details_include_full_read_result_for_dev_use():
    body = {
        "products": [
            {
                "id": f"prod_{index}",
                "title": f"Product {index}",
                "description": "x" * 1200,
                "options": [{"title": "Size", "values": [{"value": "S"}, {"value": "M"}, {"value": "L"}]}],
            }
            for index in range(8)
        ],
        "count": 8,
    }

    details = _preview_body_json(body)

    assert '"Product 0"' in details
    assert '"Product 7"' in details
    assert '"__preview_truncated"' not in details


def test_public_write_success_summarizes_completed_order():
    result = {
        "body": {
            "type": "order",
            "order": {
                "id": "order_123",
                "display_id": 42,
                "currency_code": "eur",
                "total": 20,
                "items": [
                    {
                        "title": "Medusa Sweatshirt",
                        "variant_sku": "SWEATSHIRT-M",
                        "quantity": 1,
                    }
                ],
            },
        }
    }

    message = rest_operator._format_public_execution_success(result=result, method="POST")

    assert "order #42 (order_123)" in message
    assert "1 x Medusa Sweatshirt (SWEATSHIRT-M)" in message
    assert "20 EUR" in message


def test_public_product_read_success_is_compact_for_shoppers():
    result = {
        "body": {
            "products": [
                {
                    "title": "Medusa Sweatshirt",
                    "options": [
                        {
                            "title": "Size",
                            "values": [{"value": "S"}, {"value": "M"}, {"value": "L"}],
                        }
                    ],
                    "variants": [{"id": "var_m", "title": "M", "sku": "SWEATSHIRT-M"}],
                }
            ],
            "count": 1,
        }
    }

    message = rest_operator._format_public_execution_success(result=result, method="GET")

    assert "Medusa Sweatshirt: sizes S, M, L" in message
    assert "```json" not in message


def test_public_shipping_options_read_success_prompts_for_choice():
    result = {
        "body": {
            "shipping_options": [
                {"id": "so_standard", "name": "Standard Shipping"},
                {"id": "so_express", "name": "Express Shipping"},
            ]
        }
    }

    message = rest_operator._format_public_execution_success(result=result, method="GET")

    assert "- Standard Shipping" in message
    assert "- Express Shipping" in message
    assert "Reply with the option name" in message


def test_public_payment_providers_read_success_prompts_for_provider_id():
    result = {"body": {"payment_providers": [{"id": "pp_system_default", "is_enabled": True}]}}

    message = rest_operator._format_public_execution_success(result=result, method="GET")

    assert "- pp_system_default" in message
    assert "Reply with the provider id" in message
    assert "```json" not in message


def test_public_order_read_success_is_compact():
    result = {
        "body": {
            "order": {
                "id": "order_123",
                "display_id": 42,
                "status": "pending",
                "currency_code": "eur",
                "total": 20,
                "items": [
                    {
                        "title": "Medusa Sweatshirt",
                        "variant_sku": "SWEATSHIRT-M",
                        "quantity": 1,
                    }
                ],
            }
        }
    }

    message = rest_operator._format_public_execution_success(result=result, method="GET")

    assert "Order #42 (order_123)" in message
    assert "Status: pending" in message
    assert "1 x Medusa Sweatshirt (SWEATSHIRT-M)" in message
    assert "```json" not in message


def test_rest_operator_infers_status_from_natural_language():
    class Action:
        parameters = [{"name": "status", "in": "query", "schema": {"enum": ["available", "pending", "sold"]}}]

    class Tool:
        function_schema = {
            "parameters": {
                "type": "object",
                "properties": {"status": {"type": "string", "enum": ["available", "pending", "sold"]}},
                "required": ["status"],
            }
        }

    inputs, missing = _build_inputs("List available pets from the connected API.", Action(), Tool())

    assert inputs == {"status": "available"}
    assert missing == []


def test_generated_tool_schema_excludes_connection_level_header_inputs():
    action = SimpleNamespace(
        name="listProducts",
        method="GET",
        path="/store/products",
        description="List products",
        parameters=[
            {
                "name": "x-publishable-api-key",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
            },
            {"name": "limit", "in": "query", "schema": {"type": "integer"}},
        ],
        request_body={},
    )

    schema = build_function_schema(action)

    params = schema["parameters"]
    assert "x-publishable-api-key" not in params["properties"]
    assert "x-publishable-api-key" not in params["required"]
    assert "limit" in params["properties"]


def test_generated_tool_schema_includes_json_request_body_allof_fields():
    action = SimpleNamespace(
        name="addLineItem",
        method="POST",
        path="/store/carts/{id}/line-items",
        description="Add a product variant as a line item in the cart.",
        parameters=[
            {
                "name": "id",
                "in": "path",
                "required": True,
                "description": "The cart's ID.",
                "schema": {"type": "string"},
            }
        ],
        request_body={
            "content": {
                "application/json": {
                    "schema": {
                        "allOf": [
                            {
                                "type": "object",
                                "required": ["variant_id", "quantity"],
                                "properties": {
                                    "variant_id": {"type": "string", "description": "Variant ID"},
                                    "quantity": {"type": "number", "description": "Quantity"},
                                },
                            }
                        ]
                    }
                }
            }
        },
    )

    params = build_function_schema(action)["parameters"]

    assert {"id", "variant_id", "quantity"} <= set(params["properties"])
    assert {"id", "variant_id", "quantity"} <= set(params["required"])


def test_generated_tool_schema_parses_stringified_json_request_body_schema():
    action = SimpleNamespace(
        name="createPaymentCollection",
        method="POST",
        path="/api/payment-collections",
        description="Create a payment collection for an account.",
        parameters=[],
        request_body={
            "content": {
                "application/json": {
                    "schema": (
                        "{'type': 'object', 'required': ['account_id'], "
                        "'properties': {'account_id': {'type': 'string', 'description': 'The account ID.'}}}"
                    )
                }
            }
        },
    )

    params = build_function_schema(action)["parameters"]

    assert "account_id" in params["properties"]
    assert "account_id" in params["required"]


def test_write_intent_bonus_prefers_mutating_action_over_read_action():
    cart_action = SimpleNamespace(method="POST", path="/store/carts/{id}/line-items", description="Add a product variant as a line item in the cart.")
    product_action = SimpleNamespace(method="GET", path="/store/products", description="Retrieve a list of products.")
    tool = SimpleNamespace(name="tool")

    assert _operation_intent_bonus("add the L size to cart", cart_action, tool) > _operation_intent_bonus(
        "add the L size to cart",
        product_action,
        tool,
    )


def test_order_collection_read_intent_prefers_orders_read_over_cart_write():
    orders_action = SimpleNamespace(method="GET", path="/store/orders", description="Retrieve the orders of the logged-in customer.")
    store_credit_action = SimpleNamespace(method="POST", path="/store/carts/{id}/store-credits", description="Add a Store Credit to a cart.")
    tool = SimpleNamespace(name="tool")

    assert rest_operator._looks_like_collection_read_request("show my orders")
    assert _operation_intent_bonus("show my orders", orders_action, tool) > _operation_intent_bonus(
        "show my orders",
        store_credit_action,
        tool,
    )


def test_exact_order_read_intent_prefers_order_get_by_id_over_checkout_write():
    order_action = SimpleNamespace(method="GET", path="/store/orders/{id}", description="Retrieve an order by its ID.")
    cart_action = SimpleNamespace(method="GET", path="/store/carts/{id}", description="Retrieve a cart by its ID.")
    complete_action = SimpleNamespace(method="POST", path="/store/carts/{id}/complete", description="Complete a cart and place an order.")
    order_tool = SimpleNamespace(name="getorder", function_schema={"parameters": {"required": ["id"], "properties": {"id": {}}}})
    cart_tool = SimpleNamespace(name="getcart", function_schema={"parameters": {"required": ["id"], "properties": {"id": {}}}})
    complete_tool = SimpleNamespace(name="completecart", function_schema={"parameters": {"required": ["id"], "properties": {"id": {}}}})

    assert not rest_operator._has_write_intent("show order order_123")
    assert _operation_intent_bonus("show order order_123", order_action, order_tool) > _operation_intent_bonus(
        "show order order_123",
        complete_action,
        complete_tool,
    )
    assert _operation_intent_bonus("show order order_123", order_action, order_tool) > _operation_intent_bonus(
        "show order order_123",
        cart_action,
        cart_tool,
    )


def test_build_inputs_extracts_resource_prefixed_id_for_matching_path():
    order_action = SimpleNamespace(method="GET", path="/store/orders/{id}", parameters=[])
    cart_action = SimpleNamespace(method="GET", path="/store/carts/{id}", parameters=[])
    tool = SimpleNamespace(function_schema={"parameters": {"required": ["id"], "properties": {"id": {"type": "string"}}}})

    order_inputs, order_missing = _build_inputs("show order order_123", order_action, tool)
    cart_inputs, cart_missing = _build_inputs("show order order_123", cart_action, tool)

    assert order_inputs == {"id": "order_123"}
    assert order_missing == []
    assert cart_inputs == {}
    assert cart_missing == ["id"]


def test_shipping_options_read_does_not_look_like_cart_write_intent():
    shipping_action = SimpleNamespace(method="GET", path="/store/shipping-options", description="Retrieve shipping options for a cart.")
    cart_update_action = SimpleNamespace(method="POST", path="/store/carts/{id}", description="Update a cart.")
    tool = SimpleNamespace(name="tool")

    assert rest_operator._looks_like_collection_read_request("show available shipping options for my cart")
    assert rest_operator._looks_like_active_resource_read_dependency("show available shipping options for my cart")
    assert not rest_operator._has_write_intent("show available shipping options for my cart")
    assert _operation_intent_bonus("show available shipping options for my cart", shipping_action, tool) > _operation_intent_bonus(
        "show available shipping options for my cart",
        cart_update_action,
        tool,
    )


def test_payment_collection_intent_prefers_payment_collection_over_cart_update():
    payment_collection_action = SimpleNamespace(method="POST", path="/store/payment-collections", description="Create a payment collection.")
    cart_update_action = SimpleNamespace(method="POST", path="/store/carts/{id}", description="Update a cart.")
    tool = SimpleNamespace(name="tool")

    assert _operation_intent_bonus("create a payment collection for my cart", payment_collection_action, tool) > _operation_intent_bonus(
        "create a payment collection for my cart",
        cart_update_action,
        tool,
    )


def test_payment_session_intent_prefers_payment_session_over_cart_complete():
    payment_session_action = SimpleNamespace(method="POST", path="/store/payment-collections/{id}/payment-sessions", description="Initialize a payment session.")
    cart_complete_action = SimpleNamespace(method="POST", path="/store/carts/{id}/complete", description="Complete a cart and place an order.")
    tool = SimpleNamespace(name="tool")

    assert _operation_intent_bonus("create a payment session using provider_id=pp_system_default", payment_session_action, tool) > _operation_intent_bonus(
        "create a payment session using provider_id=pp_system_default",
        cart_complete_action,
        tool,
    )


def test_frame_rerank_prefers_payment_provider_read_for_payment_options_question():
    frame = {
        "active_resource": {
            "collection_path": "/store/carts",
            "id": "cart_123",
            "source_action_path": "/store/carts/{id}/line-items",
        }
    }
    providers_candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(name="getpaymentproviders", function_schema={"parameters": {"required": [], "properties": {"region_id": {}}}}),
        action=SimpleNamespace(method="GET", path="/store/payment-providers", description="Retrieve payment providers.", parameters=[]),
        connection=SimpleNamespace(),
        score=10,
        reason="",
    )
    collection_candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(name="postpaymentcollections", function_schema={"parameters": {"required": ["cart_id"], "properties": {"cart_id": {}}}}),
        action=SimpleNamespace(method="POST", path="/store/payment-collections", description="Create a payment collection.", parameters=[]),
        connection=SimpleNamespace(),
        score=80,
        reason="",
    )

    ranked = rest_operator._rerank_candidates_for_frame(
        message="What payment options can I use?",
        candidates=[collection_candidate, providers_candidate],
        frame=frame,
    )

    assert ranked[0].action.path == "/store/payment-providers"


def test_context_rerank_strictly_prefers_payment_session_path():
    frame = {
        "variables": {
            "resource./store/payment-collections.id": {
                "value": "pay_col_123",
                "resource": {"collection_path": "/store/payment-collections", "resource_id": "pay_col_123"},
            },
            "resource./store/carts.id": {
                "value": "cart_123",
                "resource": {"collection_path": "/store/carts", "resource_id": "cart_123"},
            },
        },
        "active_resource": {"collection_path": "/store/carts", "id": "cart_123"},
    }
    payment_collection_candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(name="postpaymentcollections", function_schema={"parameters": {"required": ["cart_id"], "properties": {"cart_id": {}}}}),
        action=SimpleNamespace(method="POST", path="/store/payment-collections", description="Create a payment collection.", parameters=[]),
        connection=SimpleNamespace(),
        score=250,
        reason="",
    )
    payment_session_candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(
            name="postpaymentsessions",
            function_schema={"parameters": {"required": ["id", "provider_id"], "properties": {"id": {}, "provider_id": {}}}},
        ),
        action=SimpleNamespace(method="POST", path="/store/payment-collections/{id}/payment-sessions", description="Create a payment session.", parameters=[]),
        connection=SimpleNamespace(),
        score=1,
        reason="",
    )

    ranked = rest_operator._rerank_candidates_for_frame(
        message="Create a payment session for the current payment collection using provider_id=pp_system_default.",
        candidates=[payment_collection_candidate, payment_session_candidate],
        frame=frame,
    )

    assert ranked[0].action.path == "/store/payment-collections/{id}/payment-sessions"


def test_named_value_strips_sentence_punctuation():
    assert rest_operator._extract_named_value("use provider_id=pp_system_default.", "provider_id") == "pp_system_default"


def test_payment_collection_result_uses_created_collection_path_not_active_cart():
    candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(name="postpaymentcollections", function_schema={}),
        action=SimpleNamespace(method="POST", path="/store/payment-collections"),
        connection=SimpleNamespace(),
        score=1,
        reason="",
    )
    active_resource = {"collection_path": "/store/carts", "id": "cart_123"}

    assert rest_operator._result_collection_path_for_frame(candidate=candidate, active_resource=active_resource) == "/store/payment-collections"


def test_payment_session_result_uses_payment_collection_parent_path():
    candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(name="postpaymentsession", function_schema={}),
        action=SimpleNamespace(method="POST", path="/store/payment-collections/{id}/payment-sessions"),
        connection=SimpleNamespace(),
        score=1,
        reason="",
    )
    active_resource = {"collection_path": "/store/carts", "id": "cart_123"}

    assert rest_operator._result_collection_path_for_frame(candidate=candidate, active_resource=active_resource) == "/store/payment-collections"


def test_checkout_completion_result_uses_returned_order_collection_path():
    candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(name="postcartcomplete", function_schema={}),
        action=SimpleNamespace(method="POST", path="/store/carts/{id}/complete"),
        connection=SimpleNamespace(),
        score=1,
        reason="",
    )
    result = {"body": {"order": {"id": "order_123", "display_id": 20}}, "error": None}
    active_resource = {"collection_path": "/store/carts", "id": "cart_123"}

    assert (
        rest_operator._result_collection_path_for_frame(
            candidate=candidate,
            active_resource=active_resource,
            result=result,
        )
        == "/store/orders"
    )


def test_frame_context_keeps_shipping_options_read_a_read():
    frame = {
        "active_resource": {
            "collection_path": "/store/carts",
            "id": "cart_123",
            "source_action_path": "/store/carts/{id}/line-items",
        }
    }
    shipping_candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(name="getshippingoptions", function_schema={"parameters": {"required": ["cart_id"], "properties": {"cart_id": {}}}}),
        action=SimpleNamespace(method="GET", path="/store/shipping-options", description="Retrieve shipping options for a cart.", parameters=[]),
        connection=SimpleNamespace(),
        score=1,
        reason="",
    )
    shipping_write_candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(name="postshippingmethod", function_schema={"parameters": {"required": ["id", "option_id"], "properties": {"id": {}, "option_id": {}}}}),
        action=SimpleNamespace(method="POST", path="/store/carts/{id}/shipping-methods", description="Add a shipping method to a cart.", parameters=[]),
        connection=SimpleNamespace(),
        score=1,
        reason="",
    )

    message = "show available shipping options for my cart"

    assert rest_operator._context_candidate_score(message=message, candidate=shipping_candidate, frame=frame) > rest_operator._context_candidate_score(
        message=message,
        candidate=shipping_write_candidate,
        frame=frame,
    )


def test_natural_shipping_question_reranks_against_active_cart():
    frame = {
        "active_resource": {
            "collection_path": "/store/carts",
            "id": "cart_123",
            "source_action_path": "/store/carts/{id}/line-items",
        }
    }
    shipping_candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(name="getshippingoptions", function_schema={"parameters": {"required": ["cart_id"], "properties": {"cart_id": {}}}}),
        action=SimpleNamespace(method="GET", path="/store/shipping-options", description="Retrieve shipping options for a cart.", parameters=[]),
        connection=SimpleNamespace(),
        score=1,
        reason="",
    )
    shipping_write_candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(name="postshippingmethod", function_schema={"parameters": {"required": ["id", "option_id"], "properties": {"id": {}, "option_id": {}}}}),
        action=SimpleNamespace(method="POST", path="/store/carts/{id}/shipping-methods", description="Add a shipping method to a cart.", parameters=[]),
        connection=SimpleNamespace(),
        score=20,
        reason="",
    )

    message = "What shipping options do I have?"

    assert rest_operator._looks_like_active_resource_read_dependency(message)

    ranked = rest_operator._rerank_candidates_for_frame(
        message=message,
        candidates=[shipping_write_candidate, shipping_candidate],
        frame=frame,
    )

    assert ranked[0].action.path == "/store/shipping-options"


def test_frame_rerank_prefers_selected_shipping_option_action_over_line_item_delete():
    frame = {
        "active_resource": {
            "collection_path": "/store/carts",
            "id": "cart_123",
            "source_action_path": "/store/carts/{id}/line-items",
        },
        "entities": [
            {
                "entity_type": "shipping_options",
                "id": "so_standard",
                "label": "Standard Shipping",
                "aliases": ["standard shipping"],
                "raw": {"id": "so_standard", "name": "Standard Shipping"},
            }
        ],
    }
    shipping_method_candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(name="postshippingmethod", function_schema={"parameters": {"required": ["id", "option_id"], "properties": {"id": {}, "option_id": {}}}}),
        action=SimpleNamespace(method="POST", path="/store/carts/{id}/shipping-methods", description="Add a shipping method to a cart.", parameters=[]),
        connection=SimpleNamespace(),
        score=1,
        reason="",
    )
    line_item_delete_candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(name="deletelineitem", function_schema={"parameters": {"required": ["id", "line_id"], "properties": {"id": {}, "line_id": {}}}}),
        action=SimpleNamespace(method="DELETE", path="/store/carts/{id}/line-items/{line_id}", description="Delete a line item from a cart.", parameters=[]),
        connection=SimpleNamespace(),
        score=20,
        reason="",
    )

    ranked = rest_operator._rerank_candidates_for_frame(
        message="Standard Shipping",
        candidates=[line_item_delete_candidate, shipping_method_candidate],
        frame=frame,
    )

    assert ranked[0].action.path == "/store/carts/{id}/shipping-methods"


def test_frame_rerank_prefers_cart_write_over_product_detail_for_add_request():
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
                    "variants": [{"id": "var_m", "title": "M", "sku": "SWEATSHIRT-M", "options": [{"value": "M"}]}],
                },
            }
        ],
    }
    product_detail_candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(name="getproduct", function_schema={"parameters": {"required": ["id"], "properties": {"id": {}}}}),
        action=SimpleNamespace(method="GET", path="/store/products/{id}", description="Retrieve a product.", parameters=[]),
        connection=SimpleNamespace(),
        score=20,
        reason="",
    )
    line_item_candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(name="postlineitem", function_schema={"parameters": {"required": ["id", "variant_id", "quantity"], "properties": {"id": {}, "variant_id": {}, "quantity": {}}}}),
        action=SimpleNamespace(method="POST", path="/store/carts/{id}/line-items", description="Add a product variant as a line item in the cart.", parameters=[]),
        connection=SimpleNamespace(),
        score=1,
        reason="",
    )

    ranked = rest_operator._rerank_candidates_for_frame(
        message="Add one Medusa Sweatshirt in size M to my cart.",
        candidates=[product_detail_candidate, line_item_candidate],
        frame=frame,
    )

    assert ranked[0].action.path == "/store/carts/{id}/line-items"


def test_frame_rerank_prefers_action_with_entity_fillable_required_inputs():
    frame = {
        "kind": "result_context",
        "selected_entity": {
            "entity_type": "products",
            "id": "prod_1",
            "label": "Starter Shirt",
            "aliases": ["starter shirt"],
            "raw": {
                "id": "prod_1",
                "title": "Starter Shirt",
                "variants": [{"id": "var_l", "options": {"Size": "L"}}],
            },
        },
        "entities": [],
    }
    read_candidate = SimpleNamespace(
        score=11,
        tool=SimpleNamespace(
            name="readItems",
            function_schema={"parameters": {"type": "object", "properties": {}, "required": []}},
        ),
        action=SimpleNamespace(method="GET", path="/items", parameters=[]),
    )
    write_candidate = SimpleNamespace(
        score=9,
        tool=SimpleNamespace(
            name="addItem",
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
            },
        ),
        action=SimpleNamespace(method="POST", path="/orders/{id}/items", parameters=[]),
    )

    ranked = _rerank_candidates_for_frame(
        message="add the L size",
        candidates=[read_candidate, write_candidate],
        frame=frame,
    )

    assert ranked[0].action.path == write_candidate.action.path


def test_missing_path_id_prompt_uses_resource_context():
    action = SimpleNamespace(path="/store/carts/{id}/line-items")

    assert _format_missing_input_names(["id"], action) == "cart id"


def test_rest_operator_does_not_ask_visitor_for_connection_headers():
    class Action:
        parameters = [
            {
                "name": "x-publishable-api-key",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
            }
        ]

    class Tool:
        function_schema = {
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            }
        }

    inputs, missing = _build_inputs("list products", Action(), Tool())

    assert inputs == {}
    assert missing == []


def test_rest_operator_does_not_fill_optional_search_with_bare_list_request():
    class Action:
        parameters = [{"name": "q", "in": "query", "schema": {"type": "string"}}]

    class Tool:
        function_schema = {
            "parameters": {
                "type": "object",
                "properties": {"q": {"type": "string"}, "limit": {"type": "integer"}},
                "required": [],
            }
        }

    inputs, missing = _build_inputs("list products", Action(), Tool())

    assert inputs == {"limit": 5}
    assert missing == []


def test_rest_operator_fills_optional_search_only_when_filter_is_explicit():
    class Action:
        parameters = [{"name": "q", "in": "query", "schema": {"type": "string"}}]

    class Tool:
        function_schema = {
            "parameters": {
                "type": "object",
                "properties": {"q": {"type": "string"}},
                "required": [],
            }
        }

    inputs, missing = _build_inputs("search for hoodie", Action(), Tool())

    assert inputs == {"q": "hoodie"}
    assert missing == []


def test_rest_operator_parses_approval_resume_controls():
    assert _parse_trace_control("approve abcdef12") == ("approve", "abcdef12")
    assert _parse_trace_control("cancel abcdef12") == ("cancel", "abcdef12")
    assert _parse_trace_control("reject abcdef12") == ("cancel", "abcdef12")
    assert _parse_trace_control("approve this please") is None


def test_rest_operator_formats_toolrouter_topk_decision():
    decision = ToolRouterDecision(
        type=ToolRouterDecisionType.SHOW_TOPK,
        candidates=[
            SimpleNamespace(tool=SimpleNamespace(name="listOrders"), action=SimpleNamespace(method="GET", path="/orders"), score=5),
            SimpleNamespace(tool=SimpleNamespace(name="searchOrders"), action=SimpleNamespace(method="GET", path="/orders/search"), score=5),
        ],
    )

    content = _format_router_decision(decision)

    assert "I need one more detail" in content
    assert "listOrders" not in content
    assert "searchOrders" not in content
    assert "/orders" not in content
    assert "score" not in content


def test_rest_operator_router_clarification_omits_connection_headers():
    decision = ToolRouterDecision(
        type=ToolRouterDecisionType.SHOW_TOPK,
        candidates=[
            SimpleNamespace(
                tool=SimpleNamespace(name="getproduct"),
                action=SimpleNamespace(
                    method="GET",
                    path="/store/products/{id}",
                    parameters=[
                        {"name": "x-publishable-api-key", "in": "header", "required": True},
                        {"name": "id", "in": "path", "required": True},
                    ],
                ),
                score=5,
            )
        ],
    )

    content = _format_router_decision(decision)

    assert "x publishable api key" not in content.lower()
    assert "api key" not in content.lower()
    assert "id" in content.lower()


def test_rest_operator_failure_message_does_not_expose_selected_tool():
    content = _format_execution_failure(
        tool_name="listproducts",
        result={"error": "All connection attempts failed", "status_code": 0},
        trace_token="abcdef12",
    )

    assert "listproducts" not in content
    assert "selected" not in content.lower()
    assert "could not reach" in content.lower()


def test_rest_operator_public_failure_omits_debug_trace():
    content = _format_execution_failure(
        tool_name="listproducts",
        result={"error": "All connection attempts failed", "status_code": 0},
        trace_token="abcdef12",
        public_response=True,
    )

    assert "listproducts" not in content
    assert "Trace:" not in content
    assert "Status:" not in content
    assert "All connection attempts failed" not in content
    assert "could not reach" in content.lower()


def test_rest_operator_public_credential_failure_is_owner_safe():
    content = _format_execution_failure(
        tool_name="listproducts",
        result={"error": "Stored API credentials could not be decrypted. Reconnect this API credential.", "error_type": "InvalidToken", "status_code": 0},
        trace_token="abcdef12",
        public_response=True,
    )

    assert "decrypt" not in content.lower()
    assert "InvalidToken" not in content
    assert "reconnect the API credentials" in content


def test_rest_operator_public_trace_control_does_not_expose_trace_details():
    async def emit(_event_name, _payload):
        raise AssertionError("public approval controls should not emit internal events")

    content = asyncio.run(
        _maybe_handle_trace_control(
            message="approve abcdef12",
            saas_agent_id="00000000-0000-0000-0000-000000000111",
            session_id=None,
            user_id=None,
            db=None,
            emit=emit,
            public_response=True,
        )
    )

    assert "agent owner" in content
    assert "abcdef12" not in content
    assert "trace" not in content.lower()


def test_execute_rest_tool_returns_structured_error_for_bad_credentials(monkeypatch):
    class InvalidToken(Exception):
        pass

    def fail_decrypt(_value):
        raise InvalidToken()

    monkeypatch.setattr(rest_operator, "decrypt_value", fail_decrypt)
    candidate = rest_operator.ToolCandidate(
        tool=SimpleNamespace(name="listProducts"),
        action=SimpleNamespace(method="GET", path="/products", parameters=[]),
        connection=SimpleNamespace(
            auth_type=SimpleNamespace(value="bearer"),
            credentials=[SimpleNamespace(encrypted_value="bad-token", metadata_={})],
            config={"base_url": "https://example.test"},
        ),
        score=10,
        reason="test",
    )

    result = asyncio.run(rest_operator.execute_rest_tool(candidate, {}, db=None))

    assert result["status_code"] == 0
    assert result["error"] == "Stored API credentials could not be decrypted. Reconnect this API credential."
    assert result["error_type"] == "InvalidToken"


def test_public_chat_service_suppresses_all_tool_events_from_sse():
    from pathlib import Path

    service_path = Path(__file__).parents[1] / "services" / "agent" / "chat_service.py"
    source = service_path.read_text(encoding="utf-8")
    runtime_source = source.split("async def _run_agent", 1)[1].split("def _is_deployed_channel", 1)[0]

    assert 'public_response and event_name in {"tool_start", "tool_end"}' in runtime_source
    assert 'if public_response:' in runtime_source.split('kind == "on_tool_start"', 1)[1].split('elif kind == "on_tool_end"', 1)[0]
    assert 'if public_response:' in runtime_source.split('kind == "on_tool_end"', 1)[1].split("# Extract follow-ups", 1)[0]


def test_chat_service_threads_session_into_rest_operator_runtime():
    from pathlib import Path

    service_path = Path(__file__).parents[1] / "services" / "agent" / "chat_service.py"
    source = service_path.read_text(encoding="utf-8")
    run_call = source.split("self._run_agent(", 1)[1].split(")", 1)[0]
    run_signature = source.split("async def _run_agent(", 1)[1].split(") -> None", 1)[0]
    rest_call = source.split("run_rest_operator_turn(", 1)[1].split(")", 1)[0]

    assert "session=session" in run_call
    assert "session: AgentSession" in run_signature
    assert "session=session," in rest_call


@pytest.mark.asyncio
async def test_chat_service_streams_rest_operator_reply_from_model_chunks(monkeypatch):
    from backend.services.agent import chat_service as chat_module

    class FakeDb:
        def __init__(self):
            self.added = []

        def add(self, item):
            self.added.append(item)

        async def commit(self):
            return None

        async def get(self, *_args, **_kwargs):
            return None

    async def fake_run_rest_operator_turn(**_kwargs):
        return "Operation result: order_123 completed."

    async def fake_stream_rest_operator_message(**kwargs):
        assert kwargs["operation_result"] == "Operation result: order_123 completed."
        yield "Order "
        yield "order_123 completed."

    def fake_build_agent_graph(**_kwargs):
        return SimpleNamespace()

    service = chat_module.ChatService()
    queue = asyncio.Queue()
    session_id = uuid.uuid4()
    db = FakeDb()

    monkeypatch.setattr(chat_module, "build_agent_graph", fake_build_agent_graph)
    monkeypatch.setattr(chat_module, "run_rest_operator_turn", fake_run_rest_operator_turn)
    monkeypatch.setattr(service, "_stream_rest_operator_message", fake_stream_rest_operator_message, raising=False)

    await service._run_agent(
        queue=queue,
        saas_agent_id=uuid.uuid4(),
        saas_agent_name="Medusa demo",
        custom_system_prompt="",
        custom_instructions="",
        user_id=None,
        messages=[SimpleNamespace(content="checkout my cart")],
        reasoning_mode="balanced",
        session_id=session_id,
        session=SimpleNamespace(metadata_={"handoff_context": {"channel": "deployed_web"}}),
        memory_context="",
        public_response=True,
        db=db,
        timing=SimpleNamespace(span=lambda _name: nullcontext(), snapshot=lambda: {}),
    )

    deltas = []
    while not queue.empty():
        item = await queue.get()
        if item is chat_module._STREAM_DONE:
            break
        if not isinstance(item, str) or not item.startswith("event: message_delta"):
            continue
        data_line = next(line for line in item.splitlines() if line.startswith("data: "))
        deltas.append(json.loads(data_line.removeprefix("data: "))["content"])

    assert deltas == ["Order ", "order_123 completed."]
    assert db.added[-1].content == "Order order_123 completed."


def test_docker_runtime_uses_stable_dev_encryption_key():
    from pathlib import Path

    compose_source = (Path(__file__).parents[2] / "docker-compose.yml").read_text(encoding="utf-8")

    assert "STA_ENCRYPTION_KEY" in compose_source


@pytest.mark.asyncio
async def test_find_tool_candidates_uses_fusion_ranker_directly(monkeypatch):
    calls = {}

    async def fake_rank_generated_tools(**kwargs):
        calls.update(kwargs)
        return []

    monkeypatch.setattr(rest_operator, "rank_generated_tools", fake_rank_generated_tools)

    result = await rest_operator.find_tool_candidates(
        message="list products",
        saas_agent_id="agent-1",
        db=object(),
        limit=7,
    )

    assert result == []
    assert calls["message"] == "list products"
    assert calls["saas_agent_id"] == "agent-1"
    assert calls["limit"] == 7


def test_tool_search_message_expands_natural_payment_language():
    message = rest_operator._tool_search_message("How can I pay?")

    assert "payment" in message
    assert "payment providers" in message
    assert "payment methods" in message
    assert "payment session" not in message


def test_tool_search_message_strips_synthetic_active_context_for_payment_options():
    message = rest_operator._tool_search_message(
        "What payment options can I use? Active resource collection /store/carts Active resource id available internally"
    )

    assert message.startswith("What payment options can I use?")
    assert "payment providers" in message
    assert "Active resource collection" not in message


@pytest.mark.asyncio
async def test_find_tool_candidates_prefers_collection_get_for_inventory_question(monkeypatch):
    detail = SimpleNamespace(
        tool=SimpleNamespace(
            name="getproduct",
            risk_level="read",
            function_schema={"parameters": {"required": ["product_id"]}},
        ),
        action=SimpleNamespace(method="GET", path="/products/{product_id}", name="getproduct", description="Get product"),
        connection=SimpleNamespace(name="Read API"),
        score=32,
        reason="fusion",
    )
    collection = SimpleNamespace(
        tool=SimpleNamespace(
            name="listproducts",
            risk_level="read",
            function_schema={"parameters": {"required": []}},
        ),
        action=SimpleNamespace(method="GET", path="/products", name="listproducts", description="List products"),
        connection=SimpleNamespace(name="Read API"),
        score=29,
        reason="fusion",
    )

    async def fake_rank_generated_tools(**kwargs):
        return [detail, collection]

    monkeypatch.setattr(rest_operator, "rank_generated_tools", fake_rank_generated_tools)

    result = await rest_operator.find_tool_candidates(
        message="what products do you have?",
        saas_agent_id="agent-1",
        db=object(),
    )

    assert result[0].tool.name == "listproducts"
    assert result[1].tool.name == "getproduct"


@pytest.mark.asyncio
async def test_find_tool_candidates_does_not_run_legacy_overlap_when_index_missing(monkeypatch):
    async def fake_rank_generated_tools(**kwargs):
        return []

    monkeypatch.setattr(rest_operator, "rank_generated_tools", fake_rank_generated_tools)

    result = await rest_operator.find_tool_candidates(
        message="unmatched",
        saas_agent_id="agent-1",
        db=object(),
    )

    assert result == []
