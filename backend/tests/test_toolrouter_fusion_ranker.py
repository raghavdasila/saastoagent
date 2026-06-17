from types import SimpleNamespace
from uuid import uuid4

from backend.services.toolrouter.documents import build_router_documents
from backend.services.toolrouter import fusion_ranker
from backend.services.toolrouter.fusion_ranker import rank_endpoint_scores


def _action(*, method: str, path: str, name: str, description: str, tags=None, parameters=None, request_body=None):
    return SimpleNamespace(
        id=uuid4(),
        method=method,
        path=path,
        name=name,
        description=description,
        parameters=parameters or [],
        request_body=request_body or {},
        responses={"200": {"description": "OK"}},
        security=[],
        tags=tags or [],
        risk_level="read",
        status="discovered",
        source_index="1",
    )


def _tool(action, *, name: str, schema=None):
    return SimpleNamespace(
        id=uuid4(),
        action_node_id=action.id,
        name=name,
        description=name,
        function_schema=schema or {"parameters": {"properties": {}, "required": []}},
        risk_level="read",
        status="active",
        requires_approval=False,
    )


def test_rank_endpoint_scores_prefers_matching_collection_read_endpoint():
    products = _action(
        method="GET",
        path="/store/products",
        name="listProducts",
        description="List products in the catalog.",
        tags=["Products"],
    )
    cart = _action(
        method="POST",
        path="/store/carts/{id}/line-items",
        name="addLineItem",
        description="Add a variant to a cart.",
        tags=["Cart"],
        request_body={"content": {"application/json": {"schema": {"properties": {"variant_id": {"type": "string"}}}}}},
    )
    docs = build_router_documents([(_tool(products, name="list_products"), products), (_tool(cart, name="add_line_item"), cart)])

    ranked = rank_endpoint_scores("list products", docs, min_score=0)

    assert ranked
    assert ranked[0].endpoint_key == str(products.id)
    assert ranked[0].score > ranked[1].score


def test_rank_endpoint_scores_uses_trigram_for_small_typos():
    sweatshirt = _action(
        method="GET",
        path="/catalog/sweatshirts/{id}",
        name="getSweatshirt",
        description="Read sweatshirt details and size options.",
        tags=["Sweatshirts"],
    )
    invoice = _action(
        method="GET",
        path="/billing/invoices",
        name="listInvoices",
        description="List invoices.",
        tags=["Invoices"],
    )
    docs = build_router_documents([(_tool(sweatshirt, name="get_sweatshirt"), sweatshirt), (_tool(invoice, name="list_invoices"), invoice)])

    ranked = rank_endpoint_scores("sweathshirt details", docs)

    assert ranked
    assert ranked[0].endpoint_key == str(sweatshirt.id)
    assert ranked[0].components["trigram"] > 0


def test_rank_endpoint_scores_drops_unrelated_low_confidence_queries():
    products = _action(
        method="GET",
        path="/store/products",
        name="listProducts",
        description="List products in the catalog.",
        tags=["Products"],
    )
    docs = build_router_documents([(_tool(products, name="list_products"), products)])

    assert rank_endpoint_scores("weather forecast tomorrow", docs) == []


def test_rank_generated_tools_rehydrates_only_indexed_active_catalog_rows():
    import inspect

    source = inspect.getsource(fusion_ranker.rank_generated_tools)

    assert "indexed_tool_ids" in source
    assert "GeneratedTool.id.in_(indexed_tool_ids)" in source
    assert "GeneratedTool.status == ToolStatus.active" in source
    assert "ActionNode.status != ActionNodeStatus.deprecated" in source
