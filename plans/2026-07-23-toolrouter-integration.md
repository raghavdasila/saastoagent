# ToolRouter Integration Implementation Plan

Status: completed and locally validated on 2026-07-23

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking. Corpus forbids worktrees and this run
> is explicitly authorized to execute inline on the current checkout.

**Goal:** Deliver an owner-only Sources debug path that uploads a real OpenAPI
collection, builds and persists ToolRouter's resource-first graph/index,
retrieves ranked operations with trace evidence, and generates/reviews an
evalset through local Ollama models.

**Architecture:** Copy the minimal authoritative ToolRouter dependency closure
into a private namespaced engine, then expose it only through a narrow Corpus
adapter. A generic Sources feature owns source/revision persistence while its
API connector delegates parser, graph, retrieval, and evalset work to the
adapter. One authenticated RouteDeck `sources.home` surface exercises the full
path without deciding Agent Designer internals.

**Tech Stack:** Python 3.11, FastAPI, RouteDeck 0.1.0, Pydantic 2, local atomic
JSON/NumPy artifacts, Prance/OpenAPI validation, Sentence Transformers 5.6.0,
MiniLM, Ollama Gemma/Qwen, React 19, Vite 8, TypeScript 7, shadcn/Radix Nova.

## Global Constraints

- Do not touch or commit unrelated active auth/UI work.
- Do not create a worktree.
- API is a connector under Sources; only Sources is a product node.
- Agent Designer remains deferred.
- No runtime dependency on the ignored Corpus benchmark or sibling ToolRouter
  checkout.
- Fail loudly; never substitute parsers, providers, models, fixtures, caches,
  or heuristic responses after a failure.
- Keep semantic GRAG labeled experimental and generated evalsets labeled
  reviewed candidates rather than gold.
- Run all services and compute locally.

---

### Task 1: Freeze the approved requirements and earlier notebook work

**Files:**

- Create: `docs/toolrouter-integration-requirements.md`
- Create: `plans/2026-07-23-toolrouter-integration.md`
- Existing committed slice: `docs/corpus-feature-behavior-notebook.html`
- Existing committed slice: `scripts/feature_behavior_notebook.py`
- Existing committed slice: `tests/test_feature_behavior_notebook.py`

**Interfaces:**

- Consumes: owner instructions and the authoritative repository boundaries.
- Produces: a durable requirement owner and this executable plan.

- [x] **Step 1: Verify the notebook contract**

  Run: `python -m unittest tests/test_feature_behavior_notebook.py -v`

  Expected: seven tests pass.

- [x] **Step 2: Commit only the notebook paths**

  Commit: `2e2a3d9 docs: add Corpus feature behavior notebook`

- [x] **Step 3: Record requirements and plan**

  The requirements define scope, boundaries, public exports, persistence,
  failures, debug behavior, dependency choice, and completion evidence.

### Task 2: Vendor the authoritative ToolRouter engine with provenance

**Files:**

- Create: `backend/src/corpus/integrations/toolrouter/engine/*.py`
- Create: `backend/src/corpus/integrations/toolrouter/engine/__init__.py`
- Create: `backend/src/corpus/integrations/toolrouter/SOURCE.md`
- Create: `backend/src/corpus/integrations/toolrouter/source_manifest.json`
- Modify: `backend/pyproject.toml`
- Test: `backend/tests/integrations/toolrouter/test_engine_snapshot.py`

**Interfaces:**

- Consumes: ToolRouter checkout commit `2611801e` plus the exact current
  working-tree bytes for the 24-module dependency closure.
- Produces: private `corpus.integrations.toolrouter.engine` modules and a hash
  manifest; no feature-facing imports.

- [x] **Step 1: Write the failing provenance test**

  Assert that every manifest path exists, its SHA-256 matches, the source root
  and commit are recorded, and the copied package cannot import the sibling
  `toolrouter` package.

- [x] **Step 2: Run the focused test and observe the missing snapshot failure**

  Run:
  `.\.venv\Scripts\python.exe -m pytest backend/tests/integrations/toolrouter/test_engine_snapshot.py -q`

- [x] **Step 3: Copy the dependency closure and rewrite only package-relative imports**

  Include parser, graph, conformance, retrieval, outcomes, GRAG, evalset
  factory, and their local helper closure. Record hashes from the source bytes
  and copied bytes separately so a future replacement can be audited.

- [x] **Step 4: Pin the proven dependency versions**

  Add exact runtime versions for NumPy, Prance, OpenAPI validation/core,
  PyYAML, JSON Schema, Sentence Transformers, PyTorch, and multipart upload.

- [x] **Step 5: Install and run the provenance/import tests**

  Run:
  `.\.venv\Scripts\python.exe -m pip install -e "backend[testing]"`

  Run:
  `.\.venv\Scripts\python.exe -m pytest backend/tests/integrations/toolrouter/test_engine_snapshot.py -q`

### Task 3: Establish the public ToolRouter adapter contract

**Files:**

- Create: `backend/src/corpus/integrations/toolrouter/contracts.py`
- Create: `backend/src/corpus/integrations/toolrouter/serialization.py`
- Create: `backend/src/corpus/integrations/toolrouter/adapter.py`
- Create: `backend/src/corpus/integrations/toolrouter/errors.py`
- Create: `backend/src/corpus/integrations/toolrouter/settings.py`
- Create: `backend/src/corpus/integrations/toolrouter/__init__.py`
- Test: `backend/tests/integrations/toolrouter/test_adapter_ingestion.py`
- Test: `backend/tests/integrations/toolrouter/test_adapter_retrieval.py`
- Test: `backend/tests/integrations/toolrouter/test_adapter_evalsets.py`

**Interfaces:**

- Consumes: private engine modules and an explicit artifact directory.
- Produces:
  `ToolRouterAdapter.ingest(IngestRequest) -> IngestResult`,
  `retrieve(RetrievalRequest) -> RetrievalResult`, and
  `generate_evalset(EvalsetRequest) -> EvalsetResult`.

- [x] **Step 1: Write failing ingestion and serialization tests**

  Tests use an isolated OpenAPI fixture and assert normalized counts, graph
  counts, conformance evidence, graph JSON, NumPy embeddings, trace output, and
  reload equality.

- [x] **Step 2: Implement immutable contracts and fail-loud errors**

  Define frozen dataclasses for requests/results and distinct input,
  dependency, and artifact errors. Public result objects contain product-safe
  values only.

- [x] **Step 3: Implement ingestion and artifact reload**

  Call `load_openapi_specs`, validate repaired/raw status, call
  `write_normalized_bundle`, `build_semantic_graph`, and
  `SemanticGraphIndex.build`, then atomically persist graph, embeddings, and
  trace evidence.

- [x] **Step 4: Write the failing retrieval test**

  Reload artifacts in a fresh adapter and assert an explicit decision, reason,
  ranked endpoint IDs/scores, and diagnostic trace.

- [x] **Step 5: Implement retrieval through `SemanticGRAGRouter`**

  Reconstruct the saved index without re-embedding all graph cards. Embed only
  the incoming query and map engine dataclasses to the public result.

- [x] **Step 6: Write the failing evalset orchestration test**

  Exercise a one-category experiment through transport-injected test clients,
  checking generator/reviewer evidence, resume identity, quarantine, accepted
  export, model digests, and token ledger without putting fake clients in the
  product path.

- [x] **Step 7: Implement real evalset generation/review**

  Build source-grounded truth tasks, resolve exact Ollama model digests, run
  `EvalsetFactoryExperiment`, and call `build_export`/`write_export` only when
  accepted candidates exist. Return quarantined evidence otherwise.

### Task 4: Build generic Sources persistence and the API connector

**Files:**

- Create: `backend/src/corpus/features/sources/models.py`
- Create: `backend/src/corpus/features/sources/contracts.py`
- Create: `backend/src/corpus/features/sources/errors.py`
- Create: `backend/src/corpus/features/sources/repository.py`
- Create: `backend/src/corpus/features/sources/service.py`
- Create: `backend/src/corpus/features/sources/connectors/base.py`
- Create: `backend/src/corpus/features/sources/connectors/api/intake.py`
- Create: `backend/src/corpus/features/sources/connectors/api/connector.py`
- Create: package `__init__.py` files with narrow exports.
- Test: `backend/tests/sources/test_repository.py`
- Test: `backend/tests/sources/test_api_connector.py`
- Test: `backend/tests/sources/test_service.py`
- Test: `backend/tests/sources/test_feature.py`

**Interfaces:**

- Consumes: `ToolRouterAdapter` only through the API connector.
- Produces: owner-scoped source/revision records and `SourceService` methods
  for create/list/get/retrieve/generate-evalset.

- [x] **Step 1: Write failing owner-isolation and atomic-write tests**

  Assert path-safe opaque-ID layout, immutable revision IDs, atomic metadata, and
  cross-owner not-found behavior.

- [x] **Step 2: Implement repository and source models**

  Keep generic source identity independent of API metadata. Persist connector
  key, current revision, timestamps, state, summaries, and explicit failure.

- [x] **Step 3: Write failing upload-boundary tests**

  Cover empty, oversized, unsupported extension, unsafe filename, malformed
  spec, and valid JSON/YAML bytes.

- [x] **Step 4: Implement `SourceConnector` and API connector**

  The generic service dispatches by registered connector key. The API
  connector alone knows ToolRouter requests and artifact paths.

- [x] **Step 5: Implement SourceService state transitions**

  Persist `processing` before work, `ready` with artifact summary after full
  ingestion, and `failed` with a safe explicit message when work raises.

### Task 5: Add authenticated HTTP and RouteDeck Sources contracts

**Files:**

- Create: `backend/src/corpus/features/sources/http.py`
- Create: `backend/src/corpus/features/sources/config.py`
- Create: `backend/src/corpus/features/sources/declarations.py`
- Create: `backend/src/corpus/features/sources/feature.py`
- Create: `backend/src/corpus/features/sources/bindings.py`
- Modify: `backend/src/corpus/features/workspace/declarations.py`
- Modify: `backend/src/corpus/features/workspace/feature.py`
- Modify: `backend/src/corpus/composition.py`
- Modify: `backend/src/corpus/bindings.py`
- Modify: `backend/src/corpus/runtime/config.py`
- Modify: `backend/src/corpus/main.py`
- Test: `backend/tests/sources/test_http.py`
- Test: `backend/tests/sources/test_config.py`
- Modify: `backend/tests/workspace/test_workspace_feature.py`
- Modify: `backend/tests/integration/test_http_app.py`

**Interfaces:**

- Consumes: current owner browser session and same-origin mutation policy.
- Produces: `sources.home`, `workspace.open_sources`,
  `sources.return_to_home`, and `/api/sources/**`.

- [x] **Step 1: Write failing RouteDeck contract tests**

  Assert one Sources node, session-bound route `/sources`, transitions from
  owner Home and back, owner context, and `sources.debug` active surface.

- [x] **Step 2: Implement Sources feature and bind navigation operations**

  Compose `SOURCES_FEATURE` beside Workspace and retain Workspace Lounge as the
  entry node.

- [x] **Step 3: Write failing HTTP auth/upload/retrieval tests**

  Assert `401` without owner auth, `403` for rejected origins, `404` across
  owners, and real connector calls for an authenticated owner.

- [x] **Step 4: Implement the source router and app composition**

  Resolve the current owner through `AuthService`, register the exception
  handler/router, and close the source service with app lifespan. Run sync
  parser/embedding/model work off the event loop.

### Task 6: Implement the Sources debug surface

**Files:**

- Create: `frontend/src/features/sources/sourceClient.ts`
- Create: `frontend/src/features/sources/SourceDebugSurface.tsx`
- Create: `frontend/src/features/sources/sources.css`
- Modify: `frontend/src/routedeck/surfaces.tsx`
- Modify: `frontend/src/features/workspace/HomeSurface.tsx`
- Modify: `frontend/src/features/workspace/WorkspaceNavigation.tsx`
- Modify: `frontend/src/main.tsx`
- Test: `frontend/src/tests/source-debug-surface.test.tsx`
- Modify: `frontend/src/tests/workspace-surfaces.test.tsx`

**Interfaces:**

- Consumes: `/api/sources/**` and RouteDeck surface affordances.
- Produces: upload, persisted source list, graph summary, retrieval inspector,
  evalset run inspector, explicit busy/error/quarantine states, and navigation.

- [x] **Step 1: Write failing surface tests**

  Assert the registered surface, multipart upload, graph counts, retrieval
  request/result rendering, evalset request/result rendering, and visible
  failures.

- [x] **Step 2: Implement a typed same-origin source client**

  Use credentials, parse structured API failures, and send multipart uploads
  without manually setting the content-type boundary.

- [x] **Step 3: Implement the debug surface using installed shadcn primitives**

  Use `FieldGroup`/`Field`, Input, Textarea, Button, Separator, semantic tables,
  proper labels, disabled busy controls, and no invented placeholder data.

- [x] **Step 4: Wire RouteDeck navigation and styles**

  Home opens Sources through its declared affordance. The source surface
  returns through RouteDeck and remains owner-only/session-bound.

### Task 7: Prove the full local product path and close documentation

**Files:**

- Modify: `architecture/code-map.md`
- Create: `architecture/components/toolrouter-source-integration.md`
- Create: `decisions/ADR-003-vendored-toolrouter-adapter.md`
- Modify: `SYSTEM_FLOW_INDEX.md`
- Modify: `docs/README.md`
- Modify: `backend/README.md`
- Modify: `frontend/README.md`
- Modify: `test_index/README.md`
- Modify: `context.md`
- Create: `logs/20260723_toolrouter_integration.md`
- Create: `context_checkpoints/2026-07-23-toolrouter-integration.md`

**Interfaces:**

- Consumes: completed implementation and fresh runtime evidence.
- Produces: exact ownership, setup, commands, claim boundaries, and restart
  state.

- [x] **Step 1: Run focused and full automated gates**

  ```powershell
  .\.venv\Scripts\python.exe -m pytest backend\tests -q
  .\.venv\Scripts\python.exe -m pip check
  pnpm --dir frontend test
  pnpm --dir frontend typecheck
  pnpm --dir frontend build
  python -m unittest discover -v
  python scripts\check_doc_coverage.py
  ```

- [x] **Step 2: Start the real local services**

  ```powershell
  .\scripts\run-backend.ps1
  .\scripts\run-frontend.ps1
  ```

  Smoke URLs: `http://127.0.0.1:8099/readyz` and
  `http://127.0.0.1:5199/sources` through RouteDeck navigation.

- [x] **Step 3: Exercise the actual ToolRouter path**

  Register/sign in a real local owner, upload a real Medusa or Ory API
  collection, record source/graph counts, query retrieval, run one uncached
  paraphrase candidate through `gemma4:latest` and `qwen2.5-coder:7b`, reload,
  and query again.

- [x] **Step 4: Perform in-app browser QA**

  Verify page identity, nonblank UI, no framework overlay, console health,
  upload interaction, retrieval interaction, evalset state, desktop layout,
  390x844 layout, and screenshots.

- [x] **Step 5: Reconcile docs and requirements**

  Completion evidence is owned by
  `docs/toolrouter-integration-requirements.md` and
  `logs/20260723_toolrouter_integration.md`.

  Map every changed file to a code-map owner, record exact upstream and local
  evidence, update the plan checkboxes, and list any unmet acceptance item as a
  blocker rather than claiming completion.
