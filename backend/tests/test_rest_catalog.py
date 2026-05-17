import asyncio

from backend.core.schemas import ActionNodeRead
from backend.services.agent.rest_operator import _build_inputs, _parse_trace_control, _tokens
from backend.services.catalog import infer_entities, preview_openapi_spec


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


def test_rest_operator_parses_approval_resume_controls():
    assert _parse_trace_control("approve abcdef12") == ("approve", "abcdef12")
    assert _parse_trace_control("cancel abcdef12") == ("cancel", "abcdef12")
    assert _parse_trace_control("reject abcdef12") == ("cancel", "abcdef12")
    assert _parse_trace_control("approve this please") is None
