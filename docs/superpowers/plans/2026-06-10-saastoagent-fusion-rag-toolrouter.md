# SaaStoAgent Fusion RAG ToolRouter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace SaaStoAgent v0.1's weak generated-tool token overlap router with a setup-time, per-SaaS-Agent fusion RAG ToolRouter built from each arbitrary OpenAPI collection.

**Architecture:** Activation builds a durable per-agent router index after `ActionNode` and `GeneratedTool` rows are generated. Runtime candidate selection loads the ready index and applies fused lexical, BM25, schema/parameter, graph, and trigram signals while returning the existing `ToolCandidate` shape to the current input-binding, approval, safety, execution, RouteDeck, and public-chat paths.

**Tech Stack:** Python, FastAPI, SQLAlchemy async, PostgreSQL 17, pg_trgm, Postgres full-text search, JSONB, React/Vite, existing SaaStoAgent RouteDeck/Corpus UI.

---

## Product And Acceptance Criteria

### Scope

- Directly replace the existing `find_tool_candidates()` scoring internals in `backend/services/agent/rest_operator.py`.
- Build router artifacts only during API setup/catalog activation, not during normal agent usage.
- Support arbitrary OpenAPI collections: no static endpoint maps, Medusa-specific routing rules, or hand-authored API corpora.
- Preserve the current `ToolCandidate` contract and all downstream safety/execution behavior.
- Keep dense embeddings out of this first slice. `pgvector` remains available for a later dense-fusion slice.

### Runtime Acceptance

- `find_tool_candidates()` uses the prebuilt fusion router index as the normal path.
- The old overlap scorer is not used as a fallback for normal behavior.
- If the router index is missing, stale, blocked, or not ready, candidate search returns no generated-tool candidates and records a bounded diagnostic reason. It must not build the index during that chat turn.
- Missing-param handling, approval handling, public-safe response shaping, trace creation, learning candidate creation, and execution-frame continuation continue to use existing code.
- Candidate summaries on traces include fused score metadata bounded to safe fields: `score`, `reason`, and per-signal scores. They must not include credentials, auth header values, raw visitor tokens, or large schema payloads.

### Setup-Time Acceptance

- Activating an arbitrary API collection creates:
  - `ActionNode` rows.
  - `GeneratedTool` rows.
  - A ready `ToolRouterIndex` row for that `saas_agent_id`.
  - `ToolRouterDocument` rows for endpoint, parameter, request/body, response, auth/security, and graph/resource docs.
- The router index has a deterministic catalog fingerprint. Re-activating unchanged catalog data should reuse or replace the index without creating duplicate ready indexes.
- Changing the OpenAPI collection, generated action rows, generated tool rows, request schemas, parameters, auth, or responses changes the fingerprint and rebuilds the router index during activation.

### UI Acceptance

- In the older owner setup surface `frontend/src/components/saasAgent/ConnectSetupView.tsx`, after "Save and activate", the activation log visibly includes a router index step, for example:
  - `step: Building fusion router index`
  - `step: Fusion router index ready`
  - doc/action/tool counts
- In the RouteDeck/Corpus app graph catalog surface `frontend/src/components/appGraph/corpusSurfaces.tsx`, the Catalog panel visibly shows router readiness, for example:
  - `Router index: Ready`
  - router docs count
  - router version
- From `context.md` current app setup, the acceptance route is:
  - `http://localhost:3007/app/home`
  - open or create a SaaS Agent
  - save and activate a REST API
  - inspect Catalog/Actions
  - submit an execution goal
  - public deployed chat at `/a/{slug}` still avoids endpoint/auth/internal leakage
- The UI must not render raw endpoint paths, trace ids, auth header names/values, or credential material in public visitor chat. Owner-only catalog/debug surfaces may show method/path because they already do today.

### Behavioral Acceptance Queries

Use fixture agents with small arbitrary OpenAPI specs, not Medusa-only hardcoding.

- Query: `list products`
  - Expected top candidate: GET collection/list/search products endpoint.
  - Must not ask for connection-level auth headers.
- Query: `just list the product names we sell`
  - Expected public-safe read behavior, not a clarification asking for publishable key headers.
- Query: `add the L size to cart`
  - Expected top candidate after prior product context: line-item/add-to-cart style write endpoint.
  - Existing approval/domain-policy behavior remains authoritative.
- Query: `delete all customers`
  - Expected: existing unsafe/bulk destructive protection still blocks or requires policy through `ToolRouterAdapter`.
- Query: typo/partial identifier such as `sweathshirt details`
  - Expected: trigram/schema/resource signals help retrieve the closest product/read endpoint when the API catalog supports it.

### Validation Commands

Run from `D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1`:

```powershell
python -m pytest backend/tests/test_toolrouter_documents.py backend/tests/test_toolrouter_index_builder.py backend/tests/test_toolrouter_fusion_ranker.py backend/tests/test_toolrouter_activation.py backend/tests/test_rest_catalog.py backend/tests/test_toolrouter_adapter.py backend/tests/test_api_orchestration.py backend/tests/test_execution_frames.py -q
```

```powershell
cd frontend
npm run type-check
```

For live UI acceptance:

```powershell
docker compose up --build
```

Then verify:

```text
http://localhost:3007/app/home
http://localhost:8085/api/health
```

---

## File Structure

### Create

- `backend/core/models/toolrouter.py`
  - SQLAlchemy models for setup-time router index manifests and router documents.
- `backend/services/toolrouter/documents.py`
  - Dynamic document and graph-ish artifact generation from `ActionNode` and `GeneratedTool` rows.
- `backend/services/toolrouter/index_builder.py`
  - Setup-time build/rebuild service and catalog fingerprinting.
- `backend/services/toolrouter/fusion_ranker.py`
  - Runtime scoring over prebuilt index artifacts and DB documents.
- `backend/tests/test_toolrouter_documents.py`
  - Unit tests for dynamic doc generation.
- `backend/tests/test_toolrouter_index_builder.py`
  - Unit tests for fingerprinting and index build behavior.
- `backend/tests/test_toolrouter_fusion_ranker.py`
  - Unit tests for direct replacement ranking behavior.
- `backend/tests/test_toolrouter_activation.py`
  - Activation-service test coverage for setup-time router index event and readiness.

### Modify

- `backend/core/database.py`
  - Enable `pg_trgm` and create expression indexes for FTS/trigram search.
- `backend/core/models/__init__.py`
  - Export the new router index/document models.
- `backend/services/discovery/activation.py`
  - Build router index after generated tools and before activation completes.
- `backend/services/toolrouter/__init__.py`
  - Export index builder/ranker entrypoints.
- `backend/services/agent/rest_operator.py`
  - Replace current candidate scoring with fusion ranker call while preserving `ToolCandidate`.
- `backend/services/app_graph/runtime.py`
  - Include router index readiness in catalog activation graph context.
- `backend/services/app_graph/corpus_surfaces.py`
  - Add router readiness data to the Catalog surface props.
- `backend/services/catalog.py`
  - Include router index status/counts in catalog payloads if useful for owner surfaces.
- `frontend/src/components/saasAgent/ConnectSetupView.tsx`
  - Render the router index activation step in the setup log.
- `frontend/src/components/appGraph/corpusSurfaces.tsx`
  - Render router index readiness in the Catalog surface.
- `architecture/code-map.md`
  - Add `backend/services/toolrouter/**/*.py` and router index tests to the proper subsystem rows.
- `architecture/components/openapi-provider-discovery.md`
  - Document setup-time router index build as part of activation.
- `architecture/components/deployed-agent-orchestration.md`
  - Document direct replacement candidate ranking boundary.
- `SYSTEM_FLOW_INDEX.md`
  - Update only if implementation changes the visible setup/execution flow wording.

---

### Task 1: Add Router Index Persistence And Postgres Extensions

**Files:**
- Create: `backend/core/models/toolrouter.py`
- Modify: `backend/core/models/__init__.py`
- Modify: `backend/core/database.py`
- Test: `backend/tests/test_toolrouter_index_builder.py`

- [ ] **Step 1: Write the model metadata test**

Create `backend/tests/test_toolrouter_index_builder.py` with this initial test:

```python
from backend.core.models import Base, ToolRouterDocument, ToolRouterIndex


def test_toolrouter_models_are_registered_in_metadata():
    assert "toolrouter_indexes" in Base.metadata.tables
    assert "toolrouter_documents" in Base.metadata.tables
    assert ToolRouterIndex.__tablename__ == "toolrouter_indexes"
    assert ToolRouterDocument.__tablename__ == "toolrouter_documents"
```

- [ ] **Step 2: Run the focused failing test**

Run:

```powershell
python -m pytest backend/tests/test_toolrouter_index_builder.py::test_toolrouter_models_are_registered_in_metadata -q
```

Expected: FAIL because `ToolRouterIndex` and `ToolRouterDocument` do not exist yet.

- [ ] **Step 3: Create the SQLAlchemy models**

Create `backend/core/models/toolrouter.py`:

```python
from __future__ import annotations

import enum
import uuid as uuid_pkg

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import Base


class ToolRouterIndexStatus(str, enum.Enum):
    building = "building"
    ready = "ready"
    blocked = "blocked"
    stale = "stale"


class ToolRouterIndex(Base):
    __tablename__ = "toolrouter_indexes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    saas_agent_id = Column(UUID(as_uuid=True), ForeignKey("saas_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    router_version = Column(String(80), nullable=False)
    catalog_fingerprint = Column(String(128), nullable=False)
    status = Column(Enum(ToolRouterIndexStatus, name="sta_v01_toolrouter_index_status", create_constraint=False), nullable=False, default=ToolRouterIndexStatus.building)
    document_count = Column(Integer, nullable=False, default=0)
    endpoint_count = Column(Integer, nullable=False, default=0)
    stats = Column(JSONB, nullable=False, default=dict)
    error = Column(Text, nullable=True)
    built_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    documents = relationship("ToolRouterDocument", back_populates="index", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("saas_agent_id", "router_version", "catalog_fingerprint", name="uq_sta_v01_toolrouter_index_fingerprint"),
        Index("ix_toolrouter_indexes_agent_ready", "saas_agent_id", "router_version", "status"),
    )


class ToolRouterDocument(Base):
    __tablename__ = "toolrouter_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid_pkg.uuid4)
    index_id = Column(UUID(as_uuid=True), ForeignKey("toolrouter_indexes.id", ondelete="CASCADE"), nullable=False, index=True)
    saas_agent_id = Column(UUID(as_uuid=True), ForeignKey("saas_agents.id", ondelete="CASCADE"), nullable=False, index=True)
    action_node_id = Column(UUID(as_uuid=True), ForeignKey("action_nodes.id", ondelete="CASCADE"), nullable=False, index=True)
    generated_tool_id = Column(UUID(as_uuid=True), ForeignKey("generated_tools.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint_key = Column(String(160), nullable=False, index=True)
    doc_kind = Column(String(40), nullable=False, index=True)
    search_text = Column(Text, nullable=False)
    tokens = Column(JSONB, nullable=False, default=list)
    graph_refs = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    index = relationship("ToolRouterIndex", back_populates="documents")

    __table_args__ = (
        Index("ix_toolrouter_documents_agent_kind", "saas_agent_id", "doc_kind"),
        Index("ix_toolrouter_documents_endpoint", "index_id", "endpoint_key"),
    )
```

- [ ] **Step 4: Export the models**

Modify `backend/core/models/__init__.py`:

```python
from .toolrouter import ToolRouterDocument, ToolRouterIndex, ToolRouterIndexStatus
```

Add these names to `__all__`:

```python
"ToolRouterIndex",
"ToolRouterDocument",
"ToolRouterIndexStatus",
```

- [ ] **Step 5: Enable Postgres search extensions and indexes**

Modify `backend/core/database.py` in `create_tables()`:

```python
await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
await conn.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
```

After `await conn.run_sync(Base.metadata.create_all)`, add:

```python
await conn.execute(
    text(
        """
        CREATE INDEX IF NOT EXISTS ix_toolrouter_documents_search_text_fts
        ON toolrouter_documents
        USING GIN (to_tsvector('simple', search_text))
        """
    )
)
await conn.execute(
    text(
        """
        CREATE INDEX IF NOT EXISTS ix_toolrouter_documents_search_text_trgm
        ON toolrouter_documents
        USING GIN (search_text gin_trgm_ops)
        """
    )
)
```

- [ ] **Step 6: Run the model test**

Run:

```powershell
python -m pytest backend/tests/test_toolrouter_index_builder.py::test_toolrouter_models_are_registered_in_metadata -q
```

Expected: PASS.

---

### Task 2: Build Dynamic Router Documents From Current Catalog Rows

**Files:**
- Create: `backend/services/toolrouter/documents.py`
- Test: `backend/tests/test_toolrouter_documents.py`

- [ ] **Step 1: Write dynamic document tests**

Create `backend/tests/test_toolrouter_documents.py`:

```python
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
```

- [ ] **Step 2: Run failing tests**

Run:

```powershell
python -m pytest backend/tests/test_toolrouter_documents.py -q
```

Expected: FAIL because `documents.py` does not exist.

- [ ] **Step 3: Implement document generation**

Create `backend/services/toolrouter/documents.py`:

```python
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Iterable

_TOKEN_RE = re.compile(r"[a-z0-9_/-]+", re.IGNORECASE)


@dataclass(frozen=True)
class RouterDocument:
    action_node_id: Any
    generated_tool_id: Any
    endpoint_key: str
    doc_kind: str
    search_text: str
    tokens: list[str]
    graph_refs: dict[str, list[str]]


def tokenize(value: str) -> list[str]:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value or "")
    normalized = re.sub(r"[_/.-]+", " ", normalized)
    tokens: list[str] = []
    for raw in _TOKEN_RE.findall(normalized):
        token = raw.lower().strip("_-/")
        if len(token) <= 1:
            continue
        tokens.append(token)
        if token.endswith("s") and len(token) > 3:
            tokens.append(token[:-1])
    return list(dict.fromkeys(tokens))


def endpoint_key_for(action: Any) -> str:
    return f"{getattr(action, 'method', '')}:{getattr(action, 'path', '')}:{getattr(action, 'id', '')}"


def build_router_documents(rows: Iterable[tuple[Any, Any]]) -> list[RouterDocument]:
    docs: list[RouterDocument] = []
    for tool, action in rows:
        endpoint_key = endpoint_key_for(action)
        common_refs = _graph_refs(action, tool)
        docs.append(_doc(action, tool, endpoint_key, "endpoint", _endpoint_text(action, tool), common_refs))
        for parameter in getattr(action, "parameters", None) or []:
            if isinstance(parameter, dict):
                docs.append(_doc(action, tool, endpoint_key, "parameter", _parameter_text(action, parameter), common_refs))
        request_text = _request_text(action, tool)
        if request_text:
            docs.append(_doc(action, tool, endpoint_key, "request", request_text, common_refs))
        response_text = _response_text(action)
        if response_text:
            docs.append(_doc(action, tool, endpoint_key, "response", response_text, common_refs))
        auth_text = _auth_text(action)
        if auth_text:
            docs.append(_doc(action, tool, endpoint_key, "auth", auth_text, common_refs))
        docs.append(_doc(action, tool, endpoint_key, "graph", _graph_text(action, tool, common_refs), common_refs))
    return docs


def catalog_fingerprint(rows: Iterable[tuple[Any, Any]]) -> str:
    payload = []
    for tool, action in rows:
        payload.append(
            {
                "action_id": str(getattr(action, "id", "")),
                "tool_id": str(getattr(tool, "id", "")),
                "method": getattr(action, "method", ""),
                "path": getattr(action, "path", ""),
                "action_name": getattr(action, "name", ""),
                "tool_name": getattr(tool, "name", ""),
                "description": getattr(action, "description", ""),
                "parameters": getattr(action, "parameters", None) or [],
                "request_body": getattr(action, "request_body", None) or {},
                "responses": getattr(action, "responses", None) or {},
                "security": getattr(action, "security", None) or [],
                "tags": getattr(action, "tags", None) or [],
                "function_schema": getattr(tool, "function_schema", None) or {},
            }
        )
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _doc(action: Any, tool: Any, endpoint_key: str, kind: str, text: str, refs: dict[str, list[str]]) -> RouterDocument:
    return RouterDocument(
        action_node_id=getattr(action, "id"),
        generated_tool_id=getattr(tool, "id"),
        endpoint_key=endpoint_key,
        doc_kind=kind,
        search_text=" ".join(str(text).split()),
        tokens=tokenize(text),
        graph_refs=refs,
    )


def _endpoint_text(action: Any, tool: Any) -> str:
    return " ".join(
        [
            "endpoint",
            str(getattr(action, "method", "") or ""),
            str(getattr(action, "path", "") or ""),
            str(getattr(action, "name", "") or ""),
            str(getattr(tool, "name", "") or ""),
            str(getattr(action, "description", "") or ""),
            str(getattr(tool, "description", "") or ""),
            "tags",
            " ".join(str(tag) for tag in (getattr(action, "tags", None) or [])),
        ]
    )


def _parameter_text(action: Any, parameter: dict[str, Any]) -> str:
    return " ".join(
        [
            str(getattr(action, "method", "") or ""),
            str(getattr(action, "path", "") or ""),
            "parameter",
            str(parameter.get("in") or "param"),
            str(parameter.get("name") or ""),
            "required" if parameter.get("required") else "optional",
            str(parameter.get("description") or ""),
            json.dumps(parameter.get("schema") or {}, sort_keys=True, default=str),
        ]
    )


def _request_text(action: Any, tool: Any) -> str:
    return " ".join(
        [
            str(getattr(action, "method", "") or ""),
            str(getattr(action, "path", "") or ""),
            "request body schema",
            json.dumps(getattr(action, "request_body", None) or {}, sort_keys=True, default=str),
            json.dumps(getattr(tool, "function_schema", None) or {}, sort_keys=True, default=str),
        ]
    ).strip()


def _response_text(action: Any) -> str:
    responses = getattr(action, "responses", None) or {}
    return f"{getattr(action, 'method', '')} {getattr(action, 'path', '')} response schema {json.dumps(responses, sort_keys=True, default=str)}" if responses else ""


def _auth_text(action: Any) -> str:
    security = getattr(action, "security", None) or []
    return f"{getattr(action, 'method', '')} {getattr(action, 'path', '')} auth security {json.dumps(security, sort_keys=True, default=str)}" if security else ""


def _graph_text(action: Any, tool: Any, refs: dict[str, list[str]]) -> str:
    return " ".join(
        [
            "graph",
            str(getattr(action, "method", "") or ""),
            str(getattr(action, "path", "") or ""),
            str(getattr(action, "name", "") or ""),
            str(getattr(tool, "name", "") or ""),
            " ".join(f"resource {item}" for item in refs.get("resources", [])),
            " ".join(f"param {item}" for item in refs.get("params", [])),
            " ".join(f"tag {item}" for item in refs.get("tags", [])),
            " ".join(f"auth {item}" for item in refs.get("auth", [])),
        ]
    )


def _graph_refs(action: Any, tool: Any) -> dict[str, list[str]]:
    del tool
    path = str(getattr(action, "path", "") or "")
    resources = [
        _singular(part)
        for part in path.split("/")
        if part and not part.startswith("{") and not part.endswith("}")
    ]
    parameters = [
        str(parameter.get("name"))
        for parameter in (getattr(action, "parameters", None) or [])
        if isinstance(parameter, dict) and parameter.get("name")
    ]
    security = []
    for item in getattr(action, "security", None) or []:
        if isinstance(item, dict):
            security.extend(str(key) for key in item.keys())
        else:
            security.append(str(item))
    return {
        "method": [str(getattr(action, "method", "") or "").upper()],
        "resources": list(dict.fromkeys(resources)),
        "params": list(dict.fromkeys(parameters)),
        "tags": [str(tag) for tag in (getattr(action, "tags", None) or [])],
        "auth": list(dict.fromkeys(security)),
    }


def _singular(value: str) -> str:
    return value[:-1] if value.endswith("s") and len(value) > 3 else value
```

- [ ] **Step 4: Run document tests**

Run:

```powershell
python -m pytest backend/tests/test_toolrouter_documents.py -q
```

Expected: PASS.

---

### Task 3: Build Router Index During Activation

**Files:**
- Create: `backend/services/toolrouter/index_builder.py`
- Modify: `backend/services/discovery/activation.py`
- Modify: `backend/services/toolrouter/__init__.py`
- Test: `backend/tests/test_toolrouter_index_builder.py`
- Test: `backend/tests/test_toolrouter_activation.py`

- [ ] **Step 1: Add index-builder unit tests**

Append to `backend/tests/test_toolrouter_index_builder.py`:

```python
from types import SimpleNamespace
from uuid import uuid4

from backend.services.toolrouter.index_builder import ROUTER_VERSION, router_index_stats
from backend.services.toolrouter.documents import build_router_documents


def test_router_index_stats_count_docs_and_endpoint_kinds():
    action_id = uuid4()
    tool_id = uuid4()
    action = SimpleNamespace(
        id=action_id,
        method="GET",
        path="/inventory/products",
        name="listProducts",
        description="List inventory products",
        parameters=[],
        request_body={},
        responses={"200": {"description": "OK"}},
        security=[],
        tags=["inventory"],
    )
    tool = SimpleNamespace(
        id=tool_id,
        action_node_id=action_id,
        name="get_inventory_products",
        description="List products",
        function_schema={"parameters": {"properties": {}, "required": []}},
    )

    stats = router_index_stats(build_router_documents([(tool, action)]))

    assert stats["router_version"] == ROUTER_VERSION
    assert stats["document_count"] >= 3
    assert stats["endpoint_count"] == 1
    assert stats["doc_kinds"]["endpoint"] == 1
```

- [ ] **Step 2: Run failing index-builder tests**

Run:

```powershell
python -m pytest backend/tests/test_toolrouter_index_builder.py -q
```

Expected: FAIL because `index_builder.py` does not exist.

- [ ] **Step 3: Implement index builder**

Create `backend/services/toolrouter/index_builder.py`:

```python
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.models import ActionNode, Connection, GeneratedTool, ToolRouterDocument, ToolRouterIndex, ToolRouterIndexStatus
from backend.services.toolrouter.documents import RouterDocument, build_router_documents, catalog_fingerprint

ROUTER_VERSION = "fusion_rag_v1"


def router_index_stats(documents: list[RouterDocument]) -> dict[str, Any]:
    return {
        "router_version": ROUTER_VERSION,
        "document_count": len(documents),
        "endpoint_count": len({doc.endpoint_key for doc in documents}),
        "doc_kinds": dict(Counter(doc.doc_kind for doc in documents)),
        "token_count": sum(len(doc.tokens) for doc in documents),
    }


async def build_toolrouter_index_for_agent(
    *,
    saas_agent_id: uuid.UUID,
    session: AsyncSession,
) -> ToolRouterIndex:
    rows = (
        await session.execute(
            select(GeneratedTool, ActionNode)
            .join(ActionNode, GeneratedTool.action_node_id == ActionNode.id)
            .join(Connection, GeneratedTool.connection_id == Connection.id)
            .where(GeneratedTool.saas_agent_id == saas_agent_id)
            .order_by(Connection.name, ActionNode.path, ActionNode.method, GeneratedTool.name)
        )
    ).all()
    fingerprint = catalog_fingerprint(rows)
    documents = build_router_documents(rows)
    stats = router_index_stats(documents)

    await session.execute(
        delete(ToolRouterDocument).where(ToolRouterDocument.saas_agent_id == saas_agent_id)
    )
    await session.execute(
        delete(ToolRouterIndex).where(
            ToolRouterIndex.saas_agent_id == saas_agent_id,
            ToolRouterIndex.router_version == ROUTER_VERSION,
        )
    )
    index = ToolRouterIndex(
        saas_agent_id=saas_agent_id,
        router_version=ROUTER_VERSION,
        catalog_fingerprint=fingerprint,
        status=ToolRouterIndexStatus.ready,
        document_count=len(documents),
        endpoint_count=stats["endpoint_count"],
        stats=stats,
        built_at=datetime.now(timezone.utc),
    )
    session.add(index)
    await session.flush()
    for doc in documents:
        session.add(
            ToolRouterDocument(
                index_id=index.id,
                saas_agent_id=saas_agent_id,
                action_node_id=doc.action_node_id,
                generated_tool_id=doc.generated_tool_id,
                endpoint_key=doc.endpoint_key,
                doc_kind=doc.doc_kind,
                search_text=doc.search_text,
                tokens=doc.tokens,
                graph_refs=doc.graph_refs,
            )
        )
    await session.flush()
    return index
```

- [ ] **Step 4: Export builder entrypoints**

Modify `backend/services/toolrouter/__init__.py`:

```python
from .adapter import ToolRouterAdapter, ToolRouterDecision, ToolRouterDecisionType
from .index_builder import ROUTER_VERSION, build_toolrouter_index_for_agent

__all__ = [
    "ROUTER_VERSION",
    "ToolRouterAdapter",
    "ToolRouterDecision",
    "ToolRouterDecisionType",
    "build_toolrouter_index_for_agent",
]
```

- [ ] **Step 5: Add activation event test**

Create `backend/tests/test_toolrouter_activation.py`:

```python
import inspect

from backend.services.discovery.activation import ActivationService


def test_activation_builds_fusion_router_index_before_ready():
    source = inspect.getsource(ActivationService.activate)

    assert "build_toolrouter_index_for_agent" in source
    assert '"router_index"' in source
    assert source.index("generate_tools_for_connection") < source.index("build_toolrouter_index_for_agent")
    assert source.index("build_toolrouter_index_for_agent") < source.index("ActivationOverallStatus.ready")
```

- [ ] **Step 6: Wire builder into activation**

Modify `backend/services/discovery/activation.py` imports:

```python
from backend.services.toolrouter import build_toolrouter_index_for_agent
```

After `generate_tools_for_connection(...)` succeeds and before setting `overall_status = ready`, insert:

```python
yield {
    "type": "step",
    "step": "router_index",
    "status": "running",
    "message": "Building fusion router index",
}
router_index = await build_toolrouter_index_for_agent(saas_agent_id=saas_agent_id, session=session)
yield {
    "type": "step",
    "step": "router_index",
    "status": "done",
    "message": "Fusion router index ready",
    "router_version": router_index.router_version,
    "router_documents_count": router_index.document_count,
    "router_endpoint_count": router_index.endpoint_count,
    "catalog_fingerprint": router_index.catalog_fingerprint[:12],
}
```

Then keep the existing generated catalog RAG step after the router index step.

- [ ] **Step 7: Run activation/index tests**

Run:

```powershell
python -m pytest backend/tests/test_toolrouter_index_builder.py backend/tests/test_toolrouter_activation.py -q
```

Expected: PASS.

---

### Task 4: Implement Fusion Ranker Over Prebuilt Index Artifacts

**Files:**
- Create: `backend/services/toolrouter/fusion_ranker.py`
- Test: `backend/tests/test_toolrouter_fusion_ranker.py`

- [ ] **Step 1: Write ranker tests**

Create `backend/tests/test_toolrouter_fusion_ranker.py`:

```python
from types import SimpleNamespace
from uuid import uuid4

from backend.services.toolrouter.fusion_ranker import fused_scores_from_documents


def _doc(kind, endpoint, text, refs=None):
    return SimpleNamespace(
        doc_kind=kind,
        endpoint_key=endpoint,
        search_text=text,
        tokens=text.lower().replace("-", " ").replace("/", " ").split(),
        graph_refs=refs or {},
    )


def test_fusion_ranker_prefers_collection_read_for_list_query():
    docs = [
        _doc("endpoint", "GET:/store/products:1", "GET /store/products list products retrieve product catalog", {"method": ["GET"], "resources": ["store", "product"]}),
        _doc("endpoint", "POST:/store/carts/{id}/line-items:2", "POST add product variant line item to cart", {"method": ["POST"], "resources": ["store", "cart", "line-item"]}),
        _doc("parameter", "POST:/store/carts/{id}/line-items:2", "parameter id variant_id quantity required"),
    ]

    scores = fused_scores_from_documents("just list the product names we sell", docs)

    assert scores["GET:/store/products:1"]["score"] > scores["POST:/store/carts/{id}/line-items:2"]["score"]
    assert "rag_all_max" in scores["GET:/store/products:1"]["components"]


def test_fusion_ranker_uses_trigram_for_typos():
    docs = [
        _doc("endpoint", "GET:/store/products/{id}:1", "GET /store/products/{id} get product details sweatshirt products", {"method": ["GET"], "resources": ["store", "product"]}),
        _doc("endpoint", "GET:/store/carts:2", "GET /store/carts retrieve carts", {"method": ["GET"], "resources": ["store", "cart"]}),
    ]

    scores = fused_scores_from_documents("sweathshirt details", docs)

    assert scores["GET:/store/products/{id}:1"]["score"] > scores["GET:/store/carts:2"]["score"]
    assert scores["GET:/store/products/{id}:1"]["components"]["trigram"] > 0


def test_fusion_ranker_boosts_schema_param_for_required_input_query():
    docs = [
        _doc("endpoint", "POST:/store/carts/{id}/line-items:1", "POST add line item to cart", {"method": ["POST"], "resources": ["store", "cart", "line-item"]}),
        _doc("parameter", "POST:/store/carts/{id}/line-items:1", "variant_id quantity required line item size"),
        _doc("endpoint", "GET:/store/products:2", "GET list products", {"method": ["GET"], "resources": ["store", "product"]}),
    ]

    scores = fused_scores_from_documents("add L size to cart", docs)

    assert scores["POST:/store/carts/{id}/line-items:1"]["components"]["schema_param"] > 0
```

- [ ] **Step 2: Run failing ranker tests**

Run:

```powershell
python -m pytest backend/tests/test_toolrouter_fusion_ranker.py -q
```

Expected: FAIL because `fusion_ranker.py` does not exist.

- [ ] **Step 3: Implement fusion scoring helpers**

Create `backend/services/toolrouter/fusion_ranker.py`:

```python
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from math import log
from typing import Any, Iterable

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.core.models import ActionNode, Connection, GeneratedTool, ToolRouterDocument, ToolRouterIndex, ToolRouterIndexStatus
from backend.services.toolrouter.documents import tokenize
from backend.services.toolrouter.index_builder import ROUTER_VERSION

PRODUCT_SCORE_WEIGHTS = {
    "rag_all_max": 0.30,
    "bm25_all_max": 0.20,
    "grag_expand": 0.20,
    "grag_rerank": 0.10,
    "grag_constrained": 0.10,
    "graph_sparse": 0.05,
    "schema_param": 0.05,
    "trigram": 0.05,
}


@dataclass(frozen=True)
class RankedToolRow:
    tool: GeneratedTool
    action: ActionNode
    connection: Connection
    score: int
    reason: str


def fused_scores_from_documents(query: str, documents: Iterable[Any]) -> dict[str, dict[str, Any]]:
    docs = list(documents)
    query_tokens = tokenize(query)
    endpoint_docs: dict[str, list[Any]] = defaultdict(list)
    for doc in docs:
        endpoint_docs[str(doc.endpoint_key)].append(doc)
    doc_freq = _document_frequency(docs)
    all_scores: dict[str, dict[str, Any]] = {}
    for endpoint_key, endpoint_group in endpoint_docs.items():
        components = {
            "rag_all_max": max((_tfidf_like(query_tokens, doc, doc_freq, len(docs)) for doc in endpoint_group), default=0.0),
            "bm25_all_max": max((_bm25(query_tokens, doc, doc_freq, docs) for doc in endpoint_group), default=0.0),
            "schema_param": max((_tfidf_like(query_tokens, doc, doc_freq, len(docs)) for doc in endpoint_group if str(doc.doc_kind) in {"parameter", "request", "response", "auth"}), default=0.0),
            "grag_expand": _graph_expand(query_tokens, endpoint_group),
            "grag_rerank": _graph_rerank(query_tokens, endpoint_group),
            "grag_constrained": _graph_constrained(query_tokens, endpoint_group),
            "graph_sparse": _graph_sparse(query_tokens, endpoint_group),
            "trigram": max((_trigram_similarity(query, str(doc.search_text)) for doc in endpoint_group), default=0.0),
        }
        score = sum(PRODUCT_SCORE_WEIGHTS[name] * components.get(name, 0.0) for name in PRODUCT_SCORE_WEIGHTS)
        all_scores[endpoint_key] = {
            "score": score,
            "components": components,
            "reason": _reason(components),
        }
    return _normalize_endpoint_scores(all_scores)


async def rank_generated_tools(
    *,
    message: str,
    saas_agent_id,
    db: AsyncSession,
    limit: int = 5,
) -> list[RankedToolRow]:
    index = await _ready_index(db, saas_agent_id)
    if index is None:
        return []
    doc_rows = (
        await db.execute(
            select(ToolRouterDocument).where(ToolRouterDocument.index_id == index.id)
        )
    ).scalars().all()
    fused = fused_scores_from_documents(message, doc_rows)
    endpoint_keys = [key for key, _payload in sorted(fused.items(), key=lambda item: item[1]["score"], reverse=True)]
    if not endpoint_keys:
        return []
    rows = (
        await db.execute(
            select(GeneratedTool, ActionNode, Connection)
            .join(ActionNode, GeneratedTool.action_node_id == ActionNode.id)
            .join(Connection, GeneratedTool.connection_id == Connection.id)
            .options(selectinload(Connection.credentials))
            .where(GeneratedTool.saas_agent_id == saas_agent_id)
        )
    ).all()
    by_key = {f"{action.method}:{action.path}:{action.id}": (tool, action, connection) for tool, action, connection in rows}
    ranked: list[RankedToolRow] = []
    for endpoint_key in endpoint_keys:
        match = by_key.get(endpoint_key)
        if match is None:
            continue
        payload = fused[endpoint_key]
        score = max(1, int(round(float(payload["score"]) * 100)))
        tool, action, connection = match
        ranked.append(
            RankedToolRow(
                tool=tool,
                action=action,
                connection=connection,
                score=score,
                reason=str(payload["reason"]),
            )
        )
    return ranked[:limit]


async def _ready_index(db: AsyncSession, saas_agent_id) -> ToolRouterIndex | None:
    result = await db.execute(
        select(ToolRouterIndex)
        .where(
            ToolRouterIndex.saas_agent_id == saas_agent_id,
            ToolRouterIndex.router_version == ROUTER_VERSION,
            ToolRouterIndex.status == ToolRouterIndexStatus.ready,
        )
        .order_by(ToolRouterIndex.built_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def _document_frequency(docs: list[Any]) -> Counter[str]:
    freq: Counter[str] = Counter()
    for doc in docs:
        freq.update(set(str(token) for token in (getattr(doc, "tokens", None) or [])))
    return freq


def _tfidf_like(query_tokens: list[str], doc: Any, doc_freq: Counter[str], total_docs: int) -> float:
    tokens = list(getattr(doc, "tokens", None) or [])
    if not query_tokens or not tokens:
        return 0.0
    counts = Counter(tokens)
    score = 0.0
    for token in query_tokens:
        if token not in counts:
            continue
        idf = log((1 + total_docs) / (1 + doc_freq[token])) + 1.0
        score += counts[token] * idf
    return min(1.0, score / max(4.0, len(query_tokens)))


def _bm25(query_tokens: list[str], doc: Any, doc_freq: Counter[str], docs: list[Any], *, k1: float = 1.2, b: float = 0.75) -> float:
    tokens = list(getattr(doc, "tokens", None) or [])
    if not query_tokens or not tokens:
        return 0.0
    counts = Counter(tokens)
    avg_len = sum(len(getattr(item, "tokens", None) or []) for item in docs) / max(1, len(docs))
    score = 0.0
    for token in query_tokens:
        tf = counts[token]
        if not tf:
            continue
        df = max(1, doc_freq[token])
        idf = log(1 + ((len(docs) - df + 0.5) / (df + 0.5)))
        denom = tf + k1 * (1 - b + b * (len(tokens) / max(avg_len, 1.0)))
        score += idf * ((tf * (k1 + 1)) / denom)
    return min(1.0, score / max(2.0, len(query_tokens)))


def _graph_expand(query_tokens: list[str], docs: list[Any]) -> float:
    refs = _merged_refs(docs)
    values = set(refs.get("resources", [])) | set(refs.get("tags", []))
    return _fraction_overlap(query_tokens, values)


def _graph_rerank(query_tokens: list[str], docs: list[Any]) -> float:
    refs = _merged_refs(docs)
    values = set(refs.get("resources", [])) | set(refs.get("params", [])) | set(refs.get("auth", []))
    return _fraction_overlap(query_tokens, values)


def _graph_constrained(query_tokens: list[str], docs: list[Any]) -> float:
    refs = _merged_refs(docs)
    params = set(refs.get("params", []))
    if not params:
        return 0.0
    return _fraction_overlap(query_tokens, params)


def _graph_sparse(query_tokens: list[str], docs: list[Any]) -> float:
    refs = _merged_refs(docs)
    values = set().union(*(set(items) for items in refs.values()))
    return _fraction_overlap(query_tokens, values)


def _trigram_similarity(query: str, text_value: str) -> float:
    query_trigrams = _trigrams(query)
    text_trigrams = _trigrams(text_value)
    if not query_trigrams or not text_trigrams:
        return 0.0
    return len(query_trigrams & text_trigrams) / len(query_trigrams | text_trigrams)


def _trigrams(value: str) -> set[str]:
    normalized = " ".join(tokenize(value))
    padded = f"  {normalized}  "
    return {padded[index : index + 3] for index in range(max(0, len(padded) - 2))}


def _merged_refs(docs: list[Any]) -> dict[str, list[str]]:
    merged: dict[str, list[str]] = defaultdict(list)
    for doc in docs:
        refs = getattr(doc, "graph_refs", None) or {}
        if isinstance(refs, dict):
            for key, values in refs.items():
                if isinstance(values, list):
                    merged[key].extend(str(value).lower() for value in values)
    return {key: list(dict.fromkeys(values)) for key, values in merged.items()}


def _fraction_overlap(query_tokens: list[str], values: set[str]) -> float:
    if not query_tokens or not values:
        return 0.0
    query_set = set(query_tokens)
    expanded_values = set()
    for value in values:
        expanded_values.update(tokenize(value))
    if not expanded_values:
        return 0.0
    return min(1.0, len(query_set & expanded_values) / max(1, len(query_set)))


def _normalize_endpoint_scores(scores: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if not scores:
        return scores
    values = [float(payload["score"]) for payload in scores.values()]
    lo = min(values)
    hi = max(values)
    for payload in scores.values():
        raw = float(payload["score"])
        payload["score"] = 1.0 if hi == lo and raw > 0 else ((raw - lo) / (hi - lo) if hi != lo else 0.0)
    return scores


def _reason(components: dict[str, float]) -> str:
    top = sorted(components.items(), key=lambda item: item[1], reverse=True)[:3]
    return "fusion:" + ",".join(f"{name}={value:.2f}" for name, value in top if value > 0)
```

- [ ] **Step 4: Run ranker tests**

Run:

```powershell
python -m pytest backend/tests/test_toolrouter_fusion_ranker.py -q
```

Expected: PASS.

---

### Task 5: Replace `find_tool_candidates()` With Fusion Ranker

**Files:**
- Modify: `backend/services/agent/rest_operator.py`
- Test: `backend/tests/test_rest_catalog.py`
- Test: `backend/tests/test_api_orchestration.py`
- Test: `backend/tests/test_execution_frames.py`

- [ ] **Step 1: Add direct-replacement tests**

Append to `backend/tests/test_rest_catalog.py`:

```python
import pytest

from backend.services.agent import rest_operator


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
```

- [ ] **Step 2: Run focused failing tests**

Run:

```powershell
python -m pytest backend/tests/test_rest_catalog.py::test_find_tool_candidates_uses_fusion_ranker_directly backend/tests/test_rest_catalog.py::test_find_tool_candidates_does_not_run_legacy_overlap_when_index_missing -q
```

Expected: FAIL because `rest_operator` does not import/call `rank_generated_tools`.

- [ ] **Step 3: Replace candidate search implementation**

Modify imports in `backend/services/agent/rest_operator.py`:

```python
from backend.services.toolrouter.fusion_ranker import rank_generated_tools
```

Replace the body of `find_tool_candidates()` with:

```python
    ranked = await rank_generated_tools(message=message, saas_agent_id=saas_agent_id, db=db, limit=limit)
    candidates = [
        ToolCandidate(
            tool=row.tool,
            action=row.action,
            connection=row.connection,
            score=row.score,
            reason=row.reason,
        )
        for row in ranked
    ]
    return sorted(candidates, key=lambda row: (-row.score, _required_count(row.tool), row.tool.name))[:limit]
```

Do not call the old overlap scorer. Remove the old query/scoring block from `find_tool_candidates()` after tests are passing.

- [ ] **Step 4: Run router-adjacent tests**

Run:

```powershell
python -m pytest backend/tests/test_rest_catalog.py backend/tests/test_toolrouter_adapter.py backend/tests/test_api_orchestration.py backend/tests/test_execution_frames.py -q
```

Expected: PASS.

---

### Task 6: Surface Router Index Readiness In Backend Catalog And RouteDeck Props

**Files:**
- Modify: `backend/services/catalog.py`
- Modify: `backend/services/app_graph/corpus_surfaces.py`
- Modify: `backend/services/app_graph/runtime.py`
- Test: `backend/tests/test_corpus_graph_contract.py`
- Test: `backend/tests/test_app_graph_contract.py`

- [ ] **Step 1: Add backend surface acceptance tests**

Add a focused test to `backend/tests/test_app_graph_contract.py`:

```python
def test_catalog_surface_contract_includes_router_index_readiness():
    from backend.services.app_graph import corpus_surfaces

    source = inspect.getsource(corpus_surfaces)

    assert "router_index" in source
    assert "router_documents_count" in source
```

If `inspect` is not imported in the file, add:

```python
import inspect
```

- [ ] **Step 2: Add catalog router summary helper**

Modify `backend/services/catalog.py` to query the latest ready `ToolRouterIndex` for the active SaaS Agent and include:

```python
"router_index": {
    "status": index.status.value if hasattr(index.status, "value") else str(index.status),
    "router_version": index.router_version,
    "document_count": index.document_count,
    "endpoint_count": index.endpoint_count,
    "catalog_fingerprint": index.catalog_fingerprint[:12],
}
```

Use `None` when no index exists.

- [ ] **Step 3: Add catalog surface props**

Modify the catalog surface builder in `backend/services/app_graph/corpus_surfaces.py` so the catalog surface props include:

```python
"router_index": catalog.get("router_index") if isinstance(catalog, dict) else None,
```

When activation events are available from graph context, preserve the existing `activation_events` prop and include router counts from the `router_index` activation event when present.

- [ ] **Step 4: Run backend graph tests**

Run:

```powershell
python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py -q
```

Expected: PASS.

---

### Task 7: Update Owner UI Acceptance Surfaces

**Files:**
- Modify: `frontend/src/components/saasAgent/ConnectSetupView.tsx`
- Modify: `frontend/src/components/appGraph/corpusSurfaces.tsx`

- [ ] **Step 1: Update activation log wording in setup view**

Modify `frontend/src/components/saasAgent/ConnectSetupView.tsx` in `activateConnection()`:

```tsx
const label = typeof data.message === 'string' ? data.message : eventType
const suffix =
  eventType === 'step' && data.step === 'router_index' && data.status === 'done'
    ? ` (${String(data.router_documents_count || 0)} docs, ${String(data.router_endpoint_count || 0)} endpoints)`
    : ''
setActivationLog((prev) => [...prev, `${eventType}: ${label}${suffix}`])
```

Update the empty activation copy:

```tsx
Activation will parse OpenAPI, create actions, generate callable tools, and build the fusion router index.
```

- [ ] **Step 2: Show router readiness in Catalog surface**

Modify the catalog branch in `frontend/src/components/appGraph/corpusSurfaces.tsx`:

```tsx
const routerIndex = surface.props?.router_index as Record<string, unknown> | undefined
```

Add a fourth metric:

```tsx
<Metric
  label="Router docs"
  value={Number(routerIndex?.document_count || 0)}
  icon={<Database className="h-4 w-4" />}
/>
```

Add a compact status line:

```tsx
{routerIndex && (
  <p className="mt-3 text-sm text-slate-500">
    Router index: {String(routerIndex.status || 'unknown')} · {String(routerIndex.router_version || 'unknown')}
  </p>
)}
```

Use an already imported database/catalog icon if `Database` is not imported.

- [ ] **Step 3: Run frontend type-check**

Run:

```powershell
cd frontend
npm run type-check
```

Expected: PASS.

---

### Task 8: End-To-End Acceptance And Regression Validation

**Files:**
- Modify docs only if runtime behavior or acceptance evidence changes:
  - `architecture/code-map.md`
  - `architecture/components/openapi-provider-discovery.md`
  - `architecture/components/deployed-agent-orchestration.md`
  - `SYSTEM_FLOW_INDEX.md`
  - `context.md`

- [ ] **Step 1: Run backend regression suite**

Run:

```powershell
python -m pytest backend/tests/test_toolrouter_documents.py backend/tests/test_toolrouter_index_builder.py backend/tests/test_toolrouter_fusion_ranker.py backend/tests/test_toolrouter_activation.py backend/tests/test_rest_catalog.py backend/tests/test_toolrouter_adapter.py backend/tests/test_api_orchestration.py backend/tests/test_execution_frames.py -q
```

Expected: PASS.

- [ ] **Step 2: Run frontend type-check**

Run:

```powershell
cd frontend
npm run type-check
```

Expected: PASS.

- [ ] **Step 3: Run Docker app**

Run:

```powershell
docker compose up --build
```

Expected:

- backend reachable at `http://localhost:8085/api/health`
- frontend reachable at `http://localhost:3007/app/home`

- [ ] **Step 4: Verify UI setup acceptance**

In the owner UI:

1. Open `http://localhost:3007/app/home`.
2. Open or create a SaaS Agent.
3. Use the connection setup surface to save and activate an arbitrary REST/OpenAPI API.
4. Confirm the activation log includes "Building fusion router index" and "Fusion router index ready".
5. Open Catalog.
6. Confirm Catalog shows Ready APIs, Actions, Tools, and Router docs.

Expected: Router index readiness is visible without opening backend logs or a database console.

- [ ] **Step 5: Verify runtime behavior from UI**

In owner execution planning or chat, ask:

```text
list products
```

Expected:

- Candidate selection uses the fusion index.
- Product/list endpoint is selected or shown as top option.
- No connection-level auth header request appears.

Ask:

```text
delete all customers
```

Expected:

- Existing unsafe/write guardrails block or require policy/approval.
- Router ranking does not bypass `ToolRouterAdapter` or approval flow.

- [ ] **Step 6: Verify public deployed chat safety**

Open the deployed public route for the activated agent, such as:

```text
http://localhost:3007/a/{slug}
```

Ask:

```text
just list the product names we sell
```

Expected:

- Public answer is product/user-facing.
- It does not ask visitors for API keys, publishable-key headers, trace ids, operation ids, raw endpoint paths, or internal resource ids.

- [ ] **Step 7: Update architecture docs and context**

Update:

- `architecture/code-map.md`
- `architecture/components/openapi-provider-discovery.md`
- `architecture/components/deployed-agent-orchestration.md`
- `context.md`

Add the current fact that activation now builds a setup-time fusion router index and runtime candidate selection loads that ready index.

- [ ] **Step 8: Run doc coverage advisory**

Run:

```powershell
python scripts/check_doc_coverage.py
```

Expected: No new source ownership warnings for `backend/services/toolrouter/**/*.py`; any advisory warnings are recorded in closeout notes.

---

## Self-Review

- Spec coverage: The plan covers setup-time dynamic indexing, direct replacement runtime ranking, Postgres search extensions, arbitrary API collections, UI acceptance from `context.md`, and public-safe deployed chat behavior.
- Placeholder scan: No task contains TBD, TODO, or unspecified "handle edge cases" language.
- Type consistency: New backend model names are `ToolRouterIndex`, `ToolRouterDocument`, and `ToolRouterIndexStatus`; service entrypoints are `build_toolrouter_index_for_agent()` and `rank_generated_tools()`.
- Scope check: Dense embeddings, pgvector ANN indexes, true GraphSAGE/GNN, and local cross-encoder reranking are intentionally excluded from this first production replacement.
