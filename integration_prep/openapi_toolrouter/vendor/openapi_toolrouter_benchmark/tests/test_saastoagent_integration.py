import json
from pathlib import Path

import pytest


FIXTURE = {
    "openapi": "3.0.0",
    "info": {"title": "Fixture Commerce API", "version": "1.0.0"},
    "servers": [{"url": "http://localhost:9000"}],
    "components": {
        "securitySchemes": {"bearer": {"type": "http", "scheme": "bearer"}},
        "schemas": {
            "ProductCreate": {
                "type": "object",
                "required": ["title"],
                "properties": {"title": {"type": "string"}},
            },
            "Product": {
                "type": "object",
                "required": ["id", "title"],
                "properties": {"id": {"type": "string"}, "title": {"type": "string"}},
            },
        },
    },
    "paths": {
        "/store/products": {
            "get": {
                "operationId": "ListProducts",
                "tags": ["Products"],
                "summary": "List products",
                "responses": {"200": {"description": "OK"}},
            },
            "post": {
                "operationId": "CreateProduct",
                "tags": ["Products"],
                "summary": "Create product",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ProductCreate"}}},
                },
                "responses": {"200": {"description": "OK"}},
                "security": [{"bearer": []}],
            },
        },
        "/store/products/{id}": {
            "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
            "get": {
                "operationId": "GetProduct",
                "tags": ["Products"],
                "summary": "Get product",
                "responses": {"200": {"description": "OK"}},
            },
            "delete": {
                "operationId": "DeleteProduct",
                "tags": ["Products"],
                "summary": "Delete product",
                "responses": {"204": {"description": "Deleted"}},
                "security": [{"bearer": []}],
            },
        },
    },
}


def build_artifacts(tmp_path: Path) -> Path:
    import yaml

    from toolrouter.graphgen import build_schema_graph, write_graph
    from toolrouter.openapi_loader import load_openapi_specs, write_normalized_bundle
    from toolrouter.raggen import build_rag_corpus, write_rag_corpus

    spec_path = tmp_path / "fixture.yaml"
    spec_path.write_text(yaml.safe_dump(FIXTURE, sort_keys=False), encoding="utf-8")
    bundle = load_openapi_specs([spec_path])
    out = tmp_path / "artifacts"
    write_normalized_bundle(bundle, out)
    write_graph(build_schema_graph(bundle), out)
    write_rag_corpus(build_rag_corpus(bundle), out)
    return out


def permissive_guardrails(**overrides):
    config = {
        "mode": "auto_read",
        "auto_route_confidence_threshold": 0.0,
        "route_margin_threshold": 0.0,
        "unsafe_write_threshold": 0.0,
    }
    config.update(overrides)
    return config


def test_route_tool_request_high_confidence_read_route(tmp_path: Path):
    from toolrouter.integration.saastoagent_adapter import route_tool_request

    decision = route_tool_request(
        tenant_id="tenant-a",
        integration_id="fixture",
        user_query="list products",
        conversation_context=None,
        artifacts_path=str(build_artifacts(tmp_path)),
        guardrail_config=permissive_guardrails(),
        feedback_log_path=str(tmp_path / "feedback.jsonl"),
        feedback_model_path=None,
    )

    assert decision.decision_type == "ROUTE"
    assert decision.selected_method == "GET"
    assert decision.selected_path == "/store/products"
    assert decision.guardrail_decision.mode == "auto_read"
    assert decision.feedback_event_id


def test_suggest_mode_forces_medium_confidence_topk(tmp_path: Path):
    from toolrouter.integration.saastoagent_adapter import route_tool_request

    decision = route_tool_request(
        tenant_id="tenant-a",
        integration_id="fixture",
        user_query="list products",
        conversation_context=None,
        artifacts_path=str(build_artifacts(tmp_path)),
        guardrail_config=permissive_guardrails(mode="suggest"),
        feedback_log_path=None,
        feedback_model_path=None,
    )

    assert decision.decision_type == "SHOW_TOPK"
    assert len(decision.top_candidates) == 3
    assert decision.selected_endpoint is None


def test_missing_param_asks_for_exact_param(tmp_path: Path):
    from toolrouter.integration.saastoagent_adapter import route_tool_request

    decision = route_tool_request(
        tenant_id="tenant-a",
        integration_id="fixture",
        user_query="get product",
        conversation_context=None,
        artifacts_path=str(build_artifacts(tmp_path)),
        guardrail_config=permissive_guardrails(),
        feedback_log_path=None,
        feedback_model_path=None,
    )

    assert decision.decision_type == "ASK_PARAM"
    assert decision.selected_path == "/store/products/{id}"
    assert "id" in decision.missing_params
    assert "id" in decision.follow_up_question


def test_policy_gap_asks_for_policy_source(tmp_path: Path):
    from toolrouter.integration.saastoagent_adapter import route_tool_request

    decision = route_tool_request(
        tenant_id="tenant-a",
        integration_id="fixture",
        user_query="only list products if merchant policy allows it",
        conversation_context=None,
        artifacts_path=str(build_artifacts(tmp_path)),
        guardrail_config=permissive_guardrails(),
        feedback_log_path=None,
        feedback_model_path=None,
    )

    assert decision.decision_type == "ASK_POLICY"
    assert "business policy" in decision.follow_up_question


def test_delete_endpoint_blocks_unsafe_without_confirmation(tmp_path: Path):
    from toolrouter.integration.saastoagent_adapter import route_tool_request

    decision = route_tool_request(
        tenant_id="tenant-a",
        integration_id="fixture",
        user_query="delete product id=prod_123",
        conversation_context=None,
        artifacts_path=str(build_artifacts(tmp_path)),
        guardrail_config=permissive_guardrails(mode="block_write"),
        feedback_log_path=None,
        feedback_model_path=None,
    )

    assert decision.decision_type == "BLOCK_UNSAFE"
    assert decision.guardrail_decision.mode == "block_write"
    assert decision.guardrail_decision.requires_confirmation is True
    assert "DELETE" in decision.guardrail_decision.reason


def test_confirm_write_guardrail_allows_confirmed_write_as_dry_route(tmp_path: Path):
    from toolrouter.integration.saastoagent_adapter import route_tool_request

    blocked = route_tool_request(
        tenant_id="tenant-a",
        integration_id="fixture",
        user_query="create product title=Hat",
        conversation_context=None,
        artifacts_path=str(build_artifacts(tmp_path)),
        guardrail_config=permissive_guardrails(mode="confirm_write"),
        feedback_log_path=None,
        feedback_model_path=None,
    )
    confirmed = route_tool_request(
        tenant_id="tenant-a",
        integration_id="fixture",
        user_query="create product title=Hat",
        conversation_context=[{"confirmed": True}],
        artifacts_path=str(build_artifacts(tmp_path)),
        guardrail_config=permissive_guardrails(mode="confirm_write"),
        feedback_log_path=None,
        feedback_model_path=None,
    )

    assert blocked.decision_type == "BLOCK_UNSAFE"
    assert blocked.guardrail_decision.requires_confirmation is True
    assert confirmed.decision_type == "ROUTE"
    assert confirmed.guardrail_decision.requires_confirmation is False
    assert confirmed.selected_method == "POST"


def test_feedback_event_is_standardized_and_redacts_secrets(tmp_path: Path):
    from toolrouter.integration.saastoagent_adapter import route_tool_request

    feedback_log = tmp_path / "feedback.jsonl"
    decision = route_tool_request(
        tenant_id="tenant-a",
        integration_id="fixture",
        user_query="list products credential_value=secret",
        conversation_context=[{"provided_params": {"api_key": "secret", "q": "shirts"}}],
        artifacts_path=str(build_artifacts(tmp_path)),
        guardrail_config=permissive_guardrails(),
        feedback_log_path=str(feedback_log),
        feedback_model_path=None,
    )
    row = json.loads(feedback_log.read_text(encoding="utf-8").splitlines()[0])

    assert row["event_id"] == decision.feedback_event_id
    assert row["tenant_id"] == "tenant-a"
    assert row["integration_id"] == "fixture"
    assert row["feedback_source"] == "agent"
    assert row["label_quality"] == "implicit"
    assert row["provided_params"]["api_key"] == "[REDACTED]"


def test_missing_feedback_model_path_is_optional(tmp_path: Path):
    from toolrouter.integration.saastoagent_adapter import route_tool_request

    decision = route_tool_request(
        tenant_id="tenant-a",
        integration_id="fixture",
        user_query="list products",
        conversation_context=None,
        artifacts_path=str(build_artifacts(tmp_path)),
        guardrail_config=permissive_guardrails(),
        feedback_log_path=None,
        feedback_model_path=str(tmp_path / "missing.joblib"),
    )

    assert decision.top_candidates


def test_chat_normalization_uses_fake_model_without_endpoint_authority():
    from toolrouter.integration.chat import normalize_chat_request

    class FakeClient:
        def normalize(self, **_kwargs):
            return {
                "router_query": "create product",
                "provided_params": {"title": "Hat"},
                "confirmed": True,
                "policy_text": "",
                "ignored_endpoint_id": "fixture:DeleteProduct",
            }

    normalized = normalize_chat_request(
        user_query="please create a product named Hat",
        conversation_context=[],
        client=FakeClient(),
    )

    assert normalized.router_query == "create product"
    assert normalized.provided_params == {"title": "Hat"}
    assert normalized.confirmed is True
    assert "ignored_endpoint_id" not in normalized.model_dump()


def test_sandbox_feedback_capture_redacts_credentials(tmp_path: Path):
    from sandbox.server import append_sandbox_feedback

    path = tmp_path / "sandbox_feedback.jsonl"
    event = append_sandbox_feedback(
        path,
        {
            "tenant_id": "tenant-a",
            "integration_id": "fixture",
            "query": "list products",
            "sandbox_credentials": {"username": "demo", "password": "secret"},
            "user_selected_endpoint": "fixture:ListProducts",
        },
    )
    row = json.loads(path.read_text(encoding="utf-8").splitlines()[0])

    assert event["event_id"] == row["event_id"]
    assert row["sandbox_credentials"]["password"] == "[REDACTED]"
    assert row["sandbox_credentials"]["username"] == "demo"


def test_route_tool_request_works_with_medusa_artifacts():
    from toolrouter.integration.saastoagent_adapter import route_tool_request

    artifacts = Path(__file__).resolve().parents[1] / "artifacts"
    decision = route_tool_request(
        tenant_id="tenant-a",
        integration_id="medusa",
        user_query="list products",
        conversation_context=None,
        artifacts_path=str(artifacts),
        guardrail_config=permissive_guardrails(mode="suggest"),
        feedback_log_path=None,
        feedback_model_path=None,
    )

    assert decision.top_candidates
    assert decision.top_candidates[0].method in {"GET", "POST", "PATCH", "DELETE"}


def test_integration_code_introduces_no_medusa_maps_or_lexicons():
    integration_dir = Path(__file__).resolve().parents[1] / "toolrouter" / "integration"
    forbidden = ["MEDUSA_ENDPOINT_MAP", "ACTION_LEXICON", "STOPWORDS", "stopword", "lexicon"]
    for path in integration_dir.rglob("*.py"):
        body = path.read_text(encoding="utf-8")
        assert not any(token in body for token in forbidden), path
