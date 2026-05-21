from types import SimpleNamespace

from backend.services.toolrouter.adapter import ToolRouterAdapter, ToolRouterDecisionType


def _candidate(name: str, *, method: str = "GET", path: str = "/products", risk: str = "read", score: int = 4):
    return SimpleNamespace(
        tool=SimpleNamespace(name=name, risk_level=risk, requires_approval=False, function_schema={"parameters": {"required": []}}),
        action=SimpleNamespace(method=method, path=path, name=name, parameters=[]),
        connection=SimpleNamespace(name="Primary API"),
        score=score,
        reason=name,
    )


def _path_candidate(name: str, *, path: str, required: list[str], score: int = 4):
    return SimpleNamespace(
        tool=SimpleNamespace(
            name=name,
            risk_level="read",
            requires_approval=False,
            function_schema={"parameters": {"required": required}},
        ),
        action=SimpleNamespace(
            method="GET",
            path=path,
            name=name,
            parameters=[{"name": item, "in": "path", "required": True} for item in required],
        ),
        connection=SimpleNamespace(name="Primary API"),
        score=score,
        reason=name,
    )


def test_toolrouter_routes_single_read_candidate():
    decision = ToolRouterAdapter().decide(
        message="list products",
        candidates=[_candidate("listProducts")],
        inputs={},
        missing=[],
    )

    assert decision.type == ToolRouterDecisionType.ROUTE
    assert decision.selected.tool.name == "listProducts"


def test_toolrouter_shows_topk_when_candidates_are_ambiguous():
    decision = ToolRouterAdapter().decide(
        message="show orders",
        candidates=[_candidate("listOrders", score=5), _candidate("searchOrders", score=5)],
        inputs={},
        missing=[],
    )

    assert decision.type == ToolRouterDecisionType.SHOW_TOPK
    assert [candidate.tool.name for candidate in decision.candidates] == ["listOrders", "searchOrders"]


def test_toolrouter_routes_collection_when_item_route_has_same_score_but_needs_identifier():
    decision = ToolRouterAdapter().decide(
        message="what products do you have?",
        candidates=[
            _path_candidate("listproducts", path="/products", required=[], score=2),
            _path_candidate("getproduct", path="/products/{product_id}", required=["product_id"], score=2),
        ],
        inputs={},
        missing=[],
    )

    assert decision.type == ToolRouterDecisionType.ROUTE
    assert decision.selected.tool.name == "listproducts"


def test_toolrouter_asks_for_missing_parameters_before_routing():
    decision = ToolRouterAdapter().decide(
        message="get order",
        candidates=[_candidate("getOrder")],
        inputs={},
        missing=["order_id"],
    )

    assert decision.type == ToolRouterDecisionType.ASK_PARAM
    assert decision.missing == ["order_id"]


def test_toolrouter_asks_policy_for_write_actions():
    decision = ToolRouterAdapter().decide(
        message="create product",
        candidates=[_candidate("createProduct", method="POST", risk="write")],
        inputs={"title": "Hat"},
        missing=[],
    )

    assert decision.type == ToolRouterDecisionType.ASK_POLICY
    assert decision.selected.tool.name == "createProduct"


def test_toolrouter_blocks_unsafe_destructive_requests():
    decision = ToolRouterAdapter().decide(
        message="delete all customers",
        candidates=[_candidate("deleteCustomer", method="DELETE", risk="destructive")],
        inputs={},
        missing=[],
    )

    assert decision.type == ToolRouterDecisionType.BLOCK_UNSAFE
