from __future__ import annotations

from types import SimpleNamespace

import pytest

from agent_execution_runtime import ApiCallResult

from corpus.app.agent_runtime_adapters import (
    CorpusApiExecutorPort,
    CorpusToolRouterPort,
    sandbox_safe_events,
)
from corpus.features.builder.ports import BuilderUnavailable


class EngineProbe:
    def __init__(self):
        self.values = None

    def retrieve(self, **values):
        self.values = values
        operation_id = values["allowed_endpoint_ids"][0]
        return SimpleNamespace(
            decision_type="ROUTE",
            decision_reason="selected_exact_operation",
            missing_inputs=(),
            steps=(
                SimpleNamespace(
                    ranked_items=(SimpleNamespace(item_id=operation_id, score=1.0),)
                ),
            ),
        )


class Bindings:
    def __init__(self, artifact_dir=".runtime/source-a"):
        self.artifact_dir = artifact_dir

    def get(self, build_hash):
        assert build_hash == "build-hash"
        return (
            {
                "artifact_dir": self.artifact_dir,
                "included_operation_ids": (
                    "GetProductTagsId",
                    "GetProductTypesId",
                ),
                "authentication_method": "api_key",
                "credential_name": "x-publishable-api-key",
            },
        )


def test_selected_clarification_operation_is_the_router_corpus_before_reroute(tmp_path):
    graph = tmp_path / "graph"
    graph.mkdir()
    (graph / "semantic_graph.json").write_text(
        '{"nodes":['
        '{"endpoint_id":"store:GetProductTagsId","facets":{"operation_id":"GetProductTagsId"}},'
        '{"endpoint_id":"store:GetProductTypesId","facets":{"operation_id":"GetProductTypesId"}}'
        ']}',
        encoding="utf-8",
    )
    engine = EngineProbe()
    port = CorpusToolRouterPort(engine, Bindings(str(tmp_path)))

    result = port.route(
        SimpleNamespace(content_hash="build-hash"),
        "Get the product type",
        {
            "__selected_operation_id": "GetProductTypesId",
            "id": "pt_exact",
            "path": {"id": "pt_exact"},
        },
    )

    assert result.decision_type == "ROUTE"
    assert engine.values["allowed_endpoint_ids"] == ("store:GetProductTypesId",)
    assert engine.values["provided_params"] == {"id": "pt_exact"}
    assert "__selected_operation_id" not in repr(engine.values)
    assert result.candidates[0].operation_id == "GetProductTypesId"


def test_selected_clarification_operation_must_belong_to_one_exact_build_binding():
    with pytest.raises(BuilderUnavailable, match="not uniquely bound"):
        CorpusToolRouterPort(EngineProbe(), Bindings()).route(
            SimpleNamespace(content_hash="build-hash"),
            "Delete a cart",
            {"__selected_operation_id": "PostCarts"},
        )


def test_sandbox_clarification_candidates_receive_exact_compiled_navgraph_titles():
    build = SimpleNamespace(compiled_navgraph={
        "nodes": [{
            "operations": [
                {
                    "id": "agent_runtime.tool.types",
                    "title": "List Product Types",
                    "public_metadata": {"source_operation_id": "GetProductTypes"},
                },
                {
                    "id": "agent_runtime.tool.tags",
                    "title": "List Product Tags",
                    "public_metadata": {"source_operation_id": "GetProductTags"},
                },
            ],
        }],
    })
    events = (
        SimpleNamespace(
            sequence=1,
            kind="router.decision",
            occurred_at="now",
            safe_data={
                "resolution": "operation_choice_required",
                "candidates": [
                    {"operation_id": "GetProductTypes", "score": 0.6},
                    {"operation_id": "GetProductTags", "score": 0.4},
                ],
                "missing_params": [],
            },
        ),
    )

    enriched = sandbox_safe_events(build, events)

    assert enriched[0]["safe_data"]["candidates"] == [
        {"operation_id": "GetProductTypes", "score": 0.6, "label": "List Product Types"},
        {"operation_id": "GetProductTags", "score": 0.4, "label": "List Product Tags"},
    ]
    assert events[0].safe_data["candidates"][0].get("label") is None


class ExecutionBindings:
    def get_build(self, build_hash):
        assert build_hash == "build-hash"
        return SimpleNamespace(runtime_build_hash=build_hash)


class SupervisorProbe:
    def __init__(self):
        self.values = None

    async def execute(self, **values):
        self.values = values
        result = ApiCallResult(
            values["execution_id"], values["operation_id"], "succeeded", 200,
            {"ok": True}, None, True, None, (),
        )
        return SimpleNamespace(api_result=result)


@pytest.mark.asyncio
async def test_router_only_clarification_values_never_enter_routedeck_arguments():
    supervisor = SupervisorProbe()
    port = CorpusApiExecutorPort(SimpleNamespace(), ExecutionBindings())
    port.attach_supervisor(supervisor)

    result = await port.execute(
        build=SimpleNamespace(content_hash="build-hash"),
        tenant_id="00000000-0000-0000-0000-000000000001",
        operation_id="GetProductTypesId",
        inputs={
            "__selected_operation_id": "GetProductTypesId",
            "id": "pt_exact",
            "path": {"id": "pt_exact"},
        },
        execution_id="execution-1",
    )

    assert result.status == "succeeded"
    assert supervisor.values["inputs"] == {"path": {"id": "pt_exact"}}
