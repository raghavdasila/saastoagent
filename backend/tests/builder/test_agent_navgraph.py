from __future__ import annotations

import json
import uuid

from corpus.features.builder.domain import BuilderInputSnapshot, BuilderSourceBinding
from corpus.features.builder.navgraph import compile_agent_navgraph, load_agent_navgraph
from corpus.features.designer.schemas import DesignContent
from corpus.features.designer.topology import compile_design_topology


def test_accepted_design_compiles_to_stable_routedeck_navgraph(tmp_path):
    document = {
        "openapi": "3.0.3",
        "info": {"title": "Store", "version": "1"},
        "paths": {
            "/store/products/{id}": {
                "get": {
                    "operationId": "GetProduct",
                    "summary": "Get one product",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "ok"}},
                }
            },
            "/store/carts": {
                "post": {
                    "operationId": "PostCarts",
                    "summary": "Create a cart",
                    "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object", "properties": {"region_id": {"type": "string"}}, "required": ["region_id"], "additionalProperties": False}}}},
                    "responses": {"200": {"description": "ok"}},
                }
            },
        },
    }
    document_path = tmp_path / "openapi.json"
    document_path.write_text(json.dumps(document), encoding="utf-8")
    binding = BuilderSourceBinding(
        source_id="source-1", source_revision_id="revision-1", curation_id="curation-1",
        inventory_fingerprint="f" * 64, included_operation_ids=("GetProduct", "PostCarts"),
        artifact_dir=tmp_path, document_path=document_path, document_hash="d" * 64,
        profile_id="profile-1", base_url="http://127.0.0.1:9100", authentication_method="api_key",
        credential_name="x-publishable-api-key", credential_reference_id=uuid.uuid4(), credential_version=1,
    )
    snapshot = BuilderInputSnapshot(
        build_id=uuid.uuid4(), build_request_id=uuid.uuid4(), organization_id=uuid.uuid4(),
        agent_id=uuid.uuid4(), agent_version=3, design_revision_id=uuid.uuid4(), input_fingerprint="i" * 64,
        name="Catalog agent", goal="Answer catalog questions", instructions="Use exact catalog evidence.",
        features=("Catalog",), behaviors=("Answer one product lookup",),
        policies=("Never invent a product.",), capabilities=("Product lookup: GetProduct, PostCarts",), tools=("GetProduct", "PostCarts"),
        runtime_areas=({"title": "Catalog", "capability_titles": ("Product lookup",)},),
        source_bindings=(binding,),
    )

    first = compile_agent_navgraph(snapshot)
    second = compile_agent_navgraph(snapshot)

    assert first == second
    assert len(first.navgraph_hash) == 64
    graph = first.compiled_navgraph
    assert graph["entry_node"]["id"] == "agent_runtime.home"
    assert len(graph["nodes"]) == 2
    assert graph["nodes"][0]["public_metadata"]["accepted_design"]["goal"] == "Answer catalog questions"
    expected_topology = compile_design_topology(DesignContent(
        goal=snapshot.goal,
        instructions=snapshot.instructions,
        features=snapshot.features,
        behaviors=snapshot.behaviors,
        policies=snapshot.policies,
        capabilities=snapshot.capabilities,
        tools=snapshot.tools,
        runtime_areas=snapshot.runtime_areas,
    ))
    assert graph["nodes"][0]["public_metadata"]["designer_topology"]["topology_hash"] == expected_topology.topology_hash
    runtime_node = next(item for item in graph["nodes"] if item["id"] != "agent_runtime.home")
    assert [item["id"] for item in runtime_node["capabilities"]] == [
        item.id for item in expected_topology.capabilities
    ]
    assert [item["title"] for item in runtime_node["capabilities"]] == [
        item.title for item in expected_topology.capabilities
    ]
    operations = {
        item["public_metadata"]["source_operation_id"]: item
        for item in runtime_node["operations"]
        if "source_operation_id" in item["public_metadata"]
    }
    assert operations["GetProduct"]["safety_class"] == "read_external"
    assert operations["GetProduct"]["review_policy"] == "none"
    assert operations["PostCarts"]["safety_class"] == "write_external"
    assert operations["PostCarts"]["review_policy"] == "required"
    assert operations["PostCarts"]["unknown_recovery_directive"]
    assert operations["GetProduct"]["input_schema"]["required"] == ["path"]
    assert operations["PostCarts"]["input_schema"]["required"] == ["body"]
    serialized = json.dumps(first.compiled_navgraph, sort_keys=True)
    assert "credential_reference" not in serialized
    assert "x-publishable-api-key" not in serialized
    restored = load_agent_navgraph(first.navgraph_hash, first.compiled_navgraph)
    assert restored.graph.name == f"corpus-agent-{snapshot.build_id}"
    assert restored.agent_policies["agent_runtime.policy.1"].instruction == "Use exact catalog evidence."
