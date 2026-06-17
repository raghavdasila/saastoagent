from types import SimpleNamespace
from uuid import uuid4

from backend.services.toolrouter.documents import build_router_documents, catalog_fingerprint


def _action(**overrides):
    data = {
        "id": uuid4(),
        "method": "POST",
        "path": "/store/carts/{id}/line-items",
        "name": "addLineItem",
        "description": "Add a product variant as a line item in the cart.",
        "parameters": [
            {"name": "id", "in": "path", "required": True, "description": "Cart ID"},
            {"name": "region_id", "in": "query", "required": False},
        ],
        "request_body": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "required": ["variant_id", "quantity"],
                        "properties": {
                            "variant_id": {"type": "string"},
                            "quantity": {"type": "integer"},
                        },
                    }
                }
            }
        },
        "responses": {"200": {"description": "Cart response"}},
        "security": [{"apiKeyAuth": []}],
        "tags": ["cart"],
        "source_index": "7",
        "updated_at": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _tool(action_id, **overrides):
    data = {
        "id": uuid4(),
        "action_node_id": action_id,
        "name": "post_store_carts_id_line_items",
        "description": "Add line item",
        "function_schema": {
            "parameters": {
                "properties": {
                    "id": {"type": "string"},
                    "variant_id": {"type": "string"},
                    "quantity": {"type": "integer"},
                },
                "required": ["id", "variant_id", "quantity"],
            }
        },
        "updated_at": None,
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def test_build_router_documents_are_dynamic_from_action_and_tool_rows():
    action = _action()
    tool = _tool(action.id)

    docs = build_router_documents([(tool, action)])

    kinds = {doc.doc_kind for doc in docs}
    assert {"endpoint", "parameter", "request", "response", "auth", "graph"} <= kinds
    assert all(doc.action_node_id == action.id for doc in docs)
    assert any("variant_id" in doc.search_text for doc in docs)
    assert any("apiKeyAuth" in doc.search_text for doc in docs)
    assert any("resource cart" in doc.search_text for doc in docs)


def test_catalog_fingerprint_changes_when_catalog_payload_changes():
    action = _action()
    tool = _tool(action.id)

    first = catalog_fingerprint([(tool, action)])
    second = catalog_fingerprint([(_tool(action.id, name="renamed_tool"), action)])

    assert first != second
