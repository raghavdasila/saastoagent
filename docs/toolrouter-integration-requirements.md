# ToolRouter Integration Requirements

Status: implemented and locally validated on 2026-07-23

## Owner Instructions

Corpus must bring the current authoritative ToolRouter capabilities from
`D:\Dev\AI Projects\openapi-toolrouter-benchmark` into the application. The
integration must include API collection upload, OpenAPI normalization, the
resource-first semantic graph/GRAG, retrieval, and evalset generation/review.
It must expose a usable owner-only debug mode now because the final Agent
Designer surface is deliberately deferred.

The copied ToolRouter implementation must remain isolated, replaceable, and
available through clean exports so Sources, Sandbox, Evaluation, and future
agent features do not import benchmark modules directly. Earlier design
notebook work must be committed separately before this implementation. Active
authentication and UI-refactor work must not be swept into that earlier
commit.

## Required Product Path

```text
authenticated owner
  -> Sources RouteDeck node
  -> upload one JSON/YAML OpenAPI collection
  -> immutable source revision is created
  -> ToolRouter normalizes the collection
  -> resource-first semantic graph and local embedding index are built
  -> owner enters a retrieval query
  -> GRAG returns an explicit decision, ranked endpoints, and trace evidence
  -> owner starts an evalset factory run
  -> Gemma generates source-grounded candidate queries
  -> Qwen independently reviews them
  -> accepted candidates are exported; rejected candidates remain quarantined
```

## Scope

### Included

- A generic Sources feature. API is a connector under Sources, not a top-level
  product node or a hardcoded generic-source type switch.
- An owner-authenticated `sources.home` RouteDeck node and debug surface.
- Upload of one OpenAPI JSON, YAML, or YML file per source revision.
- File size, extension, empty-input, filename, and parse validation.
- Immutable owner-scoped local source/revision artifacts.
- The authoritative ToolRouter OpenAPI loader and default-invalid repair
  policy.
- `resource_first_v1` semantic graph construction and conformance checks.
- Local `sentence-transformers/all-MiniLM-L6-v2` embeddings pinned to revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`.
- Persisted graph and embedding artifacts that can be reloaded after restart.
- GRAG retrieval with the five ToolRouter outcomes: `ROUTE`,
  `ASK_DISAMBIGUATE`, `ASK_PARAM`, `NO_TOOL`, and `ABSTAIN`.
- Bounded and full diagnostic trace modes.
- The ToolRouter evalset factory generator, deterministic validation,
  independent semantic reviewer, resume identity, token ledger, summary, and
  accepted-candidate export.
- A first product task-builder mode that creates source-grounded `paraphrase`
  truth tasks for real endpoints. The adapter accepts an explicit category
  list, but rejects categories for which it cannot construct source-backed
  truth rather than inventing evidence.
- Clean feature-facing Python exports and HTTP response contracts.
- Focused backend, frontend, integration, and real local end-to-end evidence.

### Deferred

- Agent Designer internals, planner/executor selection, and generated agent
  configuration.
- Sandbox pretend-action execution and evalset execution against an agent.
- Public Web channel deployment.
- Database, Slack, WhatsApp, phone, and other future source/channel connectors.
- Background workers, distributed processing, remote artifact storage, and
  production deployment.
- Claims that generated/reviewed evalset candidates are human gold.
- Promotion of experimental semantic GRAG to an unqualified production claim.

## Boundaries

### ToolRouter engine snapshot

`backend/src/corpus/integrations/toolrouter/engine/` is a mechanically copied,
namespaced snapshot. It owns ToolRouter algorithms only. A checked-in source
manifest records the source checkout, Git commit, dirty-snapshot warning, file
hashes, dependency versions, and local reference evidence.

No feature imports `engine` directly.

### Corpus ToolRouter adapter

`backend/src/corpus/integrations/toolrouter/` owns product-safe contracts,
artifact serialization, model readiness, error translation, and the single
public `ToolRouterAdapter` facade. It may import the engine.

### Sources feature

`backend/src/corpus/features/sources/` owns source identity, owner scoping,
revision state, artifact locations, connector-neutral HTTP behavior, and the
RouteDeck Sources node. Its `connectors/api/` package owns API upload settings,
HTTP, validation, an engine protocol, and the one bridge that invokes the
public ToolRouter adapter.

Future source connectors implement the same connector boundary and keep their
own parsing, retrieval, and evalset adapters inside their connector folder.

### Frontend

`frontend/src/features/sources/` owns the owner-only debug experience and its
HTTP client. `frontend/src/routedeck/surfaces.tsx` only registers the surface.
The UI never imports ToolRouter concepts from the copied engine.

## Public Integration Contract

The `corpus.integrations.toolrouter` package exports:

```python
ToolRouterAdapter
ToolRouterSettings
IngestRequest
IngestResult
RetrievalRequest
RetrievalResult
EvalsetRequest
EvalsetResult
ToolRouterIntegrationError
ToolRouterInputError
ToolRouterDependencyError
ToolRouterArtifactError
```

The `corpus.features.sources` package exports:

```python
SourceService
LocalSourceRepository
SourceSettings
SourceRetrievalResult
SourceEvalsetResult
SourceIntegrationError
create_sources_router
SOURCES_FEATURE
create_sources_bindings
```

Features consume `SourceService` for product behavior. Only the explicit
API/ToolRouter bridge consumes `ToolRouterAdapter`; host composition constructs
it. Generic Sources contracts use ranked `item_id` / 
`item_kind` values and `missing_inputs`; they do not expose API endpoints,
ToolRouter errors, or engine artifact paths.

## Persistence Contract

The data root is required configuration. Local setup explicitly writes
`.runtime/sources`; production may provide another path. Each owner and source
revision is isolated beneath opaque identifiers:

```text
.runtime/sources/<owner-hash>/<source-id>/
  source.json
  r/<revision-id>/
    revision.json
    i/<original-filename>
    a/
      normalized/                  # normalized OpenAPI bundle and indexes
      graph/                       # semantic graph, embeddings, graph trace
      integration_manifest.json
      c/                           # immutable evalset model-call cache
      e/<evalset-hash>/            # run, audits, reviews, ledger, export
```

Metadata replacement is atomic. The owner directory is a 64-bit prefix of the
owner-key SHA-256. Source and revision names are independently generated
96-bit URL-safe opaque identifiers. An evalset label is validated but its
directory uses a 20-hex SHA-256 token, so no user input becomes a path segment.
These deliberately compact names leave room for the evalset factory's long
immutable cache keys on Windows. A source owned by one owner is
indistinguishable from missing to another owner.

## State And Failure Semantics

Ingestion states are `processing`, `ready`, and `failed`. Evalset runs are
separate revision-scoped artifacts and do not make a successfully indexed
source unavailable when generation or review fails.

- Missing auth returns `401`.
- Cross-owner access returns `404`.
- Origin-rejected mutations return `403`.
- Invalid uploads return `400` or `413` with an explicit problem code.
- Parser, conformance, embedding, Ollama, artifact, and model-digest failures
  remain failures and are persisted as failed state/evidence.
- No alternate parser, embedding provider, LLM, cached output, mock, fixture,
  or canned response is selected after failure.
- A completed evalset run with zero accepted candidates is `quarantined`, not
  a successful exported evalset.

## Debug Surface Acceptance

The Sources surface must let an authenticated owner:

1. upload a real API collection and see the resulting revision state;
2. inspect endpoint, schema, graph-node, graph-edge, and graph-card counts;
3. submit a query and see the decision, reason, missing parameters, ranked
   endpoint scores, and bounded/full trace evidence;
4. run at least one source-grounded evalset candidate through the real Gemma
   generator and Qwen reviewer;
5. inspect accepted/quarantined counts, exact token usage, model tags/digests,
   and generated candidate evidence;
6. reload and still retrieve from the persisted revision.

The surface is a debug product surface, not a public channel and not evidence
that Agent Designer is complete.

## Reference And Dependency Decision

The selected stack is the stack already proven by the authoritative ToolRouter
checkout: Prance/OpenAPI validators for parsing and Sentence Transformers with
MiniLM for local embeddings. The embedding alternatives considered were
FastEmbed (lighter ONNX runtime) and direct Hugging Face Transformers/PyTorch
(lower-level control but more custom code). Sentence Transformers is retained
because it is the exact upstream reference path, uses Apache-2.0 code/model
licensing, has an active 5.6.0 release, and avoids changing retrieval behavior
while this adapter boundary is being established.

The ToolRouter repository itself has no root license file. This copy is an
internal same-owner source transfer; external redistribution remains blocked
until repository licensing is made explicit.

## Completion Evidence

- Earlier notebook commit: `2e2a3d9 docs: add Corpus feature behavior
  notebook`; it contains only the five notebook documentation/script/test
  paths and excludes the active auth/UI work.
- ToolRouter source: main at `2611801e`, captured from a dirty working tree.
  `source_manifest.json` records matching source/copied SHA-256 values for all
  24 Python modules plus the v1 recipe pack.
- Upstream focused suite: `79 passed in 3.32s`. Real Ory Kratos v26.2.0
  reference: 56 endpoints, 477 nodes, 876 edges, 477 cards, with
  `ASK_DISAMBIGUATE` for `create a new identity`.
- Corpus gates: 56 backend tests passed; 19 frontend tests passed; frontend
  strict typecheck and production build passed; 12 repository unittest tests
  passed; `pip check` reported no broken requirements.
- Real product upload at `http://127.0.0.1:5199/sources`: 56 endpoints, 316
  schemas, two security schemes, zero repairs, 477 nodes, 876 edges, and 477
  cards. The collection remained present after page reload and GRAG retrieval
  again returned `ASK_DISAMBIGUATE` with `low_score_margin` and
  `api:createRecoveryLinkForIdentity` ranked first at `0.4280`.
- Real evalset run `api-debug-v1`: one of one candidate completed and accepted,
  zero quarantined, 2,936 offline tokens. Gemma generated the candidate and
  Qwen independently reviewed it; both exact installed Ollama digests are
  retained in the run evidence. The accepted task selected
  `api:listIdentitySessions` and remains a reviewed candidate, not human gold.
- Rendered desktop and 390x844 checks passed with no browser warning/error
  logs. The local backend returned `200 {"status":"ready"}` at
  `http://127.0.0.1:8099/readyz`.
- The configuration/HTTP boundary refactor was re-proven through the production
  routers with Ory YAML: source `ex1IDkDESNq_5EWy` produced the same 56/477/876/
  477 counts and retrieval decision; evalset
  `boundary-proof-65553b771add` completed 1/1 accepted with zero quarantined and
  2,936 offline tokens using exact Gemma/Qwen digests.
