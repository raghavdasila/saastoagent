# Corpus R1 Design and Full-Flow Proof Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to execute this plan. In this session execution is inline with `superpowers:executing-plans`; the active multi-agent policy does not authorize delegation.

**Goal:** Design the complete 11-feature Corpus launch baseline in the Agent Design Studio, then implement and prove the locked minimal path in an isolated `mockruns/corpus-r1` copy using current RouteDeck, current ToolRouter, a real local sandbox API, and real local Ollama.

**Architecture:** The repository workbench remains the durable, reviewable product-design artifact. All new behavior stories are seeded as drafts; only the seven implementation-backed authentication stories remain approved. RouteDeck candidates live in a separate studio view after behavior, so user/agent intent and product behavior do not become runtime contracts. The isolated run copies current Corpus, keeps owner-facing Corpus and generated-agent runtimes separate, persists product/version/evidence records locally, dynamically compiles a version-pinned RouteDeck agent from the selected API operations, and records Sandbox and public interactions for Evaluation and Operations.

**Technology:** React 19, TypeScript 7, Vite 8, Vitest/Testing Library, FastAPI, Python 3.11, SQLAlchemy/SQLite, current sibling RouteDeck 0.1.0 packages, current in-repo ToolRouter snapshot, Ollama, Docker Compose, Playwright or browser automation for visual and end-to-end proof.

## Authority and operating boundaries

- `docs/corpus-agent-design/feature-behavior-notes.md` is the launch-behavior authority.
- The launch set is exactly Workspace, Agents, Source Hub, API Source, Agent Designer, Agent Builder, Sandbox, Evaluation, Channels (hosted Web), Deployment, and Operations.
- `benchmark/saastoagent-v0.1` is read-only behavior evidence. Runtime imports and copied architecture from it are forbidden.
- `D:\Dev\AI Projects\AutomationBench` is out of scope and must not be accessed.
- `D:\Dev\AI Projects\routedeck` is read-only. Its current packages and Medusa example are reference/dependency inputs only.
- Product implementation writes are confined to `mockruns/corpus-r1`. Studio/design-document writes remain under `docs/corpus-agent-design`.
- No new story becomes approved without owner review. Provisional implementation in `corpus-r1` may use draft designs because that lane is explicitly authorized.
- No fixture, schema simulation, canned response, heuristic success, cached substitute, or provider fallback may satisfy a runtime proof. Test/demo fixtures remain isolated and labeled.
- No git operations are part of this plan unless the owner separately asks.

## Definition of done

The work is complete only when all of the following are true:

1. The studio contains all 11 launch features, their boundaries, atomic draft stories, user intent, agent intent, concise mock Corpus conversations, separate actions, useful inline surfaces, variations, handoffs, and a separately labeled provisional RouteDeck candidate model.
2. Existing locally saved v6 workbench data migrates without losing edits or the seven approved authentication stories.
3. The studio can export and import its complete design state as JSON and passes build, unit, and representative visual/interactivity checks.
4. `mockruns/corpus-r1` is self-contained except for explicit current RouteDeck package dependencies and local Ollama, with its own ports, storage, environment, and evidence folder.
5. A real run proves: create agent -> upload API YAML -> attach ready source -> generate a RouteDeck design -> build an immutable runnable version -> execute a real sandbox API interaction -> evaluate the exact version -> validate hosted Web -> deploy that same eligible version -> interact at a public local URL -> inspect the recorded interaction and trace in Operations -> add it to an evalset.
6. The generated agent is actually executed through a compiled RouteDeck application and RouteDeck operation runner; a label or serialized pseudo-graph alone is insufficient.
7. Sandbox and public turns use a real configured local Ollama model. Missing Ollama, models, source artifacts, target API, exact version, evaluation eligibility, or channel readiness fails visibly.
8. Evidence includes exact commands, URLs, immutable IDs, selected source revision and operation, RouteDeck application identity, model identity, real HTTP request/result, evaluation result, deployment/public URL, Operations interaction/trace, screenshots, and machine-readable proof output.

## Task 1: Extend the design-studio contract before adding content

**Files:**

- Modify: `docs/corpus-agent-design/workbench/src/workbench/types.ts`
- Modify: `docs/corpus-agent-design/workbench/src/workbench/storage.ts`
- Modify: `docs/corpus-agent-design/workbench/src/tests/workbench.test.tsx`

**Contract:**

- Upgrade persisted state to version 7.
- Add feature-level `purpose`, `owns`, `doesNotOwn`, `inputs`, `outputs`, and `handoffs`.
- Add story-level `variations` and `openQuestions` while retaining the existing atomic story, intents, conversation, actions, surface path, and review status.
- Add a `routeDeckCandidate` containing explicitly provisional nodes and exact `operation / outcome -> target` transitions. Candidate nodes record kind, route, deep-link policy, and surface components.
- Add exported parsing/validation helpers so JSON import uses the same fail-closed contract as local persistence.
- Migrate v1-v6 data, merge newly seeded features/stories without replacing existing edits, and populate only missing v7 fields from the seed.

**Tests first:**

- Assert all v7 fields validate.
- Assert malformed import fails without replacing local state.
- Assert v6 intent/action edits and review states survive v7 migration.
- Assert all newly seeded features/stories are merged into prior saves.

**Verify:**

```powershell
pnpm test -- --run
pnpm typecheck
```

Run from `docs/corpus-agent-design/workbench`.

## Task 2: Make the studio usable for complete feature design

**Files:**

- Modify: `docs/corpus-agent-design/workbench/src/App.tsx`
- Modify: `docs/corpus-agent-design/workbench/src/workbench/FeatureRail.tsx`
- Modify: `docs/corpus-agent-design/workbench/src/workbench/StoryEditor.tsx`
- Add: `docs/corpus-agent-design/workbench/src/workbench/FeatureEditor.tsx`
- Add: `docs/corpus-agent-design/workbench/src/workbench/RouteDeckCandidateEditor.tsx`
- Add: `docs/corpus-agent-design/workbench/src/workbench/ListEditor.tsx`
- Add: `docs/corpus-agent-design/workbench/src/workbench/WorkbenchTransfer.tsx`
- Modify: `docs/corpus-agent-design/workbench/src/tests/workbench.test.tsx`

**Behavior:**

- Add compact `Behavior`, `Feature model`, and `RouteDeck candidate` views.
- Keep story approval controls only in Behavior view.
- Label RouteDeck content `Provisional — derived after behavior` and never imply story approval.
- Allow feature/list/candidate text edits while preserving the flat compact visual system.
- Export the exact current state to JSON; import only a valid v7 state after explicit confirmation.
- Retain deletion only for draft stories and require explicit confirmation.
- Replace the Slice 1 header with an 11-feature launch-baseline label and show draft/approved counts.

**Tests first:**

- Switch among all three studio views without losing selection.
- Edit a feature boundary and RouteDeck candidate.
- Export contains the current design state.
- Import rejects invalid data and accepts a valid state.
- Story approval remains independent of feature/candidate edits.

**Verify:** same workbench test/typecheck commands, then `pnpm build`.

## Task 3: Seed the full 11-feature behavior design

**Files:**

- Add: `docs/corpus-agent-design/workbench/src/workbench/launchDesign.ts`
- Modify: `docs/corpus-agent-design/workbench/src/workbench/seed.ts`
- Modify: `docs/corpus-agent-design/workbench/src/tests/workbench.test.tsx`
- Modify: `docs/corpus-agent-design/agent-design-progress-log.md`

**Content rules:**

- Keep the seven authentication stories byte-for-byte approved unless a runtime contradiction is found.
- Keep `Enter the workspace` and every other new story in Draft.
- Treat `Create an agent` as an action, not a surface. The draft-agent behavior may remain conversational; the resulting overview can use a surface.
- Use concise mock product conversations between `Owner` and `Corpus`; do not copy the live owner-Codex design conversation.
- Attach a surface only for structured information/input that is materially clearer than chat.
- Capture empty, ready, processing, failure, stale-version, ineligible, and unavailable states as variations where they belong, not as gratuitous durable nodes.
- Keep Agent Builder within the Designer experience even though it remains a feature owner in the model.

**Minimum atomic story inventory:**

- Workspace: enter and orient in the one private Workspace, plus the seven approved auth baselines.
- Agents: create a draft; open/switch an agent; attach or change a source; understand exact version/deployment status.
- Source Hub: view inventory/readiness; choose an existing source; begin adding the only launch source family.
- API Source: upload YAML; observe processing/failure; inspect ready operations and provenance.
- Agent Designer: establish the brief; propose selected operations and behavior; review/request changes; accept an exact design.
- Agent Builder: build the accepted design; inspect validation/failure; accept the immutable runnable version.
- Sandbox: start an isolated session; run a real interaction; inspect result/API activity/decision trace; finish and retain evidence.
- Evaluation: generate an evalset; edit cases; run against an exact version; inspect eligible/ineligible evidence; accept a captured Operations interaction as a case.
- Channels: configure and validate hosted Web for an exact version.
- Deployment: review eligibility/target; deploy the exact version; view active version and public URL; surface activation failure.
- Operations: find the public interaction; inspect result/API activity/decision trace; add the interaction to an evalset.

**Verify:** add assertions for 11 exact feature IDs, non-empty intent fields, valid action/surface separation, candidate edge targets, and only the seven auth stories approved.

## Task 4: Add useful inline mock surfaces

**Files:**

- Add: `docs/corpus-agent-design/workbench/public/mock-surfaces/launch-surface.css`
- Add one compact HTML surface file under each relevant feature folder in `public/mock-surfaces/`.
- Reuse: `docs/corpus-agent-design/workbench/public/mock-surfaces/surface-height.js`
- Modify: `docs/corpus-agent-design/workbench/src/tests/workbench.test.tsx`

**Surface set:**

- Agents overview/version state.
- Source inventory and readiness.
- API upload/progress/ready-operation evidence.
- Designer proposal/review and Builder result as two states in one Designer experience.
- Sandbox live run/trace.
- Evaluation evalset/run/gate.
- Hosted Web channel readiness.
- Deployment review/active URL.
- Operations sessions/trace/capture.

Each surface renders inline above the composer, grows to content, and caps at half the chat surface. It contains no duplicate Corpus shell, modal/dialog framing, or action masquerading as a surface.

**Verify:** inspect at desktop and narrow viewport; capture screenshots under `logs/evidence/corpus-design-studio/` only if that existing evidence folder is intentionally used, otherwise under a task-specific temporary folder and report it.

## Task 5: Derive the provisional 11-feature RouteDeck candidate

**Files:**

- Populate `routeDeckCandidate` in `launchDesign.ts`.
- Modify: `docs/corpus-agent-design/routedeck-design-glossary.md` only if runtime work exposes a vocabulary gap.
- Modify: `docs/corpus-agent-design/agent-design-progress-log.md`.

**Rules:**

- Derive nodes only after the feature/story inventory exists.
- Prefer surfaces/status variations over durable nodes when location, legal operation scope, history, or deep-link behavior does not change.
- Use exact feature-owned namespaces and exact edge targets.
- Separate the Corpus owner Navgraph from each generated agent's Navgraph.
- Do not import the older 53-node notebook proposal wholesale; use it as a question set and simplify for the launch baseline.

**Verify:** programmatically assert unique node IDs, known edge targets, one Corpus entry node, and a reachable path covering all 11 launch features.

## Task 6: Create the isolated Corpus R1 copy

**Target:** `mockruns/corpus-r1`

**Copy:** current `backend`, `frontend`, root Docker/config scripts needed to run, and selected documentation needed for a local run.

**Exclude:** `.git`, `.runtime`, `.venv`, `node_modules`, build/dist/cache folders, `logs/evidence`, `benchmark`, and nested `mockruns`.

**Files after copy:**

- Add: `mockruns/corpus-r1/README.md`
- Add: `mockruns/corpus-r1/.env.example`
- Modify: `mockruns/corpus-r1/compose.yaml`
- Modify: `mockruns/corpus-r1/Dockerfile`
- Add: `mockruns/corpus-r1/evidence/README.md`

**Isolation:**

- Compose name: `corpus-r1`.
- Frontend: `127.0.0.1:5299`.
- Corpus backend: `127.0.0.1:8199`.
- Real sandbox API: `127.0.0.1:8301`.
- All SQLite/filesystem state under `mockruns/corpus-r1/.runtime`.
- RouteDeck packages come from the current sibling checkout at build/install time; sibling files are never edited.
- Explicit Ollama URL/model configuration; no fallback provider/model.

**Verify:** resolved paths stay under the target before any replace/delete; list the copied tree and assert excluded directories are absent.

## Task 7: Establish persistent launch-domain contracts

**Files inside `mockruns/corpus-r1`:**

- Add: `backend/src/corpus/domain/models.py`
- Add: `backend/src/corpus/domain/repository.py`
- Add: `backend/src/corpus/domain/service.py`
- Add: `backend/src/corpus/domain/errors.py`
- Add: `backend/src/corpus/domain/http.py`
- Add: `backend/tests/domain/test_repository.py`
- Add: `backend/tests/domain/test_launch_lifecycle.py`

**Persist:** owner-scoped agents, source attachments, accepted designs, immutable runnable versions, evalsets/cases, evaluation runs, hosted-Web bindings, deployments, public/sandbox interactions, and trace references.

**Invariants:**

- IDs exposed to browser/model are opaque.
- Every downstream artifact pins exact agent/source/design/version IDs.
- Runnable versions are immutable.
- Deployment requires a passing evaluation for that exact version and a ready Web binding.
- Public resolution returns only an active deployment.
- Operations cannot read another owner’s evidence.

**Verify:** focused unit tests plus a repository-level lifecycle test using a temporary real SQLite database.

## Task 8: Implement owner feature path and RouteDeck topology

**Files inside `mockruns/corpus-r1`:**

- Add feature packages for `agents`, `designer`, `sandbox`, `evaluation`, `channels`, `deployment`, and `operations` under `backend/src/corpus/features/`.
- Refine the copied `sources` declarations into Source Hub/API launch states without breaking current ToolRouter boundaries.
- Modify `backend/src/corpus/composition.py` and `backend/src/corpus/bindings.py`.
- Add feature contract tests under `backend/tests/features/`.

**Behavior:**

- Compile one owner-facing Corpus application covering the provisional launch path.
- Bind exact operations to product services; use API endpoints for structured payloads when appropriate, then dispatch declared RouteDeck affordances for navigation/state.
- Project only product-safe IDs and state.
- Keep build status inside Designer UI even though Builder owns its declarations/handlers.

**Verify:** compiler/binding tests, reachable full path, frontend-contract generation, and no missing/extra bindings or surface registrations.

## Task 9: Build a real local sandbox target and upload path

**Files inside `mockruns/corpus-r1`:**

- Add: `sandbox_api/app.py`
- Add: `sandbox_api/pyproject.toml`
- Add: `tests/fixtures/support-sandbox-openapi.yaml`
- Add: `tests/e2e/prepare_support_sandbox.py`
- Modify Compose/Docker files to run it.

**Behavior:**

- The service owns a real SQLite-backed ticket collection.
- Test setup creates a ticket through the service's real HTTP API.
- The uploaded OpenAPI YAML points to the Compose-internal service URL and accurately describes the exercised operation.
- Corpus uploads and processes that YAML through the copied ToolRouter adapter, persists a ready source revision, and attaches it to the agent.

**Verify:** direct target API create/read calls, Corpus upload readiness, artifact persistence, and ToolRouter retrieval evidence from a fresh adapter reload.

## Task 10: Implement Designer/Builder and generated RouteDeck agent runtime

**Files inside `mockruns/corpus-r1`:**

- Add: `backend/src/corpus/generated_agents/contracts.py`
- Add: `backend/src/corpus/generated_agents/compiler.py`
- Add: `backend/src/corpus/generated_agents/bindings.py`
- Add: `backend/src/corpus/generated_agents/http_client.py`
- Add: `backend/src/corpus/generated_agents/runtime_registry.py`
- Add: `backend/src/corpus/generated_agents/agent.py`
- Add corresponding unit/integration tests.

**Behavior:**

- Designer consumes the agent goal and exact ready source revision, retrieves relevant operations through ToolRouter, and stores a reviewable proposal.
- Owner acceptance freezes the exact proposal identity.
- Builder compiles a generated RouteDeck `Application` whose declared operations are derived from the selected source operations, validates exact bindings, serializes a reproducible public contract, and creates an immutable runnable version.
- Each version opens a version-specific persistent RouteDeck runtime on demand.
- Its LangGraph/Ollama agent receives only version/node-scoped RouteDeck tools.
- Generated operation handlers perform actual HTTP requests described by the ready OpenAPI source. Unsupported auth, unsafe writes, missing required inputs, transport errors, or invalid responses fail loudly.
- Runtime registry has one explicit path. It never substitutes a scripted model, alternate model/provider, schema response, cached answer, or direct non-RouteDeck executor.

**Verify:** generated contract compile, exact binding parity, version immutability, real target API request through `RouteDeckOperationRunner`, and real Ollama agent turn that selects and completes the declared operation.

## Task 11: Implement Sandbox, Evaluation, Channel, Deployment, and Operations APIs

**Files inside `mockruns/corpus-r1`:**

- Add or complete each feature's service/HTTP/bindings package.
- Add integration tests for each cross-feature invariant.

**Behavior:**

- Sandbox creates a non-public RouteDeck session for the exact runnable version and stores every completed interaction with request/result/operation evidence.
- Evaluation can generate source-grounded candidate cases with existing ToolRouter, permits explicit case edits, runs exact-version agent turns, and stores immutable case results plus a simple eligible/ineligible gate.
- Hosted Web channel validation proves the exact version's public surface and interaction contract are supported.
- Deployment atomically activates only an eligible exact version for the ready hosted-Web binding and creates a unique local public slug/URL.
- Public chat resolves the active deployment, creates/resumes a generated-agent RouteDeck session, streams a real Ollama turn, and records the interaction.
- Operations lists the public interaction and exposes its result, API request/activity, RouteDeck decision/operation evidence, and exact IDs; capture creates an evaluation case without rewriting history.

**Verify:** failure tests for wrong version, ineligible version, unready channel, inactive slug, unavailable target API, and unavailable Ollama.

## Task 12: Implement the owner and public Web surfaces

**Files inside `mockruns/corpus-r1`:**

- Add feature clients/components/styles under `frontend/src/features/{agents,sources,designer,sandbox,evaluation,channels,deployment,operations}`.
- Add public page under `frontend/src/public/`.
- Update `frontend/src/routedeck/surfaces.tsx`, application routing/bootstrap, and tests.

**Interaction:**

- Preserve the Corpus chat-first shell.
- Render active/review surfaces inline immediately above the composer and cap them at half the chat surface.
- Keep command actions separate from surfaces.
- Show exact version/source/evaluation/deployment identity where it prevents ambiguity.
- Make progress/failure states truthful; no optimistic success before backend proof.
- Public URL renders the deployed agent, not the owner Corpus shell.

**Verify:** component tests and real browser exercise at 1440x900 and narrow mobile width, including scroll, surface height, source upload, sandbox trace, gate, public chat, and Operations capture.

## Task 13: Add one reproducible full-flow verifier

**Files inside `mockruns/corpus-r1`:**

- Add: `scripts/verify-r1.ps1`
- Add: `tests/e2e/full_launch_flow.py` or a browser equivalent where UI state is essential.
- Add: `evidence/schema/full-flow-proof.schema.json`

**Verifier sequence:**

1. Prove Ollama readiness and exact model presence.
2. Prove sandbox API readiness and create a real ticket via HTTP.
3. Create/sign in a local owner through real auth.
4. Create the draft agent.
5. Upload the API YAML and wait for a ready ToolRouter revision.
6. Attach that exact source revision.
7. Produce, review, and accept a design; build the runnable RouteDeck version.
8. Run a real Sandbox turn and assert the ticket returned by the target API is present.
9. Create/edit/run an evalset against the same version and assert eligible.
10. Validate hosted Web and deploy the same version.
11. Use the public URL to perform a real Ollama/RouteDeck interaction.
12. Open Operations, locate that interaction, validate its API/decision evidence, and add it to the evalset.
13. Write a timestamped JSON proof bundle and human-readable report with no secrets.

**Verify:** run twice from clean `corpus-r1` state to prove reproducibility, using explicit teardown/recreate confined to the isolated folder.

## Task 14: Run the design/runtime feedback loop and close with evidence

When any real run contradicts a draft story:

1. Record the observed failure and exact evidence.
2. Decide whether it is an implementation defect or design defect.
3. If design-defective, update the story/variation/handoff and provisional RouteDeck candidate in the studio; leave it Draft.
4. Update only the owning `corpus-r1` implementation.
5. Re-run the narrow failing path, then the full verifier.

**Final verification commands:**

```powershell
pnpm test
pnpm typecheck
pnpm build
python -m pytest
docker compose -f compose.yaml up --build -d
powershell -ExecutionPolicy Bypass -File scripts/verify-r1.ps1
```

Use the appropriate workbench, `mockruns/corpus-r1/frontend`, `mockruns/corpus-r1/backend`, and `mockruns/corpus-r1` working directories. Record the exact realized commands if package/Compose entry points differ after copying.

**Closeout artifacts:**

- Update `docs/corpus-agent-design/agent-design-progress-log.md` with designed feature/story counts and unresolved owner-review items.
- Add `mockruns/corpus-r1/evidence/<run-id>/FULL_FLOW_REPORT.md` and machine-readable proof JSON.
- Add a concise `mockruns/corpus-r1/README.md` restart/run guide with exact local URLs and limitations.
- Update only affected repository context owners after verified completion; do not turn `context.md` into a session log.

