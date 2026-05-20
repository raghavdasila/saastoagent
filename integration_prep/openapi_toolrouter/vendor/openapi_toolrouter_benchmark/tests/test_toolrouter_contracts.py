import json
from pathlib import Path

import pytest


FIXTURE = {
    "openapi": "3.0.0",
    "info": {"title": "Fixture Commerce API", "version": "1.0.0"},
    "servers": [{"url": "http://localhost:9000"}],
    "components": {
        "securitySchemes": {
            "bearer": {"type": "http", "scheme": "bearer"},
            "publishable": {"type": "apiKey", "in": "header", "name": "x-publishable-api-key"},
        },
        "schemas": {
            "Product": {
                "type": "object",
                "required": ["id", "title"],
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "variants": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/ProductVariant"},
                    },
                },
            },
            "ProductVariant": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "sku": {"type": "string"},
                },
            },
            "ProductListResponse": {
                "type": "object",
                "properties": {
                    "products": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/Product"},
                    }
                },
            },
            "ProductCreate": {
                "type": "object",
                "required": ["title"],
                "properties": {"title": {"type": "string"}},
            },
            "InvalidDefault": {
                "type": "object",
                "properties": {
                    "deleted": {
                        "type": "boolean",
                        "default": "variant",
                    }
                },
            },
        },
    },
    "paths": {
        "/store/products": {
            "get": {
                "operationId": "ListStoreProducts",
                "tags": ["Products"],
                "summary": "List products",
                "parameters": [
                    {"name": "q", "in": "query", "required": False, "schema": {"type": "string"}}
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ProductListResponse"}
                            }
                        },
                    }
                },
                "security": [{"publishable": []}],
            },
            "post": {
                "operationId": "CreateStoreProduct",
                "tags": ["Products"],
                "summary": "Create product",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ProductCreate"}
                        }
                    },
                },
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Product"}
                            }
                        },
                    }
                },
                "security": [{"bearer": []}],
            },
        },
        "/store/products/{id}": {
            "parameters": [
                {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
            ],
            "get": {
                "operationId": "GetStoreProduct",
                "tags": ["Products"],
                "summary": "Get product",
                "responses": {
                    "200": {
                        "description": "OK",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Product"}
                            }
                        },
                    }
                },
            },
        },
    },
}


def write_fixture(tmp_path: Path) -> Path:
    import yaml

    path = tmp_path / "fixture.yaml"
    path.write_text(yaml.safe_dump(FIXTURE, sort_keys=False), encoding="utf-8")
    return path


def write_spec(tmp_path: Path, spec: dict, name: str = "fixture.yaml") -> Path:
    import yaml

    path = tmp_path / name
    path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
    return path


def fixture_with_delete() -> dict:
    spec = json.loads(json.dumps(FIXTURE))
    spec["paths"]["/store/products/{id}"]["delete"] = {
        "operationId": "DeleteStoreProduct",
        "tags": ["Products"],
        "summary": "Delete product",
        "responses": {"204": {"description": "Deleted"}},
        "security": [{"bearer": []}],
    }
    return spec


def make_many_endpoint_bundle(domain_count: int = 6, per_domain: int = 30):
    from toolrouter.openapi_loader import NormalizedBundle, NormalizedEndpoint, NormalizedParameter

    endpoints = []
    operation_classes = ["list", "get", "create", "update", "delete", "search"]
    methods = {
        "list": "GET",
        "get": "GET",
        "create": "POST",
        "update": "PATCH",
        "delete": "DELETE",
        "search": "GET",
    }
    for domain_idx in range(domain_count):
        domain = f"domain{domain_idx}"
        for idx in range(per_domain):
            op_class = operation_classes[idx % len(operation_classes)]
            path = f"/v1/{domain}/entity-{idx}"
            params = []
            if op_class in {"get", "update", "delete"}:
                path = f"{path}/{{id}}"
                params.append(
                    NormalizedParameter(
                        name="id",
                        location="path",
                        required=True,
                        schema={"type": "string"},
                    )
                )
            endpoints.append(
                NormalizedEndpoint(
                    id=f"fixture:{domain}_{op_class}_{idx}",
                    source="fixture",
                    method=methods[op_class],
                    path=path,
                    operation_id=f"{op_class.title()}Domain{domain_idx}Entity{idx}",
                    tags=[f"{domain} Entities"],
                    summary=f"{op_class.title()} {domain} entity {idx}",
                    description=f"Endpoint for {domain} entity {idx}",
                    params=params,
                    required_params=[param.name for param in params if param.required],
                    request_schemas=[f"{domain.title()}Write{idx}"] if op_class in {"create", "update"} else [],
                    response_schemas=[f"{domain.title()}Read{idx}"],
                    security=["bearer"] if idx % 2 else [],
                    resources=[domain],
                    operation_class=op_class,
                    operation_confidence=0.95,
                )
            )
    return NormalizedBundle(
        endpoints=endpoints,
        schemas={},
        security_schemes={"bearer": {"type": "http", "scheme": "bearer"}},
        manifest={"spec_count": 1},
    )


def test_loader_normalizes_openapi_without_endpoint_mapping(tmp_path: Path):
    from toolrouter.openapi_loader import load_openapi_specs

    spec_path = write_fixture(tmp_path)
    bundle = load_openapi_specs([spec_path])

    assert bundle.manifest["spec_count"] == 1
    assert len(bundle.endpoints) == 3
    by_operation = {endpoint.operation_id: endpoint for endpoint in bundle.endpoints}
    assert by_operation["ListStoreProducts"].operation_class == "list"
    assert by_operation["CreateStoreProduct"].operation_class == "create"
    assert by_operation["GetStoreProduct"].required_params == ["id"]
    assert "products" in by_operation["ListStoreProducts"].resources
    assert "Product" in bundle.schemas
    assert bundle.manifest["specs"][0]["prance_resolution"]["ok"] is True
    assert bundle.manifest["specs"][0]["prance_resolution"]["refs_after"] < bundle.manifest["specs"][0]["prance_resolution"]["refs_before"]


def test_spec_repair_preserves_raw_and_removes_invalid_defaults(tmp_path: Path):
    import yaml

    from toolrouter.openapi_loader import load_openapi_specs, write_normalized_bundle
    from toolrouter.spec_repair import read_repair_manifest

    spec_path = write_fixture(tmp_path)
    bundle = load_openapi_specs([spec_path])
    out = tmp_path / "artifacts"
    write_normalized_bundle(bundle, out)

    raw_spec = yaml.safe_load((out / "raw_openapi" / "fixture.yaml").read_text(encoding="utf-8"))
    repaired_spec = yaml.safe_load((out / "repaired_openapi" / "fixture.yaml").read_text(encoding="utf-8"))
    manifest = read_repair_manifest(out)

    assert raw_spec["components"]["schemas"]["InvalidDefault"]["properties"]["deleted"]["default"] == "variant"
    assert "default" not in repaired_spec["components"]["schemas"]["InvalidDefault"]["properties"]["deleted"]
    assert manifest["repairs"][0]["json_pointer"].endswith("/default")
    assert manifest["repairs"][0]["old_value"] == "variant"
    assert manifest["repairs"][0]["new_value"] is None
    assert manifest["repairs"][0]["action"] == "remove_invalid_default"
    assert bundle.manifest["repair_counts"]["fixture"] == 1
    assert bundle.manifest["openapi_core_repaired"]["fixture"] == "loaded"


def test_graph_and_rag_are_generated_from_same_endpoints(tmp_path: Path):
    from toolrouter.graphgen import build_schema_graph
    from toolrouter.openapi_loader import load_openapi_specs
    from toolrouter.raggen import build_rag_corpus

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    graph = build_schema_graph(bundle)
    corpus = build_rag_corpus(bundle)

    endpoint_ids = {endpoint.id for endpoint in bundle.endpoints}
    graph_endpoint_ids = {
        node["id"].replace("endpoint:", "")
        for node in graph.nodes
        if node["kind"] == "endpoint"
    }
    corpus_endpoint_ids = {
        doc["endpoint_id"] for doc in corpus.documents if doc["kind"] == "endpoint"
    }

    assert endpoint_ids <= graph_endpoint_ids
    assert endpoint_ids <= corpus_endpoint_ids
    assert any(edge["kind"] == "references" for edge in graph.edges)


def test_router_baselines_include_rag_graph_hybrid_and_learned(tmp_path: Path):
    from toolrouter.graphgen import build_schema_graph
    from toolrouter.openapi_loader import load_openapi_specs
    from toolrouter.raggen import build_rag_corpus
    from toolrouter.router_baselines import rank_all_baselines

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    graph = build_schema_graph(bundle)
    corpus = build_rag_corpus(bundle)
    tasks = [
        {
            "id": "t1",
            "query": "list products",
            "expected_endpoint_sequence": [bundle.endpoint_by_operation("ListStoreProducts").id],
            "expected_required_params": {},
            "allowed_alternatives": [],
            "task_type": "single_step",
            "notes": "",
        },
        {
            "id": "t2",
            "query": "create product with title",
            "expected_endpoint_sequence": [bundle.endpoint_by_operation("CreateStoreProduct").id],
            "expected_required_params": {},
            "allowed_alternatives": [],
            "task_type": "single_step",
            "notes": "",
        },
        {
            "id": "t3",
            "query": "get product by id",
            "expected_endpoint_sequence": [bundle.endpoint_by_operation("GetStoreProduct").id],
            "expected_required_params": {
                bundle.endpoint_by_operation("GetStoreProduct").id: ["id"]
            },
            "allowed_alternatives": [],
            "task_type": "single_step",
            "notes": "",
        },
    ]

    rankings = rank_all_baselines("list products", bundle, corpus, graph, tasks=tasks)

    assert {
        "rag_endpoint",
        "rag_all_top3",
        "bm25_all_top3",
        "graph_text",
        "graph_sparse",
        "hybrid",
        "learned",
    } <= set(rankings)
    for ranked in rankings.values():
        assert ranked[0]["endpoint_id"] in {endpoint.id for endpoint in bundle.endpoints}


def test_task_generation_covers_requested_domains(tmp_path: Path):
    from toolrouter.openapi_loader import NormalizedBundle, NormalizedEndpoint
    from toolrouter.tasks import generate_tasks

    endpoints = []
    for domain in [
        "products",
        "orders",
        "customers",
        "carts",
        "inventory",
        "payments",
        "fulfillment",
        "returns",
        "promotions",
    ]:
        endpoints.append(
            NormalizedEndpoint(
                id=f"fixture:list_{domain}",
                source="fixture",
                method="GET",
                path=f"/admin/{domain}",
                operation_id=f"List{domain.title()}",
                tags=[domain.title()],
                summary=f"List {domain}",
                description="",
                params=[],
                required_params=[],
                request_schemas=[],
                response_schemas=[],
                security=[],
                resources=[domain],
                operation_class="list",
                operation_confidence=0.95,
            )
        )
    bundle = NormalizedBundle(
        endpoints=endpoints,
        schemas={},
        security_schemes={},
        manifest={"spec_count": 1},
    )

    coverage_terms = [
        "products",
        "orders",
        "customers",
        "carts",
        "inventory",
        "payments",
        "fulfillment",
        "returns",
        "promotions",
    ]
    tasks = generate_tasks(bundle, min_count=100, coverage_terms=coverage_terms)
    notes = " ".join(task["notes"] for task in tasks)

    assert len(tasks) >= 100
    for domain in coverage_terms:
        assert domain in notes
    assert any(task["task_type"] == "policy_required" for task in tasks)


def test_task_generation_derives_coverage_without_domain_terms(tmp_path: Path):
    from toolrouter.openapi_loader import NormalizedBundle, NormalizedEndpoint
    from toolrouter.tasks import derive_coverage_terms, generate_tasks

    endpoints = [
        NormalizedEndpoint(
            id="fixture:list_widgets",
            source="fixture",
            method="GET",
            path="/v1/widgets",
            operation_id="ListWidgets",
            tags=["Widgets"],
            summary="List widgets",
            description="",
            params=[],
            required_params=[],
            request_schemas=[],
            response_schemas=[],
            security=[],
            resources=["widgets"],
            operation_class="list",
            operation_confidence=0.95,
        ),
        NormalizedEndpoint(
            id="fixture:create_widgets",
            source="fixture",
            method="POST",
            path="/v1/widgets",
            operation_id="CreateWidgets",
            tags=["Widgets"],
            summary="Create widgets",
            description="",
            params=[],
            required_params=[],
            request_schemas=["WidgetCreate"],
            response_schemas=[],
            security=[],
            resources=["widgets"],
            operation_class="create",
            operation_confidence=0.95,
        ),
    ]
    bundle = NormalizedBundle(endpoints=endpoints, schemas={}, security_schemes={}, manifest={"spec_count": 1})

    assert "widgets" in derive_coverage_terms(bundle)
    tasks = generate_tasks(bundle, min_count=4, task_prefix="fixture")
    assert {task["id"].split("_")[0] for task in tasks} == {"fixture"}
    assert any("resource=widgets" in task["notes"] for task in tasks)


def test_task_generation_adds_provenance_and_allowed_alternatives(tmp_path: Path):
    from toolrouter.openapi_loader import NormalizedBundle, NormalizedEndpoint
    from toolrouter.tasks import generate_tasks

    endpoints = [
        NormalizedEndpoint(
            id="fixture:list_widgets",
            source="fixture",
            method="GET",
            path="/v1/widgets",
            operation_id="ListWidgets",
            tags=["Widgets"],
            summary="List widgets",
            description="Primary list",
            params=[],
            required_params=[],
            request_schemas=[],
            response_schemas=["WidgetList"],
            security=[],
            resources=["widgets"],
            operation_class="list",
            operation_confidence=0.95,
        ),
        NormalizedEndpoint(
            id="fixture:list_widgets_alt",
            source="fixture",
            method="GET",
            path="/v1/widgets/search",
            operation_id="SearchWidgets",
            tags=["Widgets"],
            summary="Search widgets",
            description="Alternate list",
            params=[],
            required_params=[],
            request_schemas=[],
            response_schemas=["WidgetList"],
            security=[],
            resources=["widgets"],
            operation_class="list",
            operation_confidence=0.95,
        ),
    ]
    bundle = NormalizedBundle(endpoints=endpoints, schemas={}, security_schemes={}, manifest={"spec_count": 1})

    tasks = generate_tasks(bundle, min_count=4, coverage_terms=["widgets"], task_prefix="fixture")
    task = next(item for item in tasks if item["expected_endpoint_sequence"] == ["fixture:list_widgets"])

    assert task["router_query"] == task["query"]
    assert task["resource"] == "widgets"
    assert task["operation_class"] == "list"
    assert task["provenance"]["path"] == "/v1/widgets"
    assert task["provenance"]["operationId"] == "ListWidgets"
    assert task["provenance"]["summary"] == "List widgets"
    assert task["provenance"]["description"] == "Primary list"
    assert task["provenance"]["tags"] == ["Widgets"]
    assert task["provenance"]["response_schemas"] == ["WidgetList"]
    assert ["fixture:list_widgets_alt"] in task["allowed_alternatives"]


def test_low_overlap_task_generation_creates_separate_abstention_suite():
    from toolrouter.leakage_audit import compute_task_leakage
    from toolrouter.tasks import generate_low_overlap_tasks

    bundle = make_many_endpoint_bundle()
    tasks = generate_low_overlap_tasks(
        bundle,
        min_routing=100,
        min_ambiguous=50,
        min_policy=50,
        coverage_terms=[f"domain{idx}" for idx in range(6)],
        task_prefix="fixture_low",
    )
    counts = {}
    for task in tasks:
        counts[task["task_type"]] = counts.get(task["task_type"], 0) + 1
    routing = [task for task in tasks if task["task_type"] == "single_step"]
    ambiguous = [task for task in tasks if task["task_type"] == "ambiguous"]
    policy = [task for task in tasks if task["task_type"] == "policy_required"]
    leakage = {row["task_id"]: row for row in compute_task_leakage(routing, bundle)}

    assert counts["single_step"] >= 100
    assert counts["ambiguous"] >= 50
    assert counts["policy_required"] >= 50
    assert all(leakage[task["id"]]["overlap_bucket"] == "low" for task in routing)
    assert all(task["expected_endpoint_sequence"] for task in routing)
    assert all(task.get("provenance") for task in routing)
    assert all(not task["expected_endpoint_sequence"] and task["allowed_alternatives"] for task in ambiguous)
    assert all("policy_required" not in task["router_query"] for task in policy)
    assert all("abstain" not in task["router_query"].casefold() for task in policy)
    assert all("no endpoint" not in task["router_query"].casefold() for task in policy)


def test_policy_tasks_are_not_auto_abstained_by_evaluator():
    from toolrouter.evaluator import evaluate_rankings

    tasks = [
        {
            "id": "policy_001",
            "query": "decide whether external authorization exists",
            "router_query": "decide whether external authorization exists",
            "expected_endpoint_sequence": [],
            "expected_required_params": {},
            "allowed_alternatives": [],
            "task_type": "policy_required",
            "resource": "widgets",
            "operation_class": "policy_required",
            "notes": "",
        }
    ]
    rankings = {
        "rag_endpoint": {
            "all": {
                "policy_001": [
                    {
                        "endpoint_id": "fixture:list_widgets",
                        "score": 0.9,
                        "required_params": [],
                    }
                ]
            }
        }
    }

    results = evaluate_rankings(tasks, rankings, split_task_ids={"all": {"policy_001"}}, k_values=[1])
    detail = results["details"][0]

    assert detail["endpoint_recall_at_k"] == 0.0
    assert detail["complete_plan_recall_at_k"] == 0.0
    assert detail["abstention_accuracy"] == 0.0


def test_validation_metrics_use_repaired_openapi_specs(tmp_path: Path):
    from toolrouter.evaluator import evaluate_rankings
    from toolrouter.openapi_loader import load_openapi_specs, write_normalized_bundle
    from toolrouter.validation import build_validation_context

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    artifacts = tmp_path / "artifacts"
    write_normalized_bundle(bundle, artifacts)
    endpoint = bundle.endpoint_by_operation("CreateStoreProduct")
    tasks = [
        {
            "id": "t1",
            "query": "create product with title",
            "router_query": "create product with title",
            "expected_endpoint_sequence": [endpoint.id],
            "expected_required_params": {},
            "allowed_alternatives": [],
            "task_type": "single_step",
            "resource": "products",
            "operation_class": "create",
            "notes": "",
        }
    ]
    rankings = {
        "rag": {
            "all": {
                "t1": [
                    {
                        "endpoint_id": endpoint.id,
                        "score": 1.0,
                        "method": endpoint.method,
                        "path": endpoint.path,
                        "required_params": [],
                    }
                ]
            }
        }
    }

    context = build_validation_context(artifacts, bundle)
    request_body = context.synthetic_request_body(endpoint)
    results = evaluate_rankings(tasks, rankings, split_task_ids={"all": {"t1"}}, k_values=[1], validation_context=context)
    detail = results["details"][0]
    summary = results["summary"][0]

    assert request_body == {"title": "sample"}
    assert detail["route_selected"] == 1.0
    assert detail["required_params_covered"] == 1.0
    assert detail["request_body_schema_pass"] == 1.0
    assert detail["validation_pass"] == 1.0
    assert detail["response_validation_status"] == "unknown_no_fixture"
    assert summary["validation_pass"] == 1.0


def test_splits_are_deterministic_and_leave_resource_out():
    from toolrouter.splits import build_task_splits

    tasks = [
        {
            "id": f"task_{idx:03d}",
            "task_type": "single_step" if idx % 2 else "policy_required",
            "resource": "widgets" if idx < 6 else "gadgets",
        }
        for idx in range(12)
    ]

    first = build_task_splits(tasks)
    second = build_task_splits(tasks)

    assert first == second
    assert set(first["primary"]) == {"train", "dev", "test"}
    widget_fold = first["leave_domain_out"]["widgets"]
    assert set(widget_fold["test"]) == {task["id"] for task in tasks if task["resource"] == "widgets"}
    assert not (set(widget_fold["train"]) & set(widget_fold["test"]))
    assert not (set(widget_fold["dev"]) & set(widget_fold["test"]))


def test_task_audit_writes_required_artifacts(tmp_path: Path):
    from toolrouter.openapi_loader import NormalizedBundle, NormalizedEndpoint
    from toolrouter.task_audit import write_task_audit

    endpoint = NormalizedEndpoint(
        id="fixture:list_widgets",
        source="fixture",
        method="GET",
        path="/v1/widgets",
        operation_id="ListWidgets",
        tags=["Widgets"],
        summary="List widgets",
        description="",
        params=[],
        required_params=[],
        request_schemas=[],
        response_schemas=["WidgetList"],
        security=[],
        resources=["widgets"],
        operation_class="list",
        operation_confidence=0.95,
    )
    bundle = NormalizedBundle(endpoints=[endpoint], schemas={}, security_schemes={}, manifest={"spec_count": 1})
    tasks = [
        {
            "id": "task_001",
            "resource": "widgets",
            "task_type": "single_step",
            "operation_class": "list",
            "expected_endpoint_sequence": ["fixture:list_widgets"],
            "expected_required_params": {},
            "allowed_alternatives": [],
        }
    ]

    write_task_audit(tasks, bundle, tmp_path, split_by_task={"task_001": "train"})

    assert (tmp_path / "task_audit.csv").exists()
    assert (tmp_path / "task_audit.json").exists()
    assert (tmp_path / "task_audit.md").exists()
    csv_text = (tmp_path / "task_audit.csv").read_text(encoding="utf-8")
    assert "task_id,split,resource,task_type,operation_class,endpoint_id" in csv_text
    assert "fixture:list_widgets" in csv_text


def test_retrieval_indices_pool_all_docs_and_bm25(tmp_path: Path):
    from toolrouter.graphgen import build_schema_graph
    from toolrouter.openapi_loader import load_openapi_specs
    from toolrouter.raggen import build_rag_corpus
    from toolrouter.retrieval_indices import build_retrieval_indices

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    corpus = build_rag_corpus(bundle)
    graph = build_schema_graph(bundle)
    indices = build_retrieval_indices(bundle, corpus, graph)

    for pooling in ["max", "mean", "top3"]:
        scores = indices.tfidf_all_scores("ProductCreate title", pooling=pooling)
        assert set(scores) == {endpoint.id for endpoint in bundle.endpoints}
        assert max(scores.values()) > 0

    bm25_scores = indices.bm25_all_scores("ProductCreate title", pooling="top3")
    assert set(bm25_scores) == {endpoint.id for endpoint in bundle.endpoints}
    assert max(bm25_scores.values()) > 0

    param_schema_scores = indices.param_schema_scores("ProductCreate title")
    assert set(param_schema_scores) == {endpoint.id for endpoint in bundle.endpoints}


def test_rag_docs_map_to_graph_nodes_without_synthetic_fallbacks(tmp_path: Path):
    from toolrouter.graphgen import build_schema_graph
    from toolrouter.openapi_loader import load_openapi_specs
    from toolrouter.raggen import build_rag_corpus
    from toolrouter.retrieval_indices import build_retrieval_indices

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    corpus = build_rag_corpus(bundle)
    graph = build_schema_graph(bundle)
    indices = build_retrieval_indices(bundle, corpus, graph)
    docs_by_id = {doc["id"]: doc for doc in corpus.documents}

    list_endpoint = bundle.endpoint_by_operation("ListStoreProducts")
    create_endpoint = bundle.endpoint_by_operation("CreateStoreProduct")
    get_endpoint = bundle.endpoint_by_operation("GetStoreProduct")

    assert indices.doc_graph_nodes(docs_by_id[f"endpoint:{list_endpoint.id}"]) == [f"endpoint:{list_endpoint.id}"]
    assert indices.doc_graph_nodes(docs_by_id[f"param:{get_endpoint.id}.path.id"]) == [f"param:{get_endpoint.id}.path.id"]
    assert "schema:ProductCreate" in indices.doc_graph_nodes(docs_by_id[f"request_schema:{create_endpoint.id}.ProductCreate"])
    assert "schema:Product" in indices.doc_graph_nodes(docs_by_id[f"response_schema:{create_endpoint.id}.Product"])
    assert "auth:bearer" in indices.doc_graph_nodes(docs_by_id[f"auth:{create_endpoint.id}"])

    assert indices.doc_graph_nodes({"id": "request_schema:missing.Nope", "kind": "request_schema", "endpoint_id": "missing"}) == []


def test_router_baselines_include_split_aware_fair_retrieval(tmp_path: Path):
    from toolrouter.graphgen import build_schema_graph
    from toolrouter.openapi_loader import load_openapi_specs
    from toolrouter.raggen import build_rag_corpus
    from toolrouter.router_baselines import rank_tasks
    from toolrouter.splits import build_task_splits

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    graph = build_schema_graph(bundle)
    corpus = build_rag_corpus(bundle)
    tasks = [
        {
            "id": "t1",
            "query": "list products",
            "router_query": "list products",
            "expected_endpoint_sequence": [bundle.endpoint_by_operation("ListStoreProducts").id],
            "expected_required_params": {},
            "allowed_alternatives": [],
            "task_type": "single_step",
            "resource": "products",
            "operation_class": "list",
            "notes": "",
        },
        {
            "id": "t2",
            "query": "create product with title",
            "router_query": "create product with title",
            "expected_endpoint_sequence": [bundle.endpoint_by_operation("CreateStoreProduct").id],
            "expected_required_params": {},
            "allowed_alternatives": [],
            "task_type": "single_step",
            "resource": "products",
            "operation_class": "create",
            "notes": "",
        },
        {
            "id": "t3",
            "query": "get product by id",
            "router_query": "get product by id",
            "expected_endpoint_sequence": [bundle.endpoint_by_operation("GetStoreProduct").id],
            "expected_required_params": {
                bundle.endpoint_by_operation("GetStoreProduct").id: ["id"]
            },
            "allowed_alternatives": [],
            "task_type": "single_step",
            "resource": "products",
            "operation_class": "get",
            "notes": "",
        },
        {
            "id": "t4",
            "query": "decide external policy",
            "router_query": "decide external policy",
            "expected_endpoint_sequence": [],
            "expected_required_params": {},
            "allowed_alternatives": [],
            "task_type": "policy_required",
            "resource": "products",
            "operation_class": "policy_required",
            "notes": "",
        },
    ]
    splits = build_task_splits(tasks)

    rankings = rank_tasks(tasks, bundle, corpus, graph, splits=splits)

    expected_baselines = {
        "rag_endpoint",
        "rag_all_max",
        "rag_all_mean",
        "rag_all_top3",
        "bm25_all_max",
        "bm25_all_mean",
        "bm25_all_top3",
        "grag_expand",
        "grag_rerank",
        "grag_constrained",
        "graph_text",
        "graph_sparse",
        "hybrid",
        "learned_lexical",
        "learned_bm25",
        "learned_graph",
        "learned_schema_param",
        "learned_lexical_graph",
        "learned_all",
        "learned",
    }
    assert set(rankings) == expected_baselines
    assert "all" in rankings["graph_sparse"]
    assert "test" in rankings["grag_expand"]
    assert "test" in rankings["grag_rerank"]
    assert "test" in rankings["grag_constrained"]
    assert "test" in rankings["learned"]
    assert "t1" in rankings["rag_all_top3"]["all"]
    assert rankings["learned"]["all"]["t1"] == rankings["learned_all"]["all"]["t1"]


def test_graph_sparse_selects_dev_config_and_emits_diagnostics(tmp_path: Path):
    from toolrouter.graphgen import build_schema_graph
    from toolrouter.openapi_loader import load_openapi_specs
    from toolrouter.raggen import build_rag_corpus
    from toolrouter.router_baselines import rank_tasks
    from toolrouter.splits import build_task_splits

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    graph = build_schema_graph(bundle)
    corpus = build_rag_corpus(bundle)
    tasks = [
        {
            "id": "t1",
            "query": "list products",
            "router_query": "list products",
            "expected_endpoint_sequence": [bundle.endpoint_by_operation("ListStoreProducts").id],
            "expected_required_params": {},
            "allowed_alternatives": [],
            "task_type": "single_step",
            "resource": "products",
            "operation_class": "list",
            "notes": "",
        },
        {
            "id": "t2",
            "query": "create product",
            "router_query": "create product",
            "expected_endpoint_sequence": [bundle.endpoint_by_operation("CreateStoreProduct").id],
            "expected_required_params": {},
            "allowed_alternatives": [],
            "task_type": "single_step",
            "resource": "products",
            "operation_class": "create",
            "notes": "",
        },
        {
            "id": "t3",
            "query": "get product by id",
            "router_query": "get product by id",
            "expected_endpoint_sequence": [bundle.endpoint_by_operation("GetStoreProduct").id],
            "expected_required_params": {bundle.endpoint_by_operation("GetStoreProduct").id: ["id"]},
            "allowed_alternatives": [],
            "task_type": "single_step",
            "resource": "products",
            "operation_class": "get",
            "notes": "",
        },
        {
            "id": "t4",
            "query": "external policy",
            "router_query": "external policy",
            "expected_endpoint_sequence": [],
            "expected_required_params": {},
            "allowed_alternatives": [],
            "task_type": "policy_required",
            "resource": "products",
            "operation_class": "policy_required",
            "notes": "",
        },
    ]
    splits = build_task_splits(tasks)

    rankings, diagnostics = rank_tasks(tasks, bundle, corpus, graph, splits=splits, include_diagnostics=True)

    assert "graph_text" in rankings
    assert "graph_sparse" in rankings
    assert diagnostics["graph_sparse_ablation"]
    assert diagnostics["graph_sparse_stability"]
    assert diagnostics["hybrid_weight_selection"]
    assert diagnostics["learned_ablations"]
    assert diagnostics["grag_expand_selection"]
    assert diagnostics["grag_rerank_selection"]
    assert diagnostics["grag_constrained_selection"]
    assert diagnostics["grag_diagnostics"]
    selected = diagnostics["graph_sparse_selected_configs"]["all"]
    assert {"seed_top_n", "steps", "damping", "directed", "high_degree_downweight", "endpoint_prior_weight"} <= set(selected)
    assert any(
        "top_seed_nodes" in row
        and "high_degree_seed_nodes" in row
        and "endpoint_projection" in row
        for row in diagnostics["graph_sparse_diagnostics"]
    )
    assert diagnostics["hybrid_weight_selection"]["all"]["selected_weights"] != {
        "lexical": 0.5,
        "bm25": 0.0,
        "graph": 0.5,
        "schema_param": 0.0,
    }
    assert set(diagnostics["grag_rerank_selection"]["all"]["selected_weights"]) == {
        "resource_match",
        "param_match",
        "schema_proximity",
        "auth_proximity",
        "graph_distance",
        "endpoint_degree",
        "operation_confidence",
    }
    assert any(
        row["baseline"] == "grag_expand"
        and row["seed_docs"]
        and row["seed_nodes"]
        and row["score_components"]
        for row in diagnostics["grag_diagnostics"]
    )
    assert any(
        row["baseline"] == "grag_rerank"
        and row["candidate_endpoints"]
        and row["graph_features"]
        for row in diagnostics["grag_diagnostics"]
    )
    assert any(
        row["baseline"] == "grag_constrained"
        and row["constraints"]
        and row["score_components"]
        for row in diagnostics["grag_diagnostics"]
    )


def test_evaluator_writes_required_metrics(tmp_path: Path):
    from toolrouter.evaluator import evaluate_rankings

    endpoint_id = "fixture:ListProducts"
    tasks = [
        {
            "id": "t1",
            "query": "list products",
            "expected_endpoint_sequence": [endpoint_id],
            "expected_required_params": {},
            "allowed_alternatives": [],
            "task_type": "single_step",
            "leakage_bucket": "high",
            "notes": "",
        }
    ]
    rankings = {
        "rag": {
            "t1": [
                {
                    "endpoint_id": endpoint_id,
                    "score": 1.0,
                    "operation_class": "list",
                    "required_params": [],
                }
            ]
        }
    }

    results = evaluate_rankings(tasks, rankings, k_values=[1])

    summary = results["summary"][0]
    assert summary["endpoint_recall_at_k"] == 1.0
    assert summary["complete_plan_recall_at_k"] == 1.0
    assert summary["first_step_top1_accuracy"] == 1.0
    assert summary["param_coverage"] == 1.0
    assert summary["schema_validation_pass_rate"] == 1.0
    assert summary["routing_only_complete_at_1"] == 1.0
    assert summary["routing_only_complete_at_10"] == 1.0
    assert summary["ambiguous_abstention_accuracy"] == 0.0
    assert summary["policy_abstention_accuracy"] == 0.0
    assert summary["macro_average_by_track"] == 1.0 / 3.0
    assert results["leakage_summary"][0]["leakage_bucket"] == "high"
    assert results["leakage_summary"][0]["routing_only_complete_at_1"] == 1.0


def test_evaluator_reports_track_metrics_for_routing_ambiguous_and_policy():
    from toolrouter.evaluator import evaluate_rankings

    endpoint_id = "fixture:ListProducts"
    tasks = [
        {
            "id": "route_1",
            "query": "route",
            "expected_endpoint_sequence": [endpoint_id],
            "expected_required_params": {},
            "allowed_alternatives": [],
            "task_type": "single_step",
            "leakage_bucket": "low",
        },
        {
            "id": "ambiguous_1",
            "query": "ambiguous",
            "expected_endpoint_sequence": [],
            "expected_required_params": {},
            "allowed_alternatives": [[endpoint_id]],
            "task_type": "ambiguous",
            "leakage_bucket": "medium",
        },
        {
            "id": "policy_1",
            "query": "policy",
            "expected_endpoint_sequence": [],
            "expected_required_params": {},
            "allowed_alternatives": [],
            "task_type": "policy_required",
            "leakage_bucket": "high",
        },
    ]
    rankings = {
        "grag_expand": {
            "all": {
                "route_1": [
                    {"endpoint_id": "fixture:WrongEndpoint", "score": 1.0, "required_params": []},
                    {"endpoint_id": endpoint_id, "score": 0.9, "required_params": []},
                ],
                "ambiguous_1": [],
                "policy_1": [],
            }
        }
    }

    results = evaluate_rankings(tasks, rankings, split_task_ids={"all": {task["id"] for task in tasks}}, k_values=[1, 10])
    k1 = next(row for row in results["summary"] if row["k"] == 1)
    k10 = next(row for row in results["summary"] if row["k"] == 10)

    assert k1["routing_task_count"] == 1
    assert k1["ambiguous_task_count"] == 1
    assert k1["policy_task_count"] == 1
    assert k1["routing_only_complete_at_1"] == 0.0
    assert k1["routing_only_complete_at_10"] == 1.0
    assert k10["routing_only_complete_at_1"] == 0.0
    assert k10["routing_only_complete_at_10"] == 1.0
    assert k1["ambiguous_abstention_accuracy"] == 1.0
    assert k1["policy_abstention_accuracy"] == 1.0
    assert k1["macro_average_by_track"] == 2.0 / 3.0
    assert {row["leakage_bucket"] for row in results["leakage_summary"]} == {"low", "medium", "high"}


def test_leakage_audit_outputs_overlap_buckets(tmp_path: Path):
    from toolrouter.leakage_audit import compute_task_leakage, write_leakage_audit
    from toolrouter.openapi_loader import load_openapi_specs

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    endpoint = bundle.endpoint_by_operation("ListStoreProducts")
    tasks = [
        {
            "id": "t1",
            "router_query": "ListStoreProducts list products",
            "expected_endpoint_sequence": [endpoint.id],
            "allowed_alternatives": [],
        },
        {
            "id": "t2",
            "router_query": "unrelated workflow",
            "expected_endpoint_sequence": [endpoint.id],
            "allowed_alternatives": [],
        },
    ]

    rows = compute_task_leakage(tasks, bundle)
    write_leakage_audit(tasks, bundle, tmp_path)

    assert rows[0]["overlap_bucket"] == "high"
    assert rows[1]["overlap_bucket"] == "low"
    assert rows[0]["operation_id_overlap"] > 0
    assert rows[0]["summary_overlap"] > 0
    assert (tmp_path / "leakage_audit.csv").exists()
    assert (tmp_path / "leakage_audit.json").exists()
    assert (tmp_path / "leakage_audit.md").exists()


def test_medusa_creds_parser_reads_required_values(tmp_path: Path):
    from toolrouter.medusa_smoke import parse_creds

    creds = tmp_path / "CREDS.md"
    creds.write_text(
        "\n".join(
            [
                "- Email: admin@example.test",
                "- Password: Secret123!",
                "- Backend URL: http://localhost:9000",
                "- Publishable API key: pk_test",
            ]
        ),
        encoding="utf-8",
    )

    parsed = parse_creds(creds)

    assert parsed.email == "admin@example.test"
    assert parsed.password == "Secret123!"
    assert parsed.backend_url == "http://localhost:9000"
    assert parsed.publishable_api_key == "pk_test"


def test_reports_write_markdown_files(tmp_path: Path):
    from toolrouter.reports import write_reports

    results = {
        "summary": [
            {
                "baseline": "rag_all_max",
                "split": "all",
                "k": 1,
                "endpoint_recall_at_k": 0.8,
                "complete_plan_recall_at_k": 0.7,
                "first_step_top1_accuracy": 0.6,
                "param_coverage": 0.9,
                "schema_validation_pass_rate": 1.0,
                "abstention_accuracy": 1.0,
                "latency_ms_mean": 12.0,
                "routing_only_complete_at_1": 0.7,
                "routing_only_complete_at_10": 0.7,
                "ambiguous_abstention_accuracy": 0.0,
                "policy_abstention_accuracy": 0.0,
                "macro_average_by_track": 0.23,
            },
            {
                "baseline": "grag_expand",
                "split": "all",
                "k": 5,
                "endpoint_recall_at_k": 0.8,
                "complete_plan_recall_at_k": 0.7,
                "first_step_top1_accuracy": 0.6,
                "param_coverage": 0.9,
                "schema_validation_pass_rate": 1.0,
                "abstention_accuracy": 1.0,
                "latency_ms_mean": 12.0,
                "routing_only_complete_at_1": 0.7,
                "routing_only_complete_at_10": 0.7,
                "ambiguous_abstention_accuracy": 0.0,
                "policy_abstention_accuracy": 0.0,
                "macro_average_by_track": 0.23,
            }
        ],
        "details": [
            {
                "baseline": "grag_expand",
                "task_id": "t1",
                "query": "list products",
                "failure_category": "none",
            }
        ],
    }

    write_reports(results, tmp_path)

    assert (tmp_path / "medusa_routing_results.md").exists()
    assert (tmp_path / "failure_analysis.md").exists()
    report = (tmp_path / "medusa_routing_results.md").read_text(encoding="utf-8")
    assert "Graph-Enriched RAG Baselines" in report
    assert report.index("GRAG_EXPAND") < report.index("RAG_ALL_MAX")
    assert "Routing@1" in report


def test_natural_tasks_generate_realistic_queries_without_router_metadata(tmp_path: Path):
    from toolrouter.openapi_loader import load_openapi_specs
    from toolrouter.tasks import generate_natural_tasks

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    tasks = generate_natural_tasks(bundle, min_count=3, task_prefix="natural")

    assert len(tasks) >= 3
    assert {task["track"] for task in tasks} == {"natural_routing"}
    assert all(task["expected_decision_type"] == "ROUTE" for task in tasks)
    assert all(task["router_query"] == task["query"] for task in tasks)
    forbidden = [
        "with required parameters",
        "with a valid request body",
        "as a dry run",
        "ListStoreProducts",
        "CreateStoreProduct",
        "GetStoreProduct",
    ]
    for task in tasks:
        for phrase in forbidden:
            assert phrase not in task["router_query"]
        assert len(task["router_query"].split()) <= 18
        assert "/" not in task["router_query"]
        assert "store products" not in task["router_query"].lower()
        assert task["expected_endpoint_sequence"]
        assert task["provenance"]["operationId"]
        assert "resource" in task
        assert "operation_class" in task
    get_task = next(task for task in tasks if task["provenance"]["operationId"] == "GetStoreProduct")
    assert "get" in get_task["router_query"].lower()


def test_generated_tracks_are_separated_for_smoke_and_low_overlap(tmp_path: Path):
    from toolrouter.openapi_loader import load_openapi_specs
    from toolrouter.tasks import generate_low_overlap_tasks, generate_tasks

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    smoke_tasks = generate_tasks(bundle, min_count=4, task_prefix="smoke")
    low_tasks = generate_low_overlap_tasks(bundle, min_routing=2, min_ambiguous=0, min_policy=1, task_prefix="low")

    assert {task["track"] for task in smoke_tasks} == {"spec_close_smoke"}
    assert {task["track"] for task in low_tasks} == {"low_overlap_stress"}
    assert all(task["expected_decision_type"] in {"ROUTE", "ASK_POLICY", "ASK_DISAMBIGUATE"} for task in low_tasks)


def test_recovery_tasks_generate_followup_decision_expectations(tmp_path: Path):
    from toolrouter.openapi_loader import load_openapi_specs
    from toolrouter.tasks import generate_recovery_tasks

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    tasks = generate_recovery_tasks(bundle, min_missing_param=1, min_ambiguous=1, min_policy=1, task_prefix="recovery")

    by_decision = {task["expected_decision_type"]: task for task in tasks}

    assert {"ASK_PARAM", "ASK_DISAMBIGUATE", "ASK_POLICY"} <= set(by_decision)
    assert by_decision["ASK_PARAM"]["expected_missing_params"]
    assert any(
        "title" in task.get("expected_missing_params", [])
        for task in tasks
        if task["expected_decision_type"] == "ASK_PARAM"
    )
    assert by_decision["ASK_DISAMBIGUATE"]["allowed_alternatives"]
    assert "OpenAPI defines possible actions" in by_decision["ASK_POLICY"]["expected_follow_up"]
    assert all(task["track"] == "recovery_followup" for task in tasks)


def test_product_decision_layer_routes_topk_and_param_followups(tmp_path: Path):
    from toolrouter.decision_router import DecisionConfig, route_product_query
    from toolrouter.graphgen import build_schema_graph
    from toolrouter.openapi_loader import load_openapi_specs
    from toolrouter.raggen import build_rag_corpus
    from toolrouter.retrieval_indices import build_retrieval_indices

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    indices = build_retrieval_indices(bundle, build_rag_corpus(bundle), build_schema_graph(bundle))

    route = route_product_query(
        "list product catalog items",
        bundle,
        indices,
        provided_params={"x-publishable-api-key": "pk"},
    )
    direct = route_product_query(
        "list product catalog items",
        bundle,
        indices,
        provided_params={"x-publishable-api-key": "pk"},
        config=DecisionConfig(route_confidence_threshold=0.0, route_margin_threshold=0.0),
    )
    missing = route_product_query("get product information", bundle, indices)
    body_missing = route_product_query("create a product", bundle, indices)
    ambiguous = route_product_query("work with products", bundle, indices)
    policy = route_product_query("only show products if the merchant policy allows it", bundle, indices)
    no_delete_unsafe = route_product_query("delete this product forever", bundle, indices)

    delete_bundle = load_openapi_specs([write_spec(tmp_path, fixture_with_delete(), "fixture_delete.yaml")])
    delete_indices = build_retrieval_indices(delete_bundle, build_rag_corpus(delete_bundle), build_schema_graph(delete_bundle))
    unsafe = route_product_query(
        "delete product",
        delete_bundle,
        delete_indices,
        provided_params={"id": "prod_123"},
        config=DecisionConfig(route_confidence_threshold=0.0, route_margin_threshold=0.0, unsafe_write_threshold=0.0),
    )

    assert route.decision_type in {"ROUTE", "SHOW_TOPK"}
    assert direct.decision_type == "ROUTE"
    assert route.top_candidates
    assert missing.decision_type == "ASK_PARAM"
    assert "id" in missing.missing_params
    assert "id" in missing.follow_up_question
    assert body_missing.decision_type == "ASK_PARAM"
    assert "title" in body_missing.missing_params
    assert "title" in body_missing.follow_up_question
    assert ambiguous.decision_type in {"SHOW_TOPK", "ASK_DISAMBIGUATE"}
    assert len(ambiguous.top_candidates) <= 3
    assert policy.decision_type == "ASK_POLICY"
    assert "OpenAPI defines possible actions" in policy.follow_up_question
    assert no_delete_unsafe.decision_type != "BLOCK_UNSAFE"
    assert unsafe.decision_type == "BLOCK_UNSAFE"


def test_feedback_log_schema_and_feedback_ranker_features(tmp_path: Path):
    from toolrouter.feedback import FeedbackEvent, feedback_adjustments, write_feedback_event

    log_path = tmp_path / "feedback_events.jsonl"
    write_feedback_event(
        log_path,
        FeedbackEvent(
            query="show products",
            decision_type="ROUTE",
            top_candidates=[{"endpoint_id": "fixture:ListStoreProducts", "score": 0.8}],
            selected_endpoint="fixture:ListStoreProducts",
            confidence=0.8,
            missing_params=[],
            follow_up_question="",
            user_selected_endpoint="fixture:ListStoreProducts",
            corrected_endpoint=None,
            rejected_endpoints=["fixture:CreateStoreProduct"],
            validation_result={"validation_pass": 1.0},
            execution_result={"status": "dry_run"},
            source="test",
        ),
    )

    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    adjustments = feedback_adjustments(log_path)

    assert rows[0]["query"] == "show products"
    assert rows[0]["timestamp"]
    assert adjustments["fixture:ListStoreProducts"]["previous_successful_usage_count"] == 1
    assert adjustments["fixture:CreateStoreProduct"]["previous_rejection_count"] == 1


def test_feedback_ranker_training_and_application(tmp_path: Path):
    from toolrouter.decision_router import product_score_maps
    from toolrouter.feedback import (
        FeedbackEvent,
        apply_feedback_model_scores,
        load_feedback_ranker,
        train_feedback_ranker,
        write_feedback_event,
    )
    from toolrouter.graphgen import build_schema_graph
    from toolrouter.openapi_loader import load_openapi_specs
    from toolrouter.raggen import build_rag_corpus
    from toolrouter.retrieval_indices import build_retrieval_indices

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    indices = build_retrieval_indices(bundle, build_rag_corpus(bundle), build_schema_graph(bundle))
    log_path = tmp_path / "feedback_events.jsonl"
    write_feedback_event(
        log_path,
        FeedbackEvent(
            query="show products",
            decision_type="ROUTE",
            top_candidates=[
                {"endpoint_id": "fixture:CreateStoreProduct", "score": 0.9},
                {"endpoint_id": "fixture:ListStoreProducts", "score": 0.4},
            ],
            selected_endpoint="fixture:CreateStoreProduct",
            confidence=0.9,
            missing_params=[],
            follow_up_question="",
            corrected_endpoint="fixture:ListStoreProducts",
            rejected_endpoints=["fixture:CreateStoreProduct"],
            validation_result={"validation_pass": 1.0},
            execution_result={"status": "dry_run"},
            source="test",
        ),
    )
    out = tmp_path / "feedback_ranker.joblib"

    manifest = train_feedback_ranker(log_path, bundle, out)
    model = load_feedback_ranker(out)
    score_maps = product_score_maps("show products", bundle, indices)
    model_scores = apply_feedback_model_scores(
        "show products",
        bundle,
        ["fixture:CreateStoreProduct", "fixture:ListStoreProducts"],
        score_maps,
        model,
        feedback_log=log_path,
    )

    assert manifest["model_status"] == "trained"
    assert out.exists()
    assert (tmp_path / "feedback_ranker.manifest.json").exists()
    assert model_scores["fixture:ListStoreProducts"] > model_scores["fixture:CreateStoreProduct"]


def test_feedback_ranker_reports_insufficient_data(tmp_path: Path):
    from toolrouter.feedback import FeedbackEvent, train_feedback_ranker, write_feedback_event
    from toolrouter.openapi_loader import load_openapi_specs

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    log_path = tmp_path / "feedback_events.jsonl"
    write_feedback_event(
        log_path,
        FeedbackEvent(
            query="show products",
            decision_type="ROUTE",
            top_candidates=[{"endpoint_id": "fixture:ListStoreProducts", "score": 0.8}],
            selected_endpoint="fixture:ListStoreProducts",
            confidence=0.8,
            missing_params=[],
            follow_up_question="",
            source="test",
        ),
    )

    manifest = train_feedback_ranker(log_path, bundle, tmp_path / "feedback_ranker.joblib")

    assert manifest["model_status"] == "insufficient_data"
    assert not (tmp_path / "feedback_ranker.joblib").exists()


def test_product_readiness_benchmark_and_reports(tmp_path: Path):
    from toolrouter.decision_router import evaluate_product_readiness
    from toolrouter.graphgen import build_schema_graph
    from toolrouter.openapi_loader import load_openapi_specs
    from toolrouter.raggen import build_rag_corpus
    from toolrouter.reports import write_reports
    from toolrouter.retrieval_indices import build_retrieval_indices
    from toolrouter.tasks import generate_natural_tasks, generate_recovery_tasks

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    indices = build_retrieval_indices(bundle, build_rag_corpus(bundle), build_schema_graph(bundle))
    tasks = generate_natural_tasks(bundle, min_count=3, task_prefix="natural")
    tasks.extend(generate_recovery_tasks(bundle, min_missing_param=1, min_ambiguous=1, min_policy=1, task_prefix="recovery"))

    feedback_log = tmp_path / "feedback_events.jsonl"
    results = evaluate_product_readiness(tasks, bundle, indices, write_feedback_log=None)
    write_reports(results, tmp_path)

    assert "product_summary" in results
    assert not feedback_log.exists()
    assert {row["track"] for row in results["product_summary"]} >= {"natural_routing", "recovery_followup"}
    assert any("natural_top1_route_accuracy" in row for row in results["product_summary"])
    assert any("correct_followup_type" in row for row in results["product_summary"])
    assert (tmp_path / "product_readiness.md").exists()
    assert (tmp_path / "natural_routing.md").exists()
    assert (tmp_path / "recovery_followup.md").exists()
    assert (tmp_path / "feedback_learning.md").exists()
    assert (tmp_path / "decision_calibration.md").exists()

    required_detail_fields = {
        "query",
        "expected_decision_type",
        "decision_type",
        "expected_endpoint_sequence",
        "selected_endpoint",
        "top_candidates",
        "confidence",
        "margin",
        "missing_params",
        "unsafe_flag",
        "validation_result",
        "decision_reason",
    }
    assert required_detail_fields <= set(results["product_details"][0])
    assert results["selected_decision_config"]["selected_from"] == "dev"
    assert "decision_calibration" in results
    assert "decision_confusion" in results


def test_decision_confusion_matrix_includes_requested_pairs():
    from toolrouter.product_calibration import decision_confusion_rows

    rows = decision_confusion_rows(
        [
            {"expected_decision_type": "ROUTE", "decision_type": "SHOW_TOPK"},
            {"expected_decision_type": "ASK_PARAM", "decision_type": "ASK_DISAMBIGUATE"},
        ]
    )
    by_pair = {(row["expected_decision_type"], row["decision_type"]): row["count"] for row in rows}

    assert by_pair[("ROUTE", "SHOW_TOPK")] == 1
    assert by_pair[("ROUTE", "ASK_PARAM")] == 0
    assert by_pair[("ROUTE", "BLOCK_UNSAFE")] == 0
    assert by_pair[("ASK_PARAM", "ASK_DISAMBIGUATE")] == 1
    assert by_pair[("ASK_POLICY", "ASK_DISAMBIGUATE")] == 0


def test_decision_config_tuning_uses_dev_rows_only():
    from toolrouter.decision_router import DecisionConfig
    from toolrouter.product_calibration import select_decision_config_from_rows

    configs = [
        DecisionConfig(
            name="bad_dev",
            route_confidence_threshold=0.0,
            route_margin_threshold=0.0,
            param_confidence_threshold=0.0,
            show_topk_confidence_threshold=0.0,
            unsafe_write_threshold=0.0,
        ),
        DecisionConfig(
            name="good_dev",
            route_confidence_threshold=0.9,
            route_margin_threshold=0.0,
            param_confidence_threshold=0.0,
            show_topk_confidence_threshold=0.0,
            unsafe_write_threshold=0.9,
        ),
    ]
    rows_by_config = {
        "bad_dev": [
            {"task_id": "dev_1", "track": "natural_routing", "expected_decision_type": "SHOW_TOPK", "decision_type": "ROUTE", "expected_endpoint_sequence": ["e1"], "top_candidate_ids": ["e1"], "false_execution": 1.0, "false_overclarification": 0.0},
            {"task_id": "test_1", "track": "natural_routing", "expected_decision_type": "ROUTE", "decision_type": "ROUTE", "expected_endpoint_sequence": ["e1"], "top_candidate_ids": ["e1"], "false_execution": 0.0, "false_overclarification": 0.0},
        ],
        "good_dev": [
            {"task_id": "dev_1", "track": "natural_routing", "expected_decision_type": "SHOW_TOPK", "decision_type": "SHOW_TOPK", "expected_endpoint_sequence": ["e1"], "top_candidate_ids": ["e1"], "false_execution": 0.0, "false_overclarification": 0.0},
            {"task_id": "test_1", "track": "natural_routing", "expected_decision_type": "ROUTE", "decision_type": "SHOW_TOPK", "expected_endpoint_sequence": ["e1"], "top_candidate_ids": ["e1"], "false_execution": 0.0, "false_overclarification": 1.0},
        ],
    }

    selected, ablation = select_decision_config_from_rows(configs, rows_by_config, {"dev_1"})

    assert selected.name == "good_dev"
    assert {row["scope"] for row in ablation} == {"dev"}
    assert all(row["task_count"] == 1 for row in ablation)


def test_missing_param_wins_over_unsafe_and_non_delete_writes_are_not_blocked(tmp_path: Path):
    from toolrouter.decision_router import DecisionConfig, route_product_query
    from toolrouter.graphgen import build_schema_graph
    from toolrouter.openapi_loader import load_openapi_specs
    from toolrouter.raggen import build_rag_corpus
    from toolrouter.retrieval_indices import build_retrieval_indices

    delete_bundle = load_openapi_specs([write_spec(tmp_path, fixture_with_delete(), "fixture_delete.yaml")])
    delete_indices = build_retrieval_indices(delete_bundle, build_rag_corpus(delete_bundle), build_schema_graph(delete_bundle))
    config = DecisionConfig(route_confidence_threshold=0.0, route_margin_threshold=0.0, unsafe_write_threshold=0.0)

    missing_delete_param = route_product_query("delete product", delete_bundle, delete_indices, config=config)
    create_write = route_product_query(
        "create a product",
        delete_bundle,
        delete_indices,
        provided_params={"title": "Shirt"},
        config=config,
    )

    assert missing_delete_param.decision_type == "ASK_PARAM"
    assert "id" in missing_delete_param.follow_up_question
    assert create_write.decision_type != "BLOCK_UNSAFE"


def test_followup_templates_include_action_context(tmp_path: Path):
    from toolrouter.decision_router import DecisionConfig, route_product_query
    from toolrouter.graphgen import build_schema_graph
    from toolrouter.openapi_loader import load_openapi_specs
    from toolrouter.raggen import build_rag_corpus
    from toolrouter.retrieval_indices import build_retrieval_indices

    bundle = load_openapi_specs([write_spec(tmp_path, fixture_with_delete(), "fixture_delete.yaml")])
    indices = build_retrieval_indices(bundle, build_rag_corpus(bundle), build_schema_graph(bundle))

    ask_param = route_product_query("get product information", bundle, indices)
    disambiguate = route_product_query("product", bundle, indices, config=DecisionConfig(route_confidence_threshold=1.0))
    policy = route_product_query("only show products if the merchant policy allows it", bundle, indices)
    unsafe = route_product_query(
        "delete product",
        bundle,
        indices,
        provided_params={"id": "prod_123"},
        config=DecisionConfig(route_confidence_threshold=0.0, route_margin_threshold=0.0, unsafe_write_threshold=0.0),
    )

    assert "GET /store/products/{id}" in ask_param.follow_up_question
    assert "id" in ask_param.follow_up_question
    assert "GET /store/products" in disambiguate.follow_up_question or "POST /store/products" in disambiguate.follow_up_question
    assert "OpenAPI exposes possible actions" in policy.follow_up_question
    assert "business policy" in policy.follow_up_question
    assert "confirmation" in unsafe.follow_up_question or "dry-run" in unsafe.follow_up_question


def test_synthetic_feedback_experiment_is_offline_and_separate(tmp_path: Path):
    from toolrouter.decision_router import evaluate_product_readiness
    from toolrouter.graphgen import build_schema_graph
    from toolrouter.openapi_loader import load_openapi_specs
    from toolrouter.raggen import build_rag_corpus
    from toolrouter.retrieval_indices import build_retrieval_indices
    from toolrouter.tasks import generate_natural_tasks, generate_recovery_tasks

    bundle = load_openapi_specs([write_fixture(tmp_path)])
    indices = build_retrieval_indices(bundle, build_rag_corpus(bundle), build_schema_graph(bundle))
    tasks = generate_natural_tasks(bundle, min_count=3, task_prefix="natural")
    tasks.extend(generate_recovery_tasks(bundle, min_missing_param=1, min_ambiguous=1, min_policy=1, task_prefix="recovery"))
    real_feedback = tmp_path / "feedback_events.jsonl"
    synthetic_feedback = tmp_path / "synthetic_feedback_events.jsonl"
    synthetic_model = tmp_path / "synthetic_feedback_ranker.joblib"

    results = evaluate_product_readiness(
        tasks,
        bundle,
        indices,
        feedback_log=real_feedback,
        synthetic_feedback_out=synthetic_feedback,
        synthetic_feedback_model=synthetic_model,
    )

    experiment = results["synthetic_feedback_experiment"]
    assert not real_feedback.exists()
    assert synthetic_feedback.exists()
    assert experiment["source"] == "synthetic_offline"
    assert experiment["event_count"] > 0
    assert "before" in experiment
    assert "after" in experiment


def test_product_readiness_keeps_low_overlap_separate_in_reports(tmp_path: Path):
    from toolrouter.reports import write_reports

    results = {
        "mode": "product_readiness",
        "product_summary": [
            {
                "track": "natural_routing",
                "task_count": 1,
                "routing_task_count": 1,
                "followup_task_count": 0,
                "natural_top1_route_accuracy": 0.6,
                "natural_top3_recoverability": 0.8,
                "natural_top10_candidate_recall": 0.9,
                "correct_decision_type": 0.7,
                "correct_followup_type": 0.0,
                "required_param_question_accuracy": 0.0,
                "policy_gap_detection_accuracy": 1.0,
                "false_execution_rate": 0.0,
                "false_overclarification_rate": 0.0,
                "feedback_recovery_rate": 0.0,
                "validation_pass_rate": 0.6,
                "latency_ms": 1.0,
            },
            {
                "track": "low_overlap_stress",
                "task_count": 1,
                "routing_task_count": 1,
                "followup_task_count": 0,
                "natural_top1_route_accuracy": 0.1,
                "natural_top3_recoverability": 0.2,
                "natural_top10_candidate_recall": 0.3,
                "correct_decision_type": 0.1,
                "correct_followup_type": 0.0,
                "required_param_question_accuracy": 0.0,
                "policy_gap_detection_accuracy": 1.0,
                "false_execution_rate": 0.0,
                "false_overclarification_rate": 0.0,
                "feedback_recovery_rate": 0.0,
                "validation_pass_rate": 0.1,
                "latency_ms": 1.0,
            },
        ],
        "product_details": [],
        "feedback_learning": {"feedback_event_count": 0, "model_status": "not_loaded", "feature_names": []},
    }

    write_reports(results, tmp_path)
    report = (tmp_path / "product_readiness.md").read_text(encoding="utf-8")

    assert "natural_routing" in report
    assert "low_overlap_stress" in report
    assert report.index("natural_routing") < report.index("low_overlap_stress")
