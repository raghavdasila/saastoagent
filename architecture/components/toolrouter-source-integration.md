# Sources And ToolRouter Integration

Status: implemented and locally validated through JSON and YAML on 2026-07-24

## Purpose

Corpus has one product feature named **Sources**. API collections are one
connector inside it. The ToolRouter snapshot is an integration dependency of
that connector, not a product feature and not a runtime dependency on the
sibling checkout.

This separation lets a later database connector own SQL metadata, retrieval,
and evalset construction without pretending it is OpenAPI. It also lets a
future ToolRouter/GRAG implementation replace the current snapshot without
changing Source identity, RouteDeck navigation, HTTP ownership, or the debug
surface contract.

## Standalone Source Hub suite

`D:\Dev\AI Projects\source-hub-runtime` is a separately proven Source Hub/API
Source suite. It combines source lifecycle, durable ToolRouter processing,
semantic graph presentation, encrypted API connections, the sibling API
execution runtime, response-schema mismatch decisions and corrected OpenAPI
schema lineage.

Corpus does not currently import that suite. Its standalone host identity,
FastAPI composition, React page, Huey choice and no-attachments usage adapter
are proof infrastructure, not Corpus integration contracts. The future mapping
must reconcile its use cases with the existing generic `SourceService`, this
repository's `ApiSourceEngine` bridge and one authoritative ToolRouter
snapshot. The detailed boundary and launch-feature coverage live in
`docs/standalone-source-hub-integration.md`.

```text
RouteDeck sources.home + /api/sources
  -> app/source_composition.py (concrete registration only)
    -> SourceService (generic source lifecycle)
      -> SourceConnector registry
        -> connectors/api/connector.py (API lifecycle + engine port)
          -> connectors/api/toolrouter.py (explicit bridge)
            -> ToolRouterAdapter (one Corpus integration facade)
              -> private vendored engine snapshot
```

The dependency arrow never points upward. Generic Sources files and the core
API connector do not import `corpus.integrations.toolrouter`; a boundary test
permits that import only in the explicit API/ToolRouter bridge. Host-level
composition may import the public ToolRouter facade to instantiate it.

## Configuration Ownership

Configuration values are defined and parsed by their owning boundary:

```text
SourceSettings
  -> required connector-neutral persistence root only

ApiSourceSettings
  -> API collection upload limit only

ToolRouterSettings
  -> embedding model/revision/device/batch/local-only
  -> ToolRouter Ollama URL
  -> evalset generator/reviewer models and timeout
```

`CorpusRuntimeSettings` composes these typed settings objects but does not copy
their fields or defaults. `app/source_composition.py` passes each object to its
owner. The Source data root has no code default: local setup writes the
explicit `CORPUS_SOURCE_DATA_ROOT` value.

In Docker development, Compose supplies ToolRouter-owned environment names
directly and points `CORPUS_TOOLROUTER_OLLAMA_URL` at the external host service
`http://host.docker.internal:11434`. The evalset engine accepts an explicitly
configured HTTP hostname with an explicit port; it no longer assumes the
provider hostname must be loopback. This is an environment-boundary adaptation
inside the private ToolRouter snapshot, is recorded in `SOURCE.md` and the
source manifest, and does not add a fallback provider or move model values into
generic Sources configuration.

## Product Path

```text
authenticated owner
  -> Sources debug node
  -> validated JSON/YAML API upload
  -> processing source revision persisted
  -> OpenAPI normalization and declared repair policy
  -> resource_first_v1 graph + conformance trace
  -> pinned local MiniLM embeddings persisted
  -> ready source revision
  -> GRAG retrieval from reloaded graph/index
  -> optional source-grounded evalset run
  -> local Gemma generator -> deterministic checks -> local Qwen reviewer
  -> accepted export or explicit quarantine/failure
```

## Sources Feature Files

Each file has one owner so adding connector families does not create a central
file full of API-, database-, Slack-, or channel-specific branches.

| File | Responsibility | Why this boundary exists |
| --- | --- | --- |
| `features/sources/__init__.py` | Curated feature-facing exports. | Callers get one stable import surface instead of reaching into storage, HTTP, or connector internals. |
| `features/sources/config.py` | Required connector-neutral Source persistence root loaded from the local environment. | Generic Sources cannot accumulate connector limits, models, or provider choices. |
| `features/sources/contracts.py` | Connector-neutral ranked-item, retrieval-step/result, trace, and evalset result dataclasses. | Generic Sources consumers must not learn API endpoint vocabulary or ToolRouter artifact locations. |
| `features/sources/errors.py` | Connector-neutral input, dependency, artifact, and integration failures. | HTTP can preserve failure semantics without importing one connector implementation. |
| `features/sources/models.py` | Source, revision, view, prepared-source, timestamp, and lifecycle-state models. | Source identity and state are common to every future connector. |
| `features/sources/repository.py` | Owner-scoped compact paths, immutable revision creation, atomic metadata/input writes, reads, and processing-to-ready/failed transitions. | Persistence and tenancy are not parser responsibilities; a future storage adapter can replace this repository. |
| `features/sources/service.py` | Connector registry and create/list/get/retrieve/generate-evalset use cases. | Product orchestration dispatches by registered connector key without a hardcoded source-family switch. |
| `features/sources/declarations.py` | `sources.home` node, route, operations, and debug-surface declarations. | RouteDeck topology remains declarative and separate from execution handlers. |
| `features/sources/feature.py` | Compiled Sources feature definition and operation legality. | Composition can include one Sources feature without copying its declarations. |
| `features/sources/bindings.py` | Handlers for owner Home to Sources and Sources back to Home. | Navigation effects are feature-owned while RouteDeck owns transition validation and state. |
| `features/sources/http.py` | Authenticated same-origin list, get, retrieve, and evalset routes. | Generic transport has no upload schema, connector key, or API-specific error vocabulary. |
| `features/sources/http_common.py` | Owner resolution, mutation authorization, thread offload, generic failure mapping, and response serialization shared by Source routers. | Connector-owned routers reuse consistent host policy without importing generic route declarations or duplicating transport mechanics. |
| `features/sources/connectors/__init__.py` | Curated generic connector exports. | Prevents callers from importing connector implementations accidentally. |
| `features/sources/connectors/base.py` | `SourceConnector` protocol plus raw/validated upload values. | Each connector can implement its own ingestion, retrieval, and evalset behavior behind the same use-case boundary. |
| `features/sources/connectors/api/__init__.py` | API connector's narrow exports. | API-specific classes stay under the API connector folder. |
| `features/sources/connectors/api/config.py` | API collection upload-size configuration. | Connector-specific transport limits do not pollute generic Source settings. |
| `features/sources/connectors/api/engine.py` | `ApiSourceEngine` parser/retrieval/evalset protocol. | The connector depends on a replaceable API-engine port instead of a concrete ToolRouter adapter. |
| `features/sources/connectors/api/http.py` | Multipart `/api/sources/api` creation route and API upload problems. | API form fields, byte limits, connector key, and upload vocabulary remain connector-owned. |
| `features/sources/connectors/api/intake.py` | Filename, extension, size, empty-file, content-type, JSON/YAML, and top-level object validation. | Hostile or malformed bytes are rejected before repository creation or ToolRouter execution. |
| `features/sources/connectors/api/connector.py` | Implements `SourceConnector` and delegates API work to `ApiSourceEngine`. | API lifecycle stays stable while graph/retrieval engines are replaced independently. |
| `features/sources/connectors/api/toolrouter.py` | Implements `ApiSourceEngine` by translating ToolRouter requests, results, and failures. | Exactly one explicit bridge knows both the API engine port and the public ToolRouter facade. |

## Composition And Shared Files

| File | Responsibility | Why this boundary exists |
| --- | --- | --- |
| `app/source_composition.py` | Registers the API connector, ToolRouter engine bridge, generic Source router, and API-owned upload router. | Concrete dependency selection belongs at the host composition root rather than inside a reusable feature. |
| `runtime/config.py` | Composes the settings objects defined by Sources, the API connector, ToolRouter, auth, host, and primary chat runtime. | The application assembles owners without duplicating their fields or values. |
| `shared/environment.py` | Reads only an owner-supplied allowlist from an env file and process environment. | Settings packages share parsing mechanics while retaining ownership of names, defaults, and validation. |

### Connector Growth Example

A database connector belongs at `connectors/database/`. It can implement
schema discovery, its own graph/index or retrieval adapter, and database-based
evalset truth without modifying `SourceService`, `repository.py`, or the HTTP
routes. The existing API connector remains unchanged. Slack, WhatsApp, and
phone calls are channel examples, not Source connectors, and therefore do not
belong in this tree.

## ToolRouter Adapter Files

| File | Responsibility | Why this boundary exists |
| --- | --- | --- |
| `integrations/toolrouter/__init__.py` | The only supported ToolRouter public exports. | Features never import the private engine snapshot. |
| `integrations/toolrouter/settings.py` | Immutable defaults, environment names/loading, and validation for embedding, ToolRouter Ollama, generator/reviewer models, and timeout. | Every ToolRouter runtime value has one owner and the adapter receives one explicit dependency object. |
| `integrations/toolrouter/contracts.py` | ToolRouter-specific ingest, ranked-endpoint, retrieval, trace, and evalset requests/results. | Engine dataclasses and filesystem details do not leak through the facade. |
| `integrations/toolrouter/errors.py` | Input, dependency, artifact, and base integration exceptions. | Failure category survives engine translation and can be translated once more by a connector. |
| `integrations/toolrouter/serialization.py` | Atomic graph JSON, NumPy embedding, and reconstructed-index persistence. | Artifact format and reload rules stay beside the integration rather than in Sources. |
| `integrations/toolrouter/adapter.py` | `ToolRouterAdapter.ingest`, `retrieve`, and `generate_evalset`; model digest resolution; artifact layout; result translation. | It is the single replaceable facade around upstream algorithms and the only non-engine file allowed to coordinate them. |
| `integrations/toolrouter/SOURCE.md` | Source checkout, commit, dirty-snapshot warning, reference command/results, inclusion, and license boundary. | A copied algorithm must remain traceable and redistributability must not be implied. |
| `integrations/toolrouter/source_manifest.json` | Exact source and vendored SHA-256 for 24 modules and the recipe pack. | The dirty upstream worktree means commit ID alone cannot identify the copied bytes. |
| `integrations/toolrouter/recipes/v1.json` | Versioned generator recipe definitions used by the evalset factory. | Prompt/acceptance recipes are data with their own immutable hash and resume identity. |

## Private Engine Snapshot Files

Nothing outside `corpus.integrations.toolrouter` may import these files.

| File | Responsibility | Why it remains private |
| --- | --- | --- |
| `engine/__init__.py` | Marks the namespaced snapshot package without re-exporting algorithms. | An empty package surface discourages feature imports. |
| `engine/openapi_loader.py` | Loads JSON/YAML OpenAPI/Swagger inputs, validates, normalizes endpoints/schemas/security, and writes the normalized bundle. | Parser structures are upstream implementation detail. |
| `engine/spec_repair.py` | Applies the declared default-value repair policy and records repairs. | Repair policy must stay coupled to upstream validation behavior. |
| `engine/semantic_schema_graph.py` | Resolves canonical schemas, fields, relations, shapes, and warnings. | Resource/schema analysis is an internal graph-construction stage. |
| `engine/semantic_graph.py` | Builds field-first/resource-first nodes, edges, evidence, cards, and graph traces. | The graph representation may change while Source contracts remain stable. |
| `engine/semantic_graph_conformance.py` | Builds and asserts staged graph invariant reports. | Conformance is engine validity evidence, not a UI contract. |
| `engine/semantic_graph_retrieval.py` | Embedding providers, persisted semantic index, graph heat propagation, endpoint scoring, optional expansion/reranking, and semantic-only routing. | Retrieval internals and provider protocols stay replaceable behind the adapter. |
| `engine/semantic_grag_router.py` | Converts semantic retrieval into decomposed plans and explicit route/ask/no-tool/abstain decisions with traces. | Decision mechanics are the experimental GRAG implementation. |
| `engine/semantic_outcomes.py` | Outcome values, thresholds, ambiguity, missing-parameter, and decision-evidence policy. | Sources exposes results but does not own ToolRouter's routing policy. |
| `engine/semantic_natural.py` | Produces natural-language graph/card representations used for semantic matching. | Text construction is coupled to upstream scoring behavior. |
| `engine/semantic_validation.py` | Semantic validation contracts and validation orchestration. | Validation implementation is upstream algorithm code. |
| `engine/semantic_validation_io.py` | Atomic validation report serialization. | Keeps validation evidence format with its producer. |
| `engine/tasks.py` | Source-grounded task/query helpers and endpoint truth/provenance utilities. | Task construction is engine support; the adapter selects only categories it can prove. |
| `engine/leakage_audit.py` | Measures lexical/path overlap and attaches leakage evidence to tasks. | Leakage diagnostics are evalset research evidence, not Source metadata. |
| `engine/ladder_llm.py` | Stable hashes, JSONL audit helpers, query canonicalization, and reranking helpers. | These are upstream LLM-audit dependencies, not a second product model adapter. |
| `engine/ladder_runtime.py` | Ladder runtime configuration and hardware/package probes. | Retained only as an upstream dependency closure; Corpus runtime configuration remains separate. |
| `engine/evalset_factory_contracts.py` | Recipe, candidate, verdict, token usage, and context-strategy contracts. | Factory-internal identity must remain stable for resume and audit. |
| `engine/evalset_factory_seed.py` | Derives source-grounded OpenAPI seed tasks and dependency fields. | Truth construction stays tied to normalized endpoints/schemas. |
| `engine/evalset_factory_generation.py` | Builds generator context/hints and calls the configured local Ollama generator with cache/audit evidence. | Generation must preserve exact upstream prompt and token-accounting semantics. |
| `engine/evalset_factory_validation.py` | Deterministic checks, review packets, and independent local Ollama semantic review. | Review is deliberately independent from generation and must not be folded into one convenience call. |
| `engine/evalset_factory_experiment.py` | Runs/resumes completion keys, writes progress/candidates/reviews/audits/ledger, and produces summaries. | The experiment is the atomic audited orchestration unit. |
| `engine/evalset_factory_export.py` | Builds and writes accepted tasks plus provenance manifest. | Only accepted reviewed candidates enter the export; quarantine remains separate. |
| `engine/evalset_factory_freeze.py` | Freezes and verifies immutable experiment configuration identity. | Resume cannot silently change model, recipe, source, or run parameters. |
| `engine/evalset_factory_isolation.py` | Builds allowlisted isolated experiment inputs and verifies frozen source identities. | Evaluation data cannot reach undeclared files or silently change inputs. |
| `engine/evalset_factory_folds.py` | Aggregates completed run artifacts into collection folds and Pareto summaries. | Retained as part of the upstream factory/report closure, not exposed to Sources. |

## Frontend Files

| File | Responsibility | Why this boundary exists |
| --- | --- | --- |
| `frontend/src/features/sources/sourceClient.ts` | Typed same-origin API calls, multipart upload, structured failures, retrieval, and evalset requests. | Network details are testable without coupling the surface to fetch response shapes. |
| `frontend/src/features/sources/SourceDebugSurface.tsx` | Owner debug workflow: JSON/YAML upload/list/select, metrics, retrieval inspector, evalset inspector, and an explicit upload -> graph/index -> retrieval -> reviewed-evalset progress rail with busy/error/quarantine states. | The deliberately temporary debug experience stays feature-owned, makes the complete ToolRouter proof legible, and can be replaced by Agent Designer later. |
| `frontend/src/features/sources/sources.css` | Sources-only desktop/mobile layout, four-stage progress rail, and evidence styling. | Connector UI styling does not leak into the generic Corpus shell, while the rail collapses independently from four columns to one. |
| `frontend/src/routedeck/surfaces.tsx` | Registers `sources.debug` to the Sources component. | The registry maps a RouteDeck projection to a feature surface but owns no Source behavior. |

## Persistence

```text
.runtime/sources/<owner-hash>/<source-id>/
  source.json
  r/<revision-id>/
    revision.json
    i/<original-filename>
    a/
      normalized/
      graph/
      integration_manifest.json
      c/
      e/<evalset-hash>/
```

Owner directories are SHA-256-derived opaque prefixes. Source and revision IDs
are independently generated 96-bit URL-safe tokens. Evalset labels are never
path segments. Metadata writes replace `.tmp` files atomically. An owner cannot
distinguish another owner's source from a missing source.

## Failure Semantics

- Upload validation fails before Source identity is created.
- After revision creation, any ingestion failure persists a `failed` revision
  with an explicit safe code/message; it never appears ready.
- Retrieval requires a ready revision and existing graph/index artifacts.
- Missing MiniLM, Ollama, model digest, parser, graph, or artifact fails loudly.
- Evalset failure does not downgrade an already-ready source revision.
- Zero accepted candidates are `quarantined`; accepted output is never called
  gold and engine `run_dir` paths are not exposed by HTTP.
- The adapter has no alternate parser, provider, model, cached product result,
  fixture, canned response, or heuristic success branch.

## Test Owners

| Test file | Contract protected |
| --- | --- |
| `backend/tests/integrations/toolrouter/test_engine_snapshot.py` | Source hashes, manifest completeness, namespaced imports, and no sibling runtime import. |
| `test_adapter_ingestion.py` | Normalization, graph/conformance/index artifacts, and reload. |
| `test_adapter_retrieval.py` | Fresh-adapter artifact reload, explicit decision, ranking, and trace. |
| `test_adapter_evalsets.py` | Generator/reviewer orchestration, digest identity, resume, quarantine/export, and token ledger. |
| `backend/tests/sources/test_repository.py` | Owner isolation, compact safe paths, immutable IDs, atomic lifecycle persistence. |
| `test_api_connector.py` | Upload boundary and ToolRouter-to-Source translation. |
| `test_service.py` | Registry dispatch and processing/ready/failed transitions. |
| `test_feature.py` | RouteDeck node, route, and operation contract. |
| `test_http.py` | Auth, origin, cross-owner 404, upload/retrieval/evalset transport. |
| `test_api_connector.py` | Upload boundary, engine delegation, ToolRouter bridge translation, and import/HTTP ownership rules. |
| `test_config.py` | Explicit generic storage and API connector configuration ownership. |
| `backend/tests/integrations/toolrouter/test_settings.py` | ToolRouter-only environment ownership and parsing. |
| `frontend/src/tests/source-debug-surface.test.tsx` | Rendered component contract and real client interaction shapes. |

## Current Claim Boundary

This proves Sources can turn an API collection into persisted ToolRouter
artifacts, retrieve from them, and create independently reviewed evalset
candidates. It does not prove Agent Designer, agent execution, Sandbox, public
Web, deployment, background workers, or production storage. Semantic GRAG
remains explicitly experimental.

The rendered evidence surface was also exercised with the real Ory Kratos
`api.yaml`: 56 endpoints produced 477 nodes, 876 edges, and 477 cards;
`create a new identity` returned `ASK_DISAMBIGUATE`; and `api-debug-v1`
completed and accepted one independently reviewed candidate with zero
quarantined candidates.
