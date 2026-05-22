import asyncio
from types import SimpleNamespace

from backend.core.schemas import ActionNodeRead
from backend.services.agent.rest_operator import _build_inputs, _format_execution_failure, _format_router_decision, _maybe_handle_trace_control, _parse_trace_control, _tokens
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
    assert "could not reach" in content.lower()


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


def test_public_chat_service_suppresses_all_tool_events_from_sse():
    from pathlib import Path

    service_path = Path(__file__).parents[1] / "services" / "agent" / "chat_service.py"
    source = service_path.read_text(encoding="utf-8")
    runtime_source = source.split("async def _run_agent", 1)[1].split("def _is_deployed_channel", 1)[0]

    assert 'public_response and event_name in {"tool_start", "tool_end"}' in runtime_source
    assert 'if public_response:' in runtime_source.split('kind == "on_tool_start"', 1)[1].split('elif kind == "on_tool_end"', 1)[0]
    assert 'if public_response:' in runtime_source.split('kind == "on_tool_end"', 1)[1].split("# Extract follow-ups", 1)[0]
