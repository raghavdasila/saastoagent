# Corpus v0.2 Sandbox Playground Implementation Plan (Superseded)

> **Superseded on 2026-08-19.** Do not execute this plan. Its owner-Workspace
> `sandbox.start` / `sandbox.send_message` transport was rejected. The accepted
> replacement is `plans/2026-08-19-v02-sandbox-deployment-mode.md`, where
> Sandbox is an explicit owner-private mode of the shared Agent deployment
> runtime.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the existing exact-build Sandbox runtime into a real, isolated, deployed-agent-like playground that preserves multi-run Sandbox conversations, shows exact-build ToolRouter evaluation coverage read-only, and keeps diagnostics, Evaluation ownership, deployed activity, and audit evidence separate.

**Architecture:** Reuse the existing `agent_sandbox_sessions` identity and Corpus session-context store so multiple ordinary Sandbox runs can share one exact build-bound private conversation. Keep `sandbox.start` for starting a new conversation and add one surface-only `sandbox.send_message` operation that delegates to the same Sandbox service with a required Corpus-owned `conversation_id`; this keeps user chat free of opaque conversation IDs while giving the Playground an explicit continuation contract. Group persisted runs into conversation projections and render the selected conversation as the primary transcript. Read evaluation coverage through the existing owner-scoped Evaluation reader; do not duplicate generation, CRUD, execution, retry, or eligibility logic in Sandbox.

**Tech Stack:** Python 3.11, FastAPI, Pydantic, SQLAlchemy, RouteDeck Corpus declarations, React 19, TypeScript, Vitest, Testing Library, Docker Compose, Playwright-based product evidence.

**Spec:** `docs/corpus-agent-design/feature-behavior-notes.md` sections 6–8, governed by `docs/corpus-behavior-first-delivery-process.md`.

## Global Constraints

- Authority checkout: `D:\Dev\AI Projects\saastoagent\saastoagent-v0.1`.
- Runtime: local Docker Compose only; Corpus `http://127.0.0.1:5199`, backend `http://127.0.0.1:8099`, Medusa `http://127.0.0.1:9100`.
- The primary Sandbox surface is a real conversation over the exact running draft build, never a fixture, canned response, mock execution, or deployed session.
- `Evaluation` remains the source of truth for ToolRouter generation, cases, runs, retry, results, and deployment eligibility. Sandbox renders only an exact-build read projection and a continuation to Evaluation.
- Owner-only NavGraph, ToolRouter, operation, and API evidence stays available under separate diagnostics and is not exposed in the primary conversation.
- A conversation is pinned to one owner, Agent, immutable build, runtime build hash, and runtime session. A different build requires a new conversation.
- A waiting clarification or action review must be resolved in the same run before another ordinary message can start in that conversation.
- Failure remains visible failure. There is no automatic retry, alternate credential, alternate provider, cached success, or fallback execution path.
- No new product dependency is required. Stop for dependency research and approval if implementation disproves this.
- RouteDeck, `agent-execution-runtime`, `agent-delivery-runtime`, public Delivery, and the Evaluation backend remain read-only unless a focused failing contract proves a necessary change and the user expands the allowlist.
- Existing canonical audit evidence remains unchanged until a new full audit campaign.
- Git operations are intentionally omitted. Any commit, staging, branch, or push requires separate explicit authorization.

## Proposed Execution Mutation Allowlist

Execution must begin only after the user approves this exact expansion:

- Design authority through the Studio save path: `docs/corpus-agent-design/workbench/design-state.json`.
- Studio mapping: `contracts/corpus-agent-design-routedeck-manifest.json`.
- Sandbox backend: `backend/src/corpus/features/sandbox/**` and focused Sandbox tests.
- Corpus runtime composition only if the existing public interfaces require wiring: `backend/src/corpus/app/**`.
- Generated Corpus frontend contract: `frontend/src/routedeck/corpus-frontend-contract.generated.json`.
- Sandbox frontend: `frontend/src/features/builder/SandboxSurface.tsx`, new Sandbox-owned components under `frontend/src/features/builder/`, `frontend/src/features/builder/builder.css`, and focused frontend tests.
- Validation tooling: `scripts/run_api_connection_check_journey.py`, `scripts/record_v02_behavior_audit.py`, one focused Sandbox journey recorder, and their tests.
- A newly created disposable local owner, Source profile, Agent, build, Sandbox conversation, and Evaluation lineage used only for validation.
- Affected documentation owners: `architecture/code-map.md`, the relevant Sandbox component document if present, `test_index/README.md`, this plan, `context.md`, and a completion checkpoint when the session is closed.

Everything else is read-only. In particular, do not edit `frontend/src/features/delivery/PublicAgentApp.tsx`, either sibling RouteDeck/runtime repository, existing owner data, or the retained audit ledger without a new decision.

---

### Task 1: Accept the revised Sandbox behaviors in Design Studio

**Files:**
- Modify through Studio save only: `docs/corpus-agent-design/workbench/design-state.json`
- Verify: `docs/corpus-agent-design/feature-behavior-notes.md`
- Test: `docs/corpus-agent-design/workbench/src/**/*.test.*`

**Interfaces:**
- Consumes: the approved behavior-note contracts for conversation-first Sandbox, isolated new conversations, separate diagnostics, and read-only exact-build evaluation coverage.
- Produces: accepted Studio behavior IDs `sandbox-start-run`, `sandbox-continue-conversation`, and `sandbox-view-evaluation-coverage`, plus the existing clarification and diagnostic behaviors.

- [ ] **Step 1: Start the authoritative Studio**

  Run:

  ```powershell
  pnpm --dir docs/corpus-agent-design/workbench dev --host 0.0.0.0 --port 8782 --strictPort
  ```

  Expected: `http://127.0.0.1:8782/` loads the Corpus design state from the repository file.

- [ ] **Step 2: Revise `sandbox-start-run` in Studio**

  Preserve the behavior ID and use this accepted behavior text:

  ```text
  User intent: Try this exact draft Agent privately in a conversation that behaves like its hosted experience.

  Expected behavior: Sandbox starts a new owner-only conversation pinned to the selected immutable running build. The conversation uses the actual draft runtime and supervised API path, keeps its state and results separate from deployed activity, and presents user and Agent messages without owner diagnostics or internal identifiers in the transcript.
  ```

  Keep operation `Start Sandbox run`, surface `Agent Sandbox`, and capability `Agent Sandbox`.

- [ ] **Step 3: Add and approve `sandbox-continue-conversation`**

  Use this atomic behavior:

  ```text
  User intent: Send another message in this same private draft-Agent conversation.

  Expected behavior: Sandbox starts one new run in the selected existing Sandbox conversation, preserves the same owner, Agent, immutable build, runtime session, and bounded response-derived context, appends the real result to the transcript, and refuses to retarget a different build or bypass a waiting clarification or action review.
  ```

  Make `Send Sandbox message` surface-only. It delegates to the same Sandbox service/runtime path as `Start Sandbox run`; it is not a second executor or chat-visible opaque-ID contract.

- [ ] **Step 4: Add and approve `sandbox-view-evaluation-coverage`**

  Use this atomic behavior:

  ```text
  User intent: See what ToolRouter-generated tests cover this exact draft build while I try it.

  Expected behavior: Sandbox shows a read-only summary for the selected immutable build: generation state, generated case count, category and difficulty coverage, latest case-result state, and eligible, ineligible, or not-yet-evaluated status. Sandbox offers explicit continuation to Evaluation for generation retry, case management, execution, and eligibility work, and never performs those actions itself.
  ```

  This behavior has no Sandbox mutation operation.

- [ ] **Step 5: Save through Studio and verify file persistence**

  Use Studio’s save action, reload Studio, and verify the three accepted behaviors remain accepted. Do not edit `design-state.json` directly.

- [ ] **Step 6: Run Studio validation**

  Run:

  ```powershell
  pnpm --dir docs/corpus-agent-design/workbench test
  .\.venv\Scripts\python.exe scripts\validate_design_notebook.py
  ```

  Expected: both commands pass; any parity failure caused by the not-yet-updated manifest is retained for Task 2 rather than weakening Studio behavior.

### Task 2: Pass the Studio-to-RouteDeck mapping gate

**Files:**
- Modify: `contracts/corpus-agent-design-routedeck-manifest.json`
- Regenerate later after backend declaration changes: `frontend/src/routedeck/corpus-frontend-contract.generated.json`
- Test: `tests/test_agent_design_parity.py`

**Interfaces:**
- Consumes: the accepted Studio behavior names and existing compiled IDs `sandbox.home`, `sandbox.execution`, `sandbox.start`, `sandbox.resume`, and `agents.open_evaluation`.
- Produces: complete manifest mappings, the planned Corpus-owned `sandbox.send_message` declaration mapping, and evaluation bindings for the two new behavior contracts without a RouteDeck repository change.

- [ ] **Step 1: Add the conversation mapping**

  Add this behavior mapping under `Builder and Sandbox`:

  ```json
  {
    "designBehavior": "Continue a Sandbox conversation",
    "node": "sandbox.home",
    "capabilities": {
      "Agent Sandbox": "sandbox.execution"
    },
    "surfaces": {
      "Agent Sandbox": "sandbox.home"
    },
    "operations": {
      "Send Sandbox message": "sandbox.send_message"
    }
  }
  ```

- [ ] **Step 2: Add the read-only coverage mapping**

  Add this behavior mapping under `Builder and Sandbox`:

  ```json
  {
    "designBehavior": "View exact-build evaluation coverage",
    "node": "sandbox.home",
    "capabilities": {
      "Agent Sandbox": "sandbox.execution"
    },
    "surfaces": {
      "Agent Sandbox": "sandbox.home"
    },
    "operations": {}
  }
  ```

- [ ] **Step 3: Add evaluation bindings**

  Add `sandbox-continue-conversation-contract` and `sandbox-view-evaluation-coverage-contract` with `implementationStatus: "pending_external_evidence"` and the focused Sandbox recorder from Task 7 as `externalEvidenceOwner`.

- [ ] **Step 4: Update the runtime-boundary prose**

  State that one Sandbox session can own multiple sequential runs for one exact build, and that the Sandbox evaluation card reads the Evaluation projection without taking Evaluation operations or persistence ownership.

- [ ] **Step 5: Run the mapping gate**

  Run:

  ```powershell
  .\.venv\Scripts\python.exe scripts\check_agent_design_parity.py --verbose
  ```

  Expected: the accepted Studio inventory and manifest match. If parity requires a new RouteDeck primitive rather than an existing Corpus declaration or projection, stop and request approval before touching RouteDeck.

### Task 3: Correct the Medusa validation identity before product diagnosis

**Files:**
- Modify: `scripts/run_api_connection_check_journey.py`
- Modify: `scripts/record_v02_behavior_audit.py`
- Test: `backend/tests/evaluation/test_api_connection_check_journey_recorder.py`
- Test: `backend/tests/evaluation/test_product_journey_artifacts.py`

**Interfaces:**
- Consumes: an explicit `Path` supplied by `--medusa-env` for the exact running Medusa environment.
- Produces: one validated Medusa environment identity passed into every full recorder run; no imported absolute default and no credential value in evidence.

- [ ] **Step 1: Write the failing CLI contract tests**

  Add tests that assert:

  ```python
  assert parse_args([]).medusa_env is None
  assert require_runtime_medusa_env(None, validate_only=False) raises SystemExit
  assert require_runtime_medusa_env(None, validate_only=True) is None
  assert require_runtime_medusa_env(explicit_path, validate_only=False) == explicit_path.resolve()
  ```

  Also assert tracked recorder output contains neither `MEDUSA_PUBLISHABLE_KEY` nor its value.

- [ ] **Step 2: Run the tests and confirm the hard-coded default fails them**

  Run:

  ```powershell
  docker compose --env-file .env.local exec -T backend python -m pytest backend/tests/evaluation/test_api_connection_check_journey_recorder.py backend/tests/evaluation/test_product_journey_artifacts.py -q
  ```

  Expected: FAIL because the current recorder imports and uses a fixed external-checkout path.

- [ ] **Step 3: Require the explicit environment path**

  Remove the absolute `MEDUSA_ENV` constant and add:

  ```python
  def require_runtime_medusa_env(value: Path | None, *, validate_only: bool) -> Path | None:
      if validate_only:
          return value.resolve() if value is not None else None
      if value is None:
          raise SystemExit("--medusa-env is required for a runtime audit")
      resolved = value.resolve(strict=True)
      return resolved
  ```

  Both journey entry points must accept `--medusa-env` and pass the resolved path explicitly. Do not search sibling directories or fall back to another `.env.local`.

- [ ] **Step 4: Re-run the focused tests**

  Run the Task 3 Step 2 command.

  Expected: PASS.

- [ ] **Step 5: Prove the official Medusa reference**

  With the workspace-owned environment path, call `GET /store/products?q=Medusa%20T-Shirt` using its configured publishable-key header.

  Expected: HTTP 200 and exactly one matching product. Record only status, count, API version, and resolved non-secret environment path.

### Task 4: Persist multi-run Sandbox conversations

**Files:**
- Modify: `backend/src/corpus/features/sandbox/domain.py`
- Modify: `backend/src/corpus/features/sandbox/ports.py`
- Modify: `backend/src/corpus/features/sandbox/repository.py`
- Modify: `backend/src/corpus/features/sandbox/service.py`
- Modify: `backend/src/corpus/features/sandbox/schemas.py`
- Modify: `backend/src/corpus/features/sandbox/operations.py`
- Modify: `backend/src/corpus/features/sandbox/declarations.py`
- Modify: `backend/src/corpus/features/sandbox/bindings.py`
- Modify: `backend/src/corpus/features/sandbox/contracts.py`
- Modify: `backend/src/corpus/features/sandbox/feature.py`
- Test: `backend/tests/builder/test_sandbox_conversations.py`
- Test: `backend/tests/builder/test_builder_sandbox_services.py`

**Interfaces:**
- Consumes: unchanged `StartSandboxArguments` for a new conversation and `SendSandboxMessageArguments.conversation_id: UUID` for an existing conversation, both with the selected exact build.
- Produces: `SandboxConversationView`, `SandboxRunView.conversation_id`, `SandboxRunCollectionView.conversations`, and a new run whose runtime session is reused only when the conversation identity and build match.

- [ ] **Step 1: Write failing service and repository tests**

  Cover these exact cases:

  ```python
  first = await service.start(owner, agent, build_id=build.id, message="Find shirts")
  second = await service.send_message(owner, agent, build_id=build.id, conversation_id=first.conversation_id, message="Use the first result")
  assert second.conversation_id == first.conversation_id
  assert second.runtime_session_id == first.runtime_session_id
  assert second.runtime_run_id != first.runtime_run_id
  ```

  Also assert rejection for another owner, Agent, build, a nonexistent conversation, and a conversation with a waiting run.

- [ ] **Step 2: Run the tests and verify they fail**

  Run:

  ```powershell
  docker compose --env-file .env.local exec -T backend python -m pytest backend/tests/builder/test_sandbox_conversations.py backend/tests/builder/test_builder_sandbox_services.py -q
  ```

  Expected: FAIL because `conversation_id` and grouped conversation projections do not exist.

- [ ] **Step 3: Add the domain and schema contracts**

  Add these shapes:

  ```python
  @dataclass(frozen=True)
  class SandboxConversationRecord:
      id: uuid.UUID
      organization_id: uuid.UUID
      agent_id: uuid.UUID
      build_id: uuid.UUID
      runtime_session_id: str
      created_at: datetime
      runs: tuple[SandboxRecord, ...]

  class SandboxConversationView(BaseModel):
      id: uuid.UUID
      agent_id: uuid.UUID
      build_id: uuid.UUID
      created_at: datetime
      updated_at: datetime
      runs: tuple[SandboxRunView, ...]
  ```

  Add `conversation_id` to every `SandboxRecord`/`SandboxRunView`. Retain the flat `runs` collection during v0.2 compatibility; add grouped `conversations` as the authoritative playground projection.

- [ ] **Step 4: Reuse or create the exact session in the repository**

  Split repository creation from continuation:

  ```python
  async def begin(
      self,
      organization_id: uuid.UUID,
      agent_id: uuid.UUID,
      *,
      build: BuilderRecord,
      message: str,
  ) -> SandboxRecord: ...

  async def begin_in_conversation(
      self,
      organization_id: uuid.UUID,
      agent_id: uuid.UUID,
      *,
      build: BuilderRecord,
      conversation_id: uuid.UUID,
      message: str,
  ) -> SandboxRecord: ...
  ```

  `begin` always creates `AgentSandboxSession`. `begin_in_conversation` locks the selected session, verifies organization, Agent, and build identity, and creates only a new `AgentSandboxRun`. Reject a new run if the conversation already has a `waiting` or `running` run.

- [ ] **Step 5: Add the explicit surface-only continuation operation**

  Add:

  ```python
  class SendSandboxMessageArguments(BaseModel):
      agent_ref: str
      build_id: uuid.UUID
      conversation_id: uuid.UUID
      message: str
  ```

  Add `SandboxService.send_message`, `SendSandboxMessageHandler`, and the `sandbox.send_message` declaration with `allowed_sources={OperationSource.SURFACE}`. Bind it to a `send_message` affordance and a self-transition on `sandbox.home`. Delegate to `repository.begin_in_conversation` and the existing runtime gateway; do not add another execution adapter. Keep conversation/runtime IDs out of the public chat observation.

- [ ] **Step 6: Group conversations in `SandboxService.list`**

  Sort conversations by their latest run update descending and runs inside each conversation by creation time ascending. Derive `updated_at` from the latest run; do not add a migration merely for presentation ordering.

- [ ] **Step 7: Re-run focused backend tests**

  Run the Task 4 Step 2 command.

  Expected: PASS, including same-session context and all identity/failure cases.

- [ ] **Step 8: Export the changed Corpus frontend contract**

  Run:

  ```powershell
  docker compose --env-file .env.local exec -T backend python scripts/export_frontend_contract.py
  ```

  Expected: the generated contract contains the new surface affordance and `sandbox.send_message` input schema; `sandbox.start` remains the new-conversation contract and no unrelated compiled feature changes appear.

### Task 5: Add the read-only exact-build evaluation projection

**Files:**
- Create: `frontend/src/features/builder/SandboxEvaluationCoverage.tsx`
- Modify: `frontend/src/features/builder/SandboxSurface.tsx`
- Reuse unchanged: `frontend/src/features/builder/client.ts`
- Reuse unchanged: `frontend/src/features/builder/models.ts` evaluation types
- Test: `frontend/src/tests/sandbox-evaluation-coverage.test.tsx`

**Interfaces:**
- Consumes: `AgentRuntimeClient.evaluations(agentId)` and `EvaluationSetView[]`.
- Produces: `SandboxEvaluationCoverage({ buildId, evaluationSets, onOpenEvaluation })` with no mutation controls.

- [ ] **Step 1: Write the failing component tests**

  Assert the component shows:

  ```text
  Generating — queued/running
  Generated — exact case count plus category/difficulty counts
  Generation failed — exact public failure message and “Open Evaluation”
  Not evaluated — no matching exact-build set
  Eligible / Ineligible / Not run
  ```

  Assert there are no Generate, Add, Edit, Remove, Run, or Retry buttons in Sandbox.

- [ ] **Step 2: Run the tests and verify they fail**

  Run:

  ```powershell
  docker compose --env-file .env.local exec -T frontend pnpm test -- sandbox-evaluation-coverage.test.tsx
  ```

  Expected: FAIL because the coverage component does not exist.

- [ ] **Step 3: Implement the pure coverage projection**

  Select only `evaluation_sets.filter(item => item.build_id === buildId)`. Aggregate categories and difficulties from non-removed cases, show the latest attempt state without converting a failed run into ineligibility success, and call only `onOpenEvaluation` for management.

- [ ] **Step 4: Load evaluations with builds and Sandbox history**

  In `SandboxSurface`, load:

  ```typescript
  Promise.all([
    runtimeClient.builds(selected.id),
    runtimeClient.sandbox(selected.id),
    runtimeClient.evaluations(selected.id),
  ])
  ```

  Keep failures visible; do not silently render an empty evaluation set when the reader fails.

- [ ] **Step 5: Re-run the focused test**

  Run the Task 5 Step 2 command.

  Expected: PASS.

### Task 6: Render the real conversation-first Playground

**Files:**
- Create: `frontend/src/features/builder/SandboxConversationPanel.tsx`
- Create: `frontend/src/features/builder/SandboxDiagnosticsPanel.tsx`
- Modify: `frontend/src/features/builder/SandboxSurface.tsx`
- Modify: `frontend/src/features/builder/models.ts`
- Modify: `frontend/src/features/builder/builder.css`
- Test: `frontend/src/tests/sandbox-playground.test.tsx`
- Modify focused regression test: `frontend/src/tests/sandbox-clarification.test.tsx`

**Interfaces:**
- Consumes: grouped `SandboxConversationView[]`, selected exact build, `dispatchAffordance("start" | "send_message" | "resume" | "continue_to_evaluation", ...)`, and the coverage component from Task 5.
- Produces: conversation selector/new-conversation action, chronological transcript, composer, natural clarification, read-only Tests panel, and collapsed owner diagnostics.

- [ ] **Step 1: Write the failing Playground tests**

  Cover:

  ```typescript
  expect(screen.getByRole("heading", { name: "Playground" })).toBeVisible();
  expect(screen.getByRole("button", { name: "New conversation" })).toBeVisible();
  expect(screen.queryByText(runtimeSessionId)).not.toBeInTheDocument();
  expect(screen.queryByText(buildUuid)).not.toBeInTheDocument();
  ```

  Send two messages and assert the second dispatch is `send_message` with the same `conversation_id`. Assert “New conversation” clears that identity and the next dispatch is `start` without a conversation ID. Assert a waiting run disables ordinary sending and exposes only its natural clarification controls.

- [ ] **Step 2: Run the tests and verify they fail**

  Run:

  ```powershell
  docker compose --env-file .env.local exec -T frontend pnpm test -- sandbox-playground.test.tsx sandbox-clarification.test.tsx
  ```

  Expected: FAIL against the current diagnostics-first list.

- [ ] **Step 3: Update TypeScript projections**

  Add:

  ```typescript
  export interface SandboxConversationView {
    readonly id: string;
    readonly agent_id: string;
    readonly build_id: string;
    readonly created_at: string;
    readonly updated_at: string;
    readonly runs: readonly SandboxRunView[];
  }
  ```

  Add `conversation_id` to `SandboxRunView` and `conversations` to `SandboxRunCollectionView`.

- [ ] **Step 4: Implement conversation selection and sending**

  Default to the most recently updated conversation for the selected build. “New conversation” sets the selected conversation to `null` but preserves history. Dispatch:

  ```typescript
  await dispatchAffordance(
    selectedConversationId === null ? "start" : "send_message",
    selectedConversationId === null
      ? { agent_ref: selectedRef, build_id: buildId, message: request.trim() }
      : { agent_ref: selectedRef, build_id: buildId, conversation_id: selectedConversationId, message: request.trim() },
  );
  ```

  After completion, reload the authoritative Sandbox projection and select the returned/new conversation.

- [ ] **Step 5: Render the transcript and composer**

  Show owner messages from `run.message` and Agent messages from `run.final_response` in ascending run order. Show queued/running/waiting/failed states inline. Do not label a failed run as an Agent answer.

- [ ] **Step 6: Separate the three owner views**

  Use `Playground` as the default view, `Tests` for `SandboxEvaluationCoverage`, and `Diagnostics` for `BuildNavGraph` plus `SandboxRuntimeEvidence`. Diagnostics may expose owner-safe runtime IDs; Playground and Tests may not.

- [ ] **Step 7: Preserve clarification and review behavior**

  Keep the existing exact candidate labels and exact missing-input validation. Render clarification inside the transcript for the waiting run and resume that run; do not start another run.

- [ ] **Step 8: Add responsive and accessibility behavior**

  At widths below 800px, stack navigation, transcript, and composer; keep the composer visible without horizontal overflow; preserve semantic headings, labels, `aria-live` status/error output, keyboard focus after send, and visible focus styles.

- [ ] **Step 9: Re-run frontend tests**

  Run the Task 6 Step 2 command.

  Expected: PASS.

### Task 7: Prove the isolated real Sandbox feature

**Files:**
- Create: `scripts/run_sandbox_playground_journey.py`
- Create: `backend/tests/evaluation/test_sandbox_playground_journey_recorder.py`
- Create after proof: `docs/superpowers/validation/2026-08-19-sandbox-playground.md`
- Produce ignored evidence: `artifacts/2026-08-19-sandbox-playground/**`

**Interfaces:**
- Consumes: explicit Corpus/backend URLs, explicit `--medusa-env`, one newly created disposable owner lineage, and the real browser product path.
- Produces: normal-speed video, desktop/mobile screenshots, safe request diagnostics, exact build/conversation/run identity assertions, and a written validation record.

- [ ] **Step 1: Write the failing recorder contract test**

  Assert the recorder requires `--medusa-env`, never serializes credentials, creates a new owner through the visible UI, uses one exact Agent/build, and records chat-only, surface-only, and hybrid modes independently.

- [ ] **Step 2: Implement the bounded recorder**

  Record these mandatory checks:

  ```text
  official Medusa product read -> HTTP 200
  first Sandbox message -> succeeded, exactly one API call
  second message in same conversation -> same conversation/runtime session, new run
  ambiguous message -> waiting
  clarification -> same run reaches terminal without duplicate call
  new conversation -> new runtime session, old transcript retained
  exact-build ToolRouter coverage -> visible read-only
  Evaluation continuation -> same selected Agent/build
  reload and backend restart -> conversation and coverage retained
  invalid credential -> explicit failed result, no fallback
  deployed Operations -> no Sandbox activity
  ```

- [ ] **Step 3: Start/rebuild the local stack**

  Run:

  ```powershell
  docker compose --env-file .env.local up --build -d backend source-worker frontend
  ```

  Expected: all services healthy at ports 5199/8099 and the separately verified Medusa at 9100.

- [ ] **Step 4: Run focused contract suites**

  Run:

  ```powershell
  docker compose --env-file .env.local exec -T backend python -m pytest backend/tests/builder backend/tests/evaluation/test_evaluation_generation.py backend/tests/evaluation/test_evaluation_service.py -q
  docker compose --env-file .env.local exec -T frontend pnpm test
  docker compose --env-file .env.local exec -T frontend pnpm typecheck
  docker compose --env-file .env.local exec -T frontend pnpm build
  ```

  Expected: all pass. Test success does not replace Steps 5–7.

- [ ] **Step 5: Run the isolated feature journey**

  Run:

  ```powershell
  .\.venv\Scripts\python.exe scripts\run_sandbox_playground_journey.py --url http://127.0.0.1:5199 --backend-url http://127.0.0.1:8099 --medusa-base-url http://127.0.0.1:9100 --medusa-env "D:\Dev\AI Projects\saastoagent\routedeck\examples\medusa-agent\.env.local"
  ```

  Expected: all mandatory checks pass against one new local lineage with no unexpected browser, backend, worker, or runtime diagnostics.

- [ ] **Step 6: Inspect the rendered feature**

  Inspect Playground, Tests, and Diagnostics at desktop and 390x844. Verify transcript readability, composer visibility, natural clarification labels, collapsed diagnostics, no primary-view internal IDs, no horizontal overflow, and truthful failure copy.

- [ ] **Step 7: Write the validation record**

  Record the runtime location, command, exact smoke URLs, owner/build/source lineage using non-secret IDs, official Medusa version/reference, expected/actual results, video/screenshot paths, diagnostics, and any unverified behavior.

### Task 8: Reconcile owners and run release gates

**Files:**
- Modify: `architecture/code-map.md`
- Modify: relevant Sandbox component document under `architecture/components/`
- Modify: `test_index/README.md`
- Modify after fresh audit only: `audits/2026-08-v0.2-behavior-audit/**`
- Modify at closeout: `context.md` and a new checkpoint under `context_checkpoints/`

**Interfaces:**
- Consumes: passing isolated evidence and the exact implemented behavior inventory.
- Produces: aligned architecture/test documentation, a fresh canonical ledger campaign, and horizontal release evidence only after all blocking Sandbox behaviors pass.

- [ ] **Step 1: Update documentation owners**

  Record multi-run Sandbox conversation ownership, Evaluation read-projection ownership, exact focused tests, and the real journey command. Do not duplicate implementation detail into `context.md`.

- [ ] **Step 2: Validate architecture and documentation**

  Run:

  ```powershell
  .\.venv\Scripts\python.exe scripts\check_architecture_boundaries.py
  .\.venv\Scripts\python.exe scripts\check_doc_coverage.py
  .\.venv\Scripts\python.exe scripts\check_agent_design_parity.py --verbose
  .\.venv\Scripts\python.exe scripts\record_v02_behavior_audit.py --validate-only
  ```

  Expected: all pass without editing retained audit outcomes.

- [ ] **Step 3: Stop for Git baseline authorization**

  The controlling process requires the product state used by a new canonical campaign to have an explicitly authorized baseline. Do not stage or commit. Report the exact changed files and request Git authorization.

- [ ] **Step 4: Run a new full canonical campaign after authorization**

  The recorder has no selective Sandbox filter. Run the full campaign with the exact Medusa environment argument and a new disposable owner lineage. Preserve the previous campaign and append the new run; never rewrite the old failed evidence.

- [ ] **Step 5: Run horizontal acceptance only after the ledger gate**

  Run independent surface, chat, and hybrid journeys with uncut video only when all blocking Sandbox behaviors pass in the new canonical ledger. Preserve separate Sandbox and deployed identities throughout.

- [ ] **Step 6: Close the session**

  Follow `work_prompt.md`: retain evidence, write the completion checkpoint, and refresh `context.md` with the concise current restart state, remaining blockers, and exact next command.

## Completion Criteria

The plan is complete only when one exact local draft build can sustain multiple real messages in one isolated Sandbox conversation, start another independent conversation without deleting history, resume clarification in the same run, show ToolRouter-generated exact-build coverage without Evaluation mutations, retain state across reload/backend restart, expose owner diagnostics separately, fail visibly on a bad credential, and pass isolated, canonical, and horizontal evidence gates in that order.
