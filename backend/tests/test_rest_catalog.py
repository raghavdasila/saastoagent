import asyncio
from types import SimpleNamespace

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


def test_docker_runtime_uses_stable_dev_encryption_key():
    from pathlib import Path

    compose_source = (Path(__file__).parents[2] / "docker-compose.yml").read_text(encoding="utf-8")

    assert "STA_ENCRYPTION_KEY" in compose_source
