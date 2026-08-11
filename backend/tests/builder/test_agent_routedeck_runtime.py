from __future__ import annotations

import asyncio
import json
import uuid
from datetime import UTC, datetime

import pytest
from agent_execution_runtime import ApiCallResult
from cryptography.fernet import Fernet
from routedeck_core.contracts.operations import OperationDisposition

from corpus.app.agent_routedeck_runtime import AgentRouteDeckSupervisor, agent_route_session
from corpus.features.builder.domain import BuilderInputSnapshot, BuilderRecord, BuilderSourceBinding
from corpus.features.builder.navgraph import compile_agent_navgraph


class DirectProbe:
    def __init__(self):
        self.calls = []

    async def execute_direct(self, **values):
        self.calls.append(values)
        return ApiCallResult(
            values["execution_id"], values["operation_id"], "succeeded", 200,
            {"ok": True}, None, True, None, (),
        )


@pytest.mark.asyncio
async def test_read_and_reviewed_write_run_in_one_durable_isolated_routedeck_session(tmp_path):
    document_path = tmp_path / "openapi.json"
    document_path.write_text(json.dumps({
        "openapi": "3.0.3", "info": {"title": "Store", "version": "1"},
        "paths": {
            "/store/products": {"get": {"operationId": "GetProducts", "responses": {"200": {"description": "ok"}}}},
            "/store/carts": {"post": {"operationId": "PostCarts", "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "properties": {}, "additionalProperties": False}}}}, "responses": {"200": {"description": "ok"}}}},
        },
    }), encoding="utf-8")
    binding = BuilderSourceBinding(
        "source", "revision", "curation", "f" * 64, ("GetProducts", "PostCarts"),
        tmp_path, document_path, "d" * 64, "profile", "http://127.0.0.1:9100",
        "none", None, None, None,
    )
    snapshot = BuilderInputSnapshot(
        uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), 1, uuid.uuid4(), "i" * 64,
        "Store Agent", "Serve store requests", "Use only exact results.", ("Store",),
        ("Answer and create carts",), ("Never invent.",), ("Store tools: GetProducts, PostCarts",),
        ("GetProducts", "PostCarts"), (binding,),
    )
    artifact = compile_agent_navgraph(snapshot)
    now = datetime.now(UTC)
    build = BuilderRecord(
        snapshot.build_id, snapshot.organization_id, snapshot.agent_id, snapshot.build_request_id,
        snapshot.design_revision_id, 1, "ready", "running", "r" * 64, "model", "digest", (),
        ("GetProducts", "PostCarts"), artifact.navgraph_hash, artifact.compiled_navgraph,
        artifact.frontend_contract, None, None, now, now,
    )
    direct = DirectProbe()
    supervisor = AgentRouteDeckSupervisor(tmp_path / "sessions", Fernet.generate_key().decode("ascii"), direct)

    with agent_route_session("sandbox-session"):
        read = await supervisor.execute(
            build=build, tenant_id=str(snapshot.organization_id), operation_id="GetProducts",
            inputs={}, execution_id="read-request",
        )
        staged = await supervisor.execute(
            build=build, tenant_id=str(snapshot.organization_id), operation_id="PostCarts",
            inputs={"body": {}}, execution_id="write-request",
        )

    assert read.operation.disposition is OperationDisposition.COMPLETED, read.operation.failure
    assert read.api_result is not None and read.api_result.status == "succeeded"
    assert staged.operation.disposition is OperationDisposition.REQUIRES_REVIEW
    assert staged.api_result is None
    assert len(direct.calls) == 1
    assert read.projection["current"]["node_id"] == "agent_runtime.home"
    assert staged.operation.review is not None

    accepted = await supervisor.accept(
        build=build, tenant_id=str(snapshot.organization_id), session_id="sandbox-session",
        review_id=staged.operation.review.id, request_id="write-accept",
    )

    assert accepted.operation.disposition is OperationDisposition.COMPLETED
    assert accepted.api_result is not None and accepted.api_result.operation_id == "PostCarts"
    assert len(direct.calls) == 2
    assert direct.calls[1]["approved_write"] is True


@pytest.mark.asyncio
async def test_parallel_read_tools_share_one_durable_agent_session_without_sqlite_failure(tmp_path):
    document_path = tmp_path / "openapi.json"
    document_path.write_text(json.dumps({
        "openapi": "3.0.3", "info": {"title": "Store", "version": "1"},
        "paths": {
            "/store/types": {"get": {"operationId": "GetProductTypes", "responses": {"200": {"description": "ok"}}}},
            "/store/tags": {"get": {"operationId": "GetProductTags", "responses": {"200": {"description": "ok"}}}},
        },
    }), encoding="utf-8")
    binding = BuilderSourceBinding(
        "source", "revision", "curation", "f" * 64,
        ("GetProductTypes", "GetProductTags"), tmp_path, document_path,
        "d" * 64, "profile", "http://127.0.0.1:9100", "none", None, None, None,
    )
    snapshot = BuilderInputSnapshot(
        uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), 1, uuid.uuid4(), "i" * 64,
        "Taxonomy Agent", "Serve taxonomy requests", "Use only exact results.",
        ("Store",), ("Answer taxonomy requests",), ("Never invent.",),
        ("Store tools: GetProductTypes, GetProductTags",), ("GetProductTypes", "GetProductTags"), (binding,),
    )
    artifact = compile_agent_navgraph(snapshot)
    now = datetime.now(UTC)
    build = BuilderRecord(
        snapshot.build_id, snapshot.organization_id, snapshot.agent_id,
        snapshot.build_request_id, snapshot.design_revision_id, 1, "ready",
        "running", "r" * 64, "model", "digest", (),
        ("GetProductTypes", "GetProductTags"), artifact.navgraph_hash,
        artifact.compiled_navgraph, artifact.frontend_contract, None, None, now, now,
    )
    direct = DirectProbe()
    supervisor = AgentRouteDeckSupervisor(
        tmp_path / "sessions", Fernet.generate_key().decode("ascii"), direct
    )

    async def execute(operation_id: str):
        with agent_route_session("parallel-sandbox-session"):
            return await supervisor.execute(
                build=build,
                tenant_id=str(snapshot.organization_id),
                operation_id=operation_id,
                inputs={},
                execution_id=f"request-{operation_id}",
            )

    results = await asyncio.gather(
        asyncio.to_thread(
            lambda: asyncio.run(execute("GetProductTypes"))
        ),
        asyncio.to_thread(
            lambda: asyncio.run(execute("GetProductTags"))
        ),
    )

    assert all(
        result.operation.disposition is OperationDisposition.COMPLETED
        for result in results
    )
    assert {call["operation_id"] for call in direct.calls} == {
        "GetProductTypes", "GetProductTags"
    }
