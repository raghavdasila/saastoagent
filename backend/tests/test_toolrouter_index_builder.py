import inspect
from types import SimpleNamespace
from uuid import uuid4

import pytest

from backend.core.models import Base, ToolRouterDocument, ToolRouterIndex
from backend.services.toolrouter.documents import catalog_fingerprint
from backend.services.toolrouter import index_builder


def test_toolrouter_models_are_registered_in_metadata():
    assert "toolrouter_indexes" in Base.metadata.tables
    assert "toolrouter_documents" in Base.metadata.tables
    assert ToolRouterIndex.__tablename__ == "toolrouter_indexes"
    assert ToolRouterDocument.__tablename__ == "toolrouter_documents"


def test_build_router_index_payload_counts_dynamic_documents():
    action_id = uuid4()
    action = SimpleNamespace(
        id=action_id,
        method="GET",
        path="/inventory/items/{id}",
        name="getInventoryItem",
        description="Read an inventory item.",
        parameters=[{"name": "id", "in": "path", "required": True}],
        request_body={},
        responses={"200": {"description": "Inventory item"}},
        security=[],
        tags=["Inventory"],
        risk_level="read",
        status="discovered",
        source_index="1",
    )
    tool = SimpleNamespace(
        id=uuid4(),
        action_node_id=action_id,
        name="get_inventory_item",
        description="Read inventory item",
        function_schema={"parameters": {"properties": {"id": {"type": "string"}}, "required": ["id"]}},
        risk_level="read",
        status="active",
        requires_approval=False,
    )

    payload = index_builder.build_router_index_payload([(tool, action)])

    assert payload["router_version"] == index_builder.ROUTER_VERSION
    assert payload["document_count"] >= 4
    assert payload["endpoint_count"] == 1
    assert payload["stats"]["doc_kinds"]["endpoint"] == 1
    assert payload["stats"]["doc_kinds"]["parameter"] == 1
    assert len(payload["catalog_fingerprint"]) == 64


def test_load_catalog_rows_excludes_deprecated_actions_and_inactive_tools():
    source = inspect.getsource(index_builder._load_catalog_rows)

    assert "ActionNodeStatus.deprecated" in source
    assert "GeneratedTool.status == ToolStatus.active" in source


def test_build_reuses_existing_fingerprint_row_instead_of_duplicate_insert():
    build_source = inspect.getsource(index_builder.build_toolrouter_index_for_agent)
    lookup_source = inspect.getsource(index_builder._existing_index_for_fingerprint)

    assert "ToolRouterIndex.catalog_fingerprint == catalog_fingerprint" in lookup_source
    assert "_replace_index_documents" in build_source


@pytest.mark.asyncio
async def test_latest_ready_index_rejects_stale_catalog_fingerprint(monkeypatch):
    action, tool = _fingerprint_row()
    index = SimpleNamespace(catalog_fingerprint="stale-fingerprint")

    class FakeResult:
        def scalar_one_or_none(self):
            return index

    class FakeSession:
        async def execute(self, _query):
            return FakeResult()

    async def fake_load_catalog_rows(**_kwargs):
        return [(tool, action)]

    monkeypatch.setattr(index_builder, "_load_catalog_rows", fake_load_catalog_rows)

    assert await index_builder.latest_ready_index(session=FakeSession(), saas_agent_id=uuid4()) is None


@pytest.mark.asyncio
async def test_latest_ready_index_accepts_matching_catalog_fingerprint(monkeypatch):
    action, tool = _fingerprint_row()
    index = SimpleNamespace(catalog_fingerprint=catalog_fingerprint([(tool, action)]))

    class FakeResult:
        def scalar_one_or_none(self):
            return index

    class FakeSession:
        async def execute(self, _query):
            return FakeResult()

    async def fake_load_catalog_rows(**_kwargs):
        return [(tool, action)]

    monkeypatch.setattr(index_builder, "_load_catalog_rows", fake_load_catalog_rows)

    assert await index_builder.latest_ready_index(session=FakeSession(), saas_agent_id=uuid4()) is index


def _fingerprint_row():
    action_id = uuid4()
    action = SimpleNamespace(
        id=action_id,
        method="GET",
        path="/inventory/items",
        name="listInventoryItems",
        description="List inventory items.",
        parameters=[],
        request_body={},
        responses={"200": {"description": "OK"}},
        security=[],
        tags=["Inventory"],
        risk_level="read",
        status="discovered",
        source_index="1",
    )
    tool = SimpleNamespace(
        id=uuid4(),
        action_node_id=action_id,
        name="list_inventory_items",
        description="List inventory items",
        function_schema={"parameters": {"properties": {}, "required": []}},
        risk_level="read",
        status="active",
        requires_approval=False,
    )
    return action, tool
