# Corpus Final Integration Tasks and Process

Date: 2026-08-11

Status: controlling owner task and process authority for the final integration stage

This document records the owner's tasks first and the mandatory execution
process second. It is not an implementation plan or a status report. It does
not replace the owner-authored
`docs/corpus-agent-design/feature-behavior-notes.md`.

## Read this before doing anything else

This is the first restart authority for the remaining Corpus work. After any
pause, context compaction, handoff, goal reset, or resumed session, the agent
must read this file and the owner-authored Behavior Notes before making a plan,
editing source, debugging a narrow failure, or launching evidence.

## Execution lock: tasks before plans or implementation

The owner task list in this file must be recorded and acknowledged before any
working plan is created or resumed. The active Goal Mode objective must name
this file and `docs/corpus-agent-design/feature-behavior-notes.md` explicitly.
Until both conditions are true, product implementation, narrow defect work,
browser campaigns, recorder work, and evidence polishing are prohibited.

This file is the task authority, not another implementation plan. A working
plan may order the next few actions only after this document is established;
it may never replace, summarize away, or narrow the owner tasks below.

The current task is not "design another plan" and it is not "finish the last
module touched." The task is to finish Corpus as one integrated product:

- retain the functionality that already works inside each feature;
- connect the 11 Behavior Note features into one understandable owner journey;
- close missing behavior, lifecycle, CRUD, recovery, and handoff gaps;
- make chat, surfaces, navigation, RouteDeck state, and persisted product state
  cooperate on the same task;
- make the surfaces and deployed Agent clear, polished, responsive, and useful;
- prove chat-only, surface-only, and hybrid use through the real product; and
- preserve complete, normal-speed internal evidence without omitting failures
  or awkward portions.

No narrower implementation plan, failing recorder, isolated feature, test
suite, or UI defect may replace this task. Plans are subordinate working aids;
this owner task list and the Behavior Notes remain the completion authority.

## Owner tasks — controlling list

1. Preserve the current working baseline in one meaningful `[WIP]` commit and
   push before further implementation. Inventory the exact included changes,
   exclude unrelated work, keep failed or incomplete behavior labelled
   truthfully, and do not treat the checkpoint as feature completion. After
   the checkpoint, restate the mandatory process in this document before
   changing product source again.
2. Preserve the working modules and stitch all 11 Behavior Note features into
   one coherent, understandable Corpus product before deeply polishing an
   isolated defect.
3. Audit every Behavior Note action and close the remaining behavior gaps:
   integrated handoffs, ordinary CRUD, lifecycle controls, durable asynchronous
   work, explicit retry and recovery, immutable lineage, rollback, promotion,
   and truthful failure states.
4. Make the configured real-model Corpus agent navigate, populate, and operate
   legal product surfaces through ordinary user chat. Do not hardcode a
   workflow or spoonfeed feature names, operation names, routes, nodes, IDs, UI
   instructions, or a sequence of microscopic commands.
5. Preserve one task and its exact Agent, Source, design, build, evaluation,
   deployment, and interaction lineage across chat, surfaces, navigation,
   reload, backend/worker restart, and changes of interaction mode.
6. Make surfaces genuinely usable and maximizable. On wide screens, maximized
   work keeps chat on the left and the active surface on the right. Mobile must
   remain independently usable.
7. Make Source Hub a guided workflow. Separate attachment from explicit
   processing; use standard API-definition language; show the real proven
   ToolRouter/Source semantic graph and its useful construction state; make
   file state, processing, connection, operation selection, Agent attachment,
   and the next action clear.
8. Make Agent Designer a visible miniature design studio. It must connect the
   Agent's goals and responsibilities, Source semantic groups, proposed
   behaviors, tools, policies, capabilities, surfaces, and the actual
   RouteDeck NavGraph that Builder will compile.
9. Replace weak NavGraph and deployed-Agent presentations with coherent Corpus
   UI grounded in real RouteDeck/runtime state. The deployed Agent must reuse
   the interaction quality and responsive layout already proven in Corpus,
   while owner-only diagnostics remain private.
10. Make ToolRouter clarification visible as real conversational waiting and
   continuation, not a hidden record or recorder-scripted exchange.
11. Preserve the independently working Builder, Sandbox, Evaluation, Channels,
    Deployment, public-session, rollback, and Operations behavior during
    integration. Do not replace it with a reduced integration-only version.
12. Close the obvious operational gaps without treating them as the whole
    product: Agent edit/archive/delete; Source description/delete; build
    start/stop/pause/delete; evaluation case create/edit/remove; channel
    availability/rollback; Operations promotion; and required explicit retry.
13. Fix shared interaction quality: after sending, focus returns to chat;
    streaming stays pinned when the owner is already at the bottom; deliberate
    user scroll-up is respected; status and navigation remain truthful.
14. Prove each material behavior independently through chat-only, surface-only,
    and hybrid chat-plus-surface paths. Chat may be omitted only for sensitive
    values such as passwords and credentials.
15. Produce complete internal development evidence: normal-speed, uncut,
    readable video from task start to final result, including slow, awkward,
    and failing portions; retain safe traces and exact diagnostics without
    rewriting evidence history.
16. Keep Design Studio, the implementation manifest, Corpus, authorized
    RouteDeck changes, architecture documents, tests, and evidence truthful and
    synchronized. Record every RouteDeck change and its purpose.

## Audited task state and remaining deliverables — 2026-08-11

This section updates the controlling list with the latest read-only boundary
and backend audit. It does not weaken any owner task above. A behavior remains
open until its real product path and required interaction modes are proven.

### Active delivery

- **Task 9 owner UI is implemented and rendered:** Builder, Evaluation, and
  Deployment reuse RouteDeck's real inspector for the exact immutable build.
  The map now exposes compiled totals and one focused runtime area's policies,
  surfaces, capabilities, legal navigation, and supervised tools instead of
  stacking every runtime contract beneath one cramped graph. The hosted Agent
  uses Corpus conversation/composer behavior and current capability actions;
  owner-only NavGraph and ToolRouter diagnostics remain private. Desktop,
  maximized split, selected-node, 390x844, and one real hosted safe-read path
  were inspected against the running product. A 44-second, 1280x720,
  normal-speed isolated video now proves the maximized owner NavGraph, selected
  runtime areas, and the hosted Agent result. Per-mode chat/surface/hybrid
  evidence remains a separate interaction gate.
- **Automatic exact-build evaluation coverage is delivered:** successful
  Builder completion now durably schedules ToolRouter generation for that exact
  immutable build. Builder shows queued/running/ready/failed generation state;
  Evaluation retains explicit retry for a failed generation and never retries
  or substitutes a case silently. A maximized, normal-speed isolated film proves
  build assembly, automatic generation, one real Sandbox clarification and
  validated Medusa taxonomy call, generated-case execution, and eligibility.
- **Durable asynchronous Builder assembly is delivered:** `builder.assemble`
  now persists one queued attempt and opaque durable job before returning. The
  source worker owns queued -> running -> ready/failed execution, never falls
  back to inline assembly, and preserves explicit failed-attempt retry. Builder
  polls authoritative build and exact-build evaluation state together so an
  owner can leave and return without losing progress. Local run
  `20260811T163659Z-73c50607a2` passed 15/15 with exact Source/design/build
  lineage, automatic evaluation scheduling, zero unexpected diagnostics, and a
  13.84-second normal-speed maximized Builder film.
- **Owner-described Designer generation is delivered:** `designer.generate_feature`
  accepts ordinary owner language through Agent and Surface sources, invokes the
  configured real model without a fallback, grounds the result in the exact
  selected Agent, pinned Source revisions, semantic groups, and saved curation,
  and appends one immutable draft. Selected API operations are repartitioned
  exactly once across capabilities and runtime areas before review. Surface run
  `20260811T171207Z-98270a1d7f` passed 12/12 with Revision 2 generation,
  Revision 3 owner customization, approval/build handoff, generated Product
  taxonomy NavGraph selection, zero unexpected diagnostics, and a 39.12-second
  normal-speed maximized Designer film. Chat-only and hybrid evidence remain in
  the later interaction-mode gate; they are not claimed by this surface run.
- **Workspace and selected-Agent aggregation are delivered:** Workspace answers
  authenticated owner/workspace questions and retains the selected Agent handoff;
  the Agent hub presents configuration, attached API versions, accepted design,
  build/evaluation status, deployment/channel state, hosted address, and Operations
  continuation from one owner-scoped overview. Current chat/hybrid campaigns must
  still prove the complete cross-feature continuation.

### Working foundations that must be preserved

- The horizontal backend path exists across Agents, Sources, Designer,
  Builder, Sandbox, Evaluation, Channels, Deployment, public sessions, and
  Operations. Exact lineage and owner boundaries are already load-bearing.
- The named operational controls now exist: Agent edit/archive/delete; Source
  description/delete; build run/pause/stop/reviewed runtime removal;
  evaluation case create/edit/remove and explicit run retry; channel
  availability; deployment retry/rollback; and Operations promotion.
- Source intake stages the attached API definition before a separate explicit
  analysis action. Source processing, Evaluation, and Deployment use durable
  worker-backed jobs with retained failure and explicit retry.
- The public deployed Agent reuses Corpus conversation and composer behavior;
  owner build/deployment diagnostics render the real compiled RouteDeck
  NavGraph; ToolRouter clarification has persisted Sandbox and public-session
  continuation paths.
- Shared chat focus and scroll behavior is implemented in the current working
  tree. Preserve it during surface-shell and feature integration.

These foundations are not a completion claim. They identify working modules
that later integration work must not reduce, replace, or mock.

### Closed regressions and current limitations

- Authenticated Lounge now shows one declared Continue to Workspace action and
  no anonymous account actions. Server-confirmed conversation snapshots survive
  the shell unmount/remount caused by RouteDeck Back, so the same owner's prior
  Lounge article visibly restores without a new conversation or direct URL
  mutation. Desktop and mobile normal-speed evidence is retained. A fresh 390x844
  rendered audit on 2026-08-12 confirms visible Corpus Back and Forward controls
  in the responsive header; disabled state remains truthful when no RouteDeck
  history exists.
- Current Sandbox is a real draft-runtime path, not a mock. The development
  Medusa catalog now contains real `Apparel`, `Catalog`, and `Essentials`
  taxonomy created/normalized through official Medusa workflows. The isolated
  product film proves a validated nonempty `Apparel` response and one API call.
- A duplicate local Ollama server caused an observed, persisted automatic
  generation failure. Corpus kept that failure visible and did not fabricate a
  case. After consolidating to one local server, the unchanged real Gemma
  generator and independent Qwen reviewer produced one accepted exact-subset
  case; the succeeding product path is retained separately.

### Remaining product and backend gaps

1. **Delivered: deepen Designer generation after the visible baseline.** The
   configured model now turns one ordinary owner-described behavior into a
   grounded immutable feature, policy, capability, runtime-area, and exact
   curated-tool delta. Existing capabilities retain every unselected curated
   tool; topology validation rejects duplicate, invented, missing, or
   unpartitioned operations. Review and build remain separate explicit steps.
2. **Delivered: Builder is genuinely asynchronous.** Assembly persists a
   queued attempt and durable job, runs only in the source worker, materializes
   the immutable build after exact rechecks, and schedules exact-build
   evaluation coverage. The surface shows queued/running/ready/failed and
   refreshes both build and generation truth; failure retry is explicit and
   retained. Do not regress this into inline or automatic retry.
3. **Delivered: generate the initial evalset from build completion.** Builder
   now schedules durable ToolRouter generation for the exact new build and
   exposes its state; Evaluation owns explicit failure retry and exact-build
   execution/eligibility. Do not regress this into a manual-only action.
4. **Delivered: owner-described Designer delta generation.** Preserve the real
   model boundary, exact Source grounding, exhaustive curated-tool ownership,
   immutable revision history, and no-build-before-approval separation. The
   remaining Designer work is only chat/hybrid evidence within item 7, not a
   missing product operation.
5. **Delivered: Workspace and selected-Agent aggregation.** Preserve the
   owner-scoped overview and legal feature continuations; final interaction-mode
   evidence remains part of item 7.
6. **Delivered: shared Source semantic-graph boundary.** Source Hub consumes the
   maintained ToolRouter/Source runtime visualizer for the complete persisted
   graph and construction replay. Non-executing route-plan creation and
   clarification retain exact curation/profile/revision boundaries; final
   interaction-mode evidence remains part of item 7.
7. **Finish current interaction-mode evidence.** Earlier horizontal evidence
   protects the baseline only. Prove every materially changed behavior through
   ordinary chat-only, surface-only, and hybrid paths, then prove one complete
   end-to-end owner journey in each mode. Do not count expected-operation
   assertions as proof that the model was not spoonfed.
8. **Reconcile all authorities before completion.** Studio, manifest, compiled
   Corpus, architecture documents, authorized RouteDeck report, tests, and
   evidence must agree. The current audit found ten Lounge parity mismatches,
   a stale documented host-node count, incomplete recording of authorized
   RouteDeck change families, and manifest statuses that conflate runtime
   implementation with mapping and evidence completion.

### Current task status summary

| Owner tasks | Current audited state |
| --- | --- |
| 1 | Partial: meaningful WIP commits exist, but the current branch is ahead of the tracked remote and has uncommitted integration work. |
| 2, 5, 11 | Strong backend foundation; preserve it while completing the integrated product. |
| 3, 12 | Most named CRUD/lifecycle operations exist; Builder async execution and automatic build evalsets are delivered. Aggregation and some recovery/evidence remain open. |
| 4, 14 | A real-model horizontal baseline exists; latest behaviors and per-behavior chat-only/surface-only/hybrid proof remain open. |
| 6, 9, 13 | Split/maximized shell, focused real NavGraph/public Agent composition, chat focus/scroll, and the isolated Task 9 video are implemented and rendered; per-mode evidence remains open. |
| 7 | Guided Source workflow is substantially implemented; shared visualizer ownership and full interaction symmetry remain open. |
| 8 | Owner-described real-model feature generation, immutable customization/review/build handoff, visible topology, and isolated maximized surface evidence are delivered; chat/hybrid proof remains open. |
| 10 | Runtime clarification paths exist; retain and re-prove them through current Sandbox and public-Agent flows. |
| 15 | Earlier normal-speed evidence exists; complete current evidence remains open. |
| 16 | Studio/manifest/compiled parity currently passes; final documentation/change-report reconciliation remains open until all modules finish. |

## Product behaviors that must remain explicit

These are named separately so they cannot disappear into a generic
"integration" or "UI polish" label after context compaction:

- Attaching an API definition stages it. Processing starts only after an
  explicit owner or agent-authorized action.
- User-facing Source language must not expose internal or non-standard terms
  such as `contract revision` when the owner is working with an API definition.
- The semantic graph uses the already-proven ToolRouter and Source runtime
  visualization, not an inferior handwritten duplicate.
- Dead-end prerequisite messages such as missing curation, connection, or
  design state must guide the owner to the exact next action and back to the
  same task.
- RouteDeck NavGraph UI must show the real topology with readable nodes and
  edges, selected-node detail, capabilities, policies, surfaces, operations,
  and relevant runtime state. Sparse cards, raw JSON, or decorative topology
  are not completion.
- The public deployed Agent must be a complete interaction product, not a
  sparse diagnostic shell. RouteDeck remains its interaction spine.
- Working feature modules must stay independently usable when joined into the
  horizontal product flow.
- Surface presence is not surface completion; module presence is not
  integration completion; CRUD presence is not behavior completion.

## Required conversational acceptance

The following is a representative acceptance scenario, not a hardcoded script.
For an ordinary request such as:

> Use this file please. Also set up the agent for me. I attached the API
> definition `openapi`.

the real Corpus agent must be able to:

1. recognize the attached file and explain that it will first add and process
   it as a Source;
2. populate the Source surface and process only after an explicit authorized
   action;
3. ask whether to use an existing Agent or create one when that choice is
   genuinely unresolved;
4. accept ordinary answers such as `create it` and `it is a shopping agent`;
5. create or select the Agent, attach the Source, and continue through
   operation selection, design, build, sandbox, evaluation, channel,
   deployment, and Operations as choices and reviews allow;
6. navigate and operate legal surfaces without asking the owner to name an
   internal module, click a hidden control, provide an ID, or restate state
   Corpus already owns; and
7. pause only for a real owner choice, clarification, sensitive value, or
   required review—not merely because the next legal action is on another
   surface.

This does not authorize guessed goals, credentials, operation selections, or
external writes. Corpus must ask only for genuinely missing owner decisions.

## Feature boundary

The tasks cover the full owner-authored Behavior Note sequence:

0. Lounge
1. Workspace
2. Agents and the selected-Agent operations hub
3. Source Hub
4. API Source / API Collection
5. Agent Designer
6. Agent Builder
7. Sandbox
8. Evaluation
9. Channels
10. Deployment
11. Operations

The shared asynchronous behavior for API processing, Builder, Evaluation, and
Deployment is mandatory: durable status, leave-and-return continuity, truthful
failure, and explicit retry.

## Mandatory process — controlling sequence

Every integration slice follows this sequence.

Before the next integration slice, complete the owner-requested meaningful
`[WIP]` Git checkpoint above and restate this process. That Git checkpoint is a
preservation boundary, not permission to claim completion or to narrow the
remaining work.

1. **Re-establish authority.** Read this document and the relevant owner-owned
   Behavior Notes. Inspect the accepted Design Studio behavior, manifest
   mapping, current RouteDeck contracts, live Corpus implementation, and the
   existing working module.
2. **Audit before editing.** Record what works, what is merely present, what is
   integrated, and what is absent, broken, or confusing. Identify the owning
   architecture/code-map subsystem and neighboring feature handoffs.
3. **Correct product design first.** If intended behavior materially differs
   from Studio, correct Studio before implementation. Keep product language and
   consequences in Studio; keep technical identifiers in the manifest.
4. **Pass the RouteDeck mapping gate.** Map
   `Studio concept -> RouteDeck contract -> Corpus implementation owner`.
   Inspect RouteDeck before claiming a framework gap. If a RouteDeck change is
   necessary, make only the smallest authorized change and record its exact
   purpose, files, compatibility impact, and validation.
5. **Preserve and integrate the working module.** Reuse its real public
   boundary. Do not rebuild it in a surface, adapter, neighboring feature, or
   recorder. Protect working behavior at risk of regression.
6. **Implement the smallest complete product slice.** Carry it vertically
   through persistence, service, RouteDeck operation/surface, frontend state,
   rendered interaction, failure/recovery, and both neighboring handoffs. Fail
   loudly; never use fixtures, canned responses, heuristics, cached success, or
   silent fallback in the product path.
7. **Validate the product before deep testing.** First exercise the real
   runtime and rendered desktop/mobile interaction. Then add focused tests for
   ownership, lineage, concurrency, review, failure, and recovery. Run broad
   gates only after the usable path works.
8. **Prove all interaction modes.** Chat-only uses ordinary owner language and
   the configured real model. Surface-only uses direct controls. Hybrid changes
   modes while retaining the same task and authoritative state. Evidence must
   come from real RouteDeck/model operations and exact state transitions.
9. **Record complete evidence.** Capture normal-speed uncut video, readable
   screenshots, allowlisted safe traces, and exact diagnostic counts. A failed
   campaign remains immutable and failed.
10. **Close truthfully.** Update only the owning Studio, manifest,
    architecture, flow, test, evidence, RouteDeck-change audit, and restart
    documents. Mark each behavior implemented-and-proven,
    implemented-but-unproven, partial, absent, or intentionally deferred.

## Horizontal work order

1. Audit the complete 11-feature flow and preserve every working module.
2. Establish the shared surface shell, maximize/split behavior, navigation
   continuity, status/action language, and chat continuity.
3. Complete Source intake, Source Hub guidance, semantic graph visualization,
   and Agent attachment continuity.
4. Complete Designer-to-Builder topology/NavGraph continuity and presentation.
5. Complete Builder/Sandbox runtime lifecycle and owner diagnostics.
6. Complete Evaluation, Channels, Deployment, public Agent, and Operations
   continuity and UI.
7. Close feature-specific CRUD, async lifecycle, retry, rollback, and
   promotion gaps.
8. Prove chat-only, surface-only, and hybrid behavior for every material slice,
   then one complete 11-feature flow in each mode.
9. Reconcile Studio, manifest, implementation, architecture, test meaning,
   evidence, and restart context.

Horizontal completion takes precedence over deep local polish. A narrow defect
may be repaired when it blocks the shared product flow, but it does not replace
this task list.

## Feature-first delivery and regression reporting

- Deliver the smallest complete, usable owner behavior before expanding unit
  coverage, polishing evidence machinery, or repairing non-blocking minor bugs.
- Keep the mandatory Studio, RouteDeck mapping, architecture, real-runtime, and
  truthful-evidence process. Process protects the feature; it must not become a
  substitute for delivering it.
- Fix a regression immediately only when it blocks the active feature path,
  violates safety or ownership, corrupts lineage, or makes completion evidence
  untruthful. Record lesser defects for the owning later task instead of letting
  them consume the active feature lane.
- Report every observed regression to the owner with its affected behavior,
  severity, retained evidence, and whether it blocks the current feature. Never
  hide, normalize, silently defer, or rewrite a regression as success.
- Tests remain proportional guards. A growing test count is not a deliverable
  and cannot be reported as feature completion without the real usable path.

## Milestone-isolated evidence

- A later feature must be reviewable without replaying every earlier feature.
  The horizontal recorder may prepare shared prerequisites once, but each
  feature checkpoint owns its exact assertions, identities, screenshots, and
  readable normal-speed video.
- `scripts/run_horizontal_product_journey.py --verify-milestone <name>
  --artifact <result.json>` validates a retained feature checkpoint without a
  browser, model call, registration, Source reprocessing, or downstream replay.
- A Designer checkpoint maximizes the surface before the first Designer
  operation. Chat remains on the left and the complete Designer surface stays
  on the right. The recorder emits a separate Designer-only normal-speed video
  while retaining the full raw campaign as the immutable source of truth.
- A milestone excerpt must disclose that it is extracted and link to the full
  raw campaign. It cannot replace missing chat-only or hybrid evidence.

## Failed Goal record — 2026-08-12

### Verdict

The autonomous final-integration Goal that ran through 2026-08-12 is **FAILED**.
It did not complete the controlling owner task, did not close all listed
Behavior Note features, and did not produce accepted current chat-only,
surface-only, and hybrid completion evidence. The Goal must not be described as
complete, mostly complete, or evidence-complete.

This is a failure of the execution process and completion claim. It does not
erase product behavior or immutable evidence that was independently completed
and accepted before or during the Goal. Every retained failed campaign remains
failed, and every independently accepted feature artifact retains only its
original bounded claim.

### Exact reason for failure

After focused feature work appeared green, the agent repeatedly launched the
complete 36-check ordinary-chat horizontal journey as an integration debugger.
Each late failure was diagnosed and patched, but the entire journey was then
started again instead of returning to the owning feature and proving that
feature boundary in isolation. This continued for roughly twelve hours.

That behavior violated this document's controlling process in four ways:

1. It violated **Milestone-isolated evidence** by replaying registration, model
   turns, Source processing, and already-proven downstream features instead of
   using an isolated feature checkpoint.
2. It violated **Feature-first delivery** by allowing recorder and evidence
   repair to become the main lane while feature acceptance remained open.
3. It violated the required validation order by treating the full horizontal
   campaign as a repeated diagnostic test rather than reserving it for the end
   of independently accepted modules.
4. It allowed the most recent recorder failure to control the work queue,
   instead of recording non-blocking defects against their owning feature and
   continuing the controlling task list.

The repeated runs were not required by the architecture or by RouteDeck. They
were an execution decision. The resulting delay is therefore not attributed to
the user, the Behavior Notes, the Design Studio, or a generic need for more
tests.

### Preserved truth at failure

- Surface-only run `20260811T232150Z-d840b95843` passed 36/36 within its exact
  recorded scope.
- Ordinary-chat run `20260812T034730Z-9f675b1edb` reached 32/36 and proved the
  current product through public deployment, second deployment, rollback,
  availability, and clarification before a recorder-owned Operations heading
  collision stopped it. It is still a failed full campaign.
- Runs `20260812T040521Z-4f270effaf` and
  `20260812T041707Z-1cedecbb60` each stopped at the Source post-approval
  continuation boundary. They remain failed evidence. The latter proves that
  `agents.return_from_source` was legal but semantically selected despite the
  owner's request to remain with the API.
- Independently accepted Lounge history, maximized Designer, asynchronous
  Builder, automatic exact-build evaluation generation, real Sandbox
  clarification/read, and owner NavGraph/deployed-Agent artifacts retain their
  bounded claims.
- A current full chat-only pass, a current hybrid pass, final broad gates, and
  final authority reconciliation were not achieved.

### Mandatory consequence

No new complete horizontal browser campaign may run until every listed feature
has a current isolated acceptance row and every blocking neighboring handoff is
closed. A full campaign failure may be diagnosed from its retained artifact,
but it may not trigger another full campaign. The owning feature returns to an
isolated lane first.

## Recovery plan of action — replaces the failed Goal's execution strategy

This recovery sequence is subordinate to the owner tasks above and to
`docs/corpus-agent-design/feature-behavior-notes.md`. It changes the execution
strategy, not the product scope.

### Phase 1 — establish the feature acceptance ledger

Create one current row for every Behavior Note boundary: Lounge, Workspace,
Agents/selected-Agent hub, Source Hub, API Source, Agent Designer, Agent
Builder, Sandbox, Evaluation, Channels, Deployment, and Operations. Each row
must record:

- implemented owner-visible behavior and both neighboring handoffs;
- missing behavior, CRUD, lifecycle, retry, recovery, lineage, or UI work;
- accepted Studio story and manifest mapping;
- exact Corpus and authorized RouteDeck owners;
- isolated chat-only, surface-only, and hybrid status;
- desktop/maximized/mobile evidence paths and diagnostic counts; and
- blocking and non-blocking regressions without converting either to success.

Existing evidence may populate a row only when its exact behavior remains
current. A test count or an old horizontal pass cannot fill a missing row.

### Initial feature audit and acceptance ledger — 2026-08-12

The owner notes contain twelve numbered product boundaries from Lounge through
Operations, plus the selected-Agent hub at section 2.5. Corpus groups some of
these into shared compiled features (`Source Hub + API Source`, `Builder +
Sandbox`, and `Channels + Deployment`). The ledger keeps the boundaries
separate so a working half cannot hide an incomplete neighboring half.

Status vocabulary:

- **implemented** means current product code and a compiled operation/surface
  boundary exist;
- **bounded evidence** means a retained artifact proves only the named path at
  its recorded revision;
- **accepted** requires a current usable path, neighboring handoffs, and the
  required isolated chat-only, surface-only, and hybrid evidence;
- **open** means acceptance is missing even when code and focused tests exist.

| Behavior Note boundary | Current implementation and bounded evidence | Critical gap analysis | Feature-isolated action and acceptance gate |
| --- | --- | --- | --- |
| **0. Lounge** | Manifest status is complete. Public help, registration, sign-in, password recovery, verification, and authenticated Continue-to-Workspace operations exist. Current desktop/mobile evidence proves authenticated history restoration without replacing the owner or conversation. A live 2026-08-12 read-only render shows a coherent anonymous Lounge with product help, Sign in, Create account, chat, NavGraph dock, and maximization. | The history fix has bounded evidence, but the complete current Lounge family has not been reaccepted as one isolated row after the latest shell changes. Credential paths must remain surface-only; product-help chat and authenticated hybrid return need current proof. | Run one short Lounge campaign: ordinary product-help chat; anonymous surface navigation; surface-only credential entry; authenticated browser/history return; declared Continue to Workspace; desktop and 390x844. Accept only with the same owner/conversation where applicable and zero relevant diagnostics. |
| **1. Workspace** | Owner overview and legal navigation to Agents, Sources, and verification exist. Surface and chat horizontal artifacts prove bounded navigation and file-first task entry. | Manifest remains partial. “Ask any Workspace question” and “ask to do any task” are broad intent-routing behaviors, not merely three buttons. Current file-first continuation and selected-Agent overview need isolated natural-language proof without product/operation spoonfeeding. | Prove three ordinary requests in isolation: status/overview, direct Agent work, and attached-file setup routed first to Sources. Surface-only quick actions and a hybrid continuation must retain one task. Accept when navigation never performs the destination mutation automatically and status remains owner-scoped. |
| **2. Agents + 2.5 selected-Agent hub** | Create, inspect, edit, source attach/detach, create-and-attach, open attached Source, archive, dependency-aware delete, immutable versions/build lineage, and downstream area navigation exist. The selected-Agent hub aggregates Source, design, build, evaluation, channel, deployment, URL, and Operations truth. Current horizontal evidence proves create plus exact Source attachment; older lifecycle evidence is bounded. | Manifest remains partial. The archive/delete browser journey stopped at 20/21 before a later handoff fix and has no complete replacement. Current edit, detach, archive, delete, dependency guard, existing-vs-new Source choice, and hub discoverability are not all accepted in the three modes. | Split into two isolated campaigns: (A) create/edit/select/attach/detach and selected-hub navigation; (B) archive reject/accept and dependency-free/dependency-blocked delete with reload. Prove ordinary chat, direct surfaces, and one mixed continuation; reviews and destructive consequences remain explicit. |
| **3. Source Hub** | Source inventory, staged API-definition intake, optional Markdown description, explicit analysis, status/retry, selected Source workspace, dependency-aware deletion, and Agent continuation exist. The successful 36/36 surface run proves the guided visible pipeline and maximized split within its exact scope. | The compiled manifest has a partial Source feature with zero accepted Source Hub behaviors, while API Source lives in a large design-only mapping. This is authority drift. Description and delete exist but lack current isolated interaction-mode evidence. The hub must remain an understandable inventory/entry surface rather than the entire API workflow. | First reconcile accepted Studio behaviors and manifest ownership without changing the user notes. Then prove add/open/description/delete/dependency guidance and leave-return status in isolation. Accept when attachment never starts analysis, the exact next action is visible, and chat/surface/hybrid retain the same Source identity. |
| **4. API Source / API Collection** | Explicit ToolRouter processing, durable failure/retry, connection profile and one-call check, complete persisted semantic graph plus construction replay, exhaustive curation, immutable API-version review, non-executing route planning, clarification, and reviewed read/write execution are implemented. Source-specific Phase A–F artifacts and the current surface run provide bounded proof for much of this path. | This is the current blocking row. After API-version approval, ordinary chat can legally call `agents.return_from_source` despite the owner explicitly asking to remain with the API. Current chat and hybrid acceptance therefore fail. Manifest still labels API Source unimplemented/design-only and contains stale `automated_e2e_pending` execution statuses. Current product-language, description/delete, processing recovery, and clarification evidence must be reconciled instead of inferred from older phases. | Correct the Studio semantic intent first, then map it through existing RouteDeck and Corpus owners. Run an isolated real-model post-approval scenario proving “stay with this API” remains in `sources.api`; separately prove explicit “return to my Agent” leaves. Then run isolated chat/surface/hybrid API setup through graph, connection, curation, and visible clarification, with credentials surface-only. This row blocks all final journeys. |
| **5. Agent Designer** | Real-model grounded proposal and owner-described feature generation, immutable customization, visible behaviors/policies/capabilities/tools/surfaces, shared topology/NavGraph, required review, acceptance, and build request exist. A maximized Designer-only surface film and the 32-check chat artifact provide strong bounded evidence. | Manifest remains partial. Current isolated chat-only and hybrid acceptance are missing; reject/no-mutation and return-without-building need explicit proof. Visual acceptance must continue to show intent, Source semantic groups, design objects, and the exact NavGraph together—not merely a form and graph. | Use the retained setup artifact to run Designer only: natural owner behavior request, generated grounded delta, customization, reject/no mutation, restage/accept, build request, and return. Record short maximized desktop and 390x844 evidence for surface-only; independently prove ordinary chat and hybrid continuation. |
| **6. Agent Builder** | Durable queued/running/ready/failed assembly, explicit retry, immutable exact-design/Source lineage, compiled per-build RouteDeck NavGraph, automatic exact-build evalset scheduling, runtime start/resume/pause/stop, and reviewed runtime removal exist. A 15/15 isolated assembly film and current surface/chat horizontal assertions prove bounded assembly and automatic generation. | Manifest remains partial. The Behavior Note says “delete a build,” while the current UI and service remove the build runtime and retain immutable build lineage. That semantic distinction is unresolved and must be made explicit in Studio/product copy. Current chat/surface/hybrid lifecycle controls, failed assembly retry, leave-return, and worker restart are not all accepted. | Decide and encode whether launch behavior is immutable build retention plus destructive runtime removal, or true build-record deletion with dependency rules. Then isolate queue/leave-return/restart/failure/retry and start/pause/stop/resume/removal. Accept only with one immutable lineage, automatic evalset scheduling exactly once, and no inline or automatic retry. |
| **7. Sandbox** | The actual isolated draft runtime, real compiled NavGraph, ToolRouter decision evidence, visible clarification subagent, same-run continuation, safe real Medusa read, nonempty taxonomy result, and redacted operation trace exist. The Evaluation milestone film and horizontal surface/chat assertions are strong bounded evidence. | Manifest is bundled partial with Builder. Current isolated chat-only and hybrid proof are missing. Separate Sandbox conversation/state from Corpus and deployed public activity is implemented but not yet one accepted interaction-mode row. Failure and no-call-before-clarification states need visible proof. | Prepare one exact ready build, then run Sandbox only: ambiguous request → visible waiting with zero calls → owner clarification → one validated read → meaningful response/trace. Prove new Sandbox session isolation and no inheritance into the deployed Agent. Capture maximized desktop/mobile surface evidence and ordinary-chat/hybrid equivalents. |
| **8. Evaluation** | Automatic exact-build ToolRouter generation, manual generation, categorized/difficulty-labelled case creation, edit, reviewed remove, durable queued runs, explicit generation/run retry, exact-build execution, metrics, and eligibility exist. The isolated Builder/Sandbox/Evaluation film and 36/36 surface run provide bounded proof. | Manifest remains partial. Current evidence does not accept the full CRUD family, failed generation/run retry, or Operations-promoted case in all interaction modes. “ToolRouter generated” must remain exact-build truth rather than a generic draft, and eligibility must not be inferred from a different case/build. | Isolate Evaluation with one ready exact build: automatic generated set, owner-created case, edit, reject/accept removal, failed-attempt explicit retry, successful run, eligibility, reload, and exact promoted interaction case. Prove list/table usability and semantic case selection through chat, surface, and hybrid. |
| **9. Channels** | Owner-scoped hosted Web channel creation, unique slug/address, visible active version, reviewed enable/disable, and public URL exist. Surface and chat horizontal evidence prove bounded create, pause, resume, and stable address behavior. | Manifest is bundled partial with Deployment. Current isolated hybrid proof, duplicate/invalid address recovery, and public-unavailable state are missing. Custom-domain linking is explicitly exploratory in the owner notes and must not be claimed as launch-complete unless Studio scope changes. | Isolate channel creation before deployment, slug collision/validation, pause/resume reviews, unchanged hosted address, and disabled public access. Prove chat, surface, and hybrid while keeping custom domains marked deferred/exploratory. |
| **10. Deployment** | Eligible-build deployment, durable queued/running/ready/failed status, required review, explicit failed retry, immutable second release, rollback, restart restoration, and hosted runtime binding exist. Current surface 36/36 and chat 32/36 artifacts prove deployment, second release, rollback, availability, restart, and public interaction within their scopes. | Manifest remains partial. A real product bug in deployment composition was fixed during the failed Goal, so current isolated acceptance must replace inference from earlier runs. The failed-deployment/retry path and current hybrid review continuation are still unproven. | Use a prepared eligible build/channel: reject deploy with no mutation; accept one deployment; force/observe one truthful failed attempt without fallback; review explicit retry; deploy a second build; rollback; restart backend/worker; verify exact active build and URL. Prove chat, surface, hybrid, and public clarification without owner diagnostics. |
| **11. Operations** | Owner-only deployed interactions, result/API activity, complete redacted decision trace, exact deployment/session/build lineage, deployed NavGraph, and promotion to a future Evaluation case exist. Surface 36/36 proves view, evidence, and promotion. | Manifest remains partial. The latest chat run stopped before Operations because of a recorder heading collision, so current chat-only and hybrid evidence are absent. Inspection must remain read-only: asking how an interaction ran must never invoke promotion. Promotion must appear in Evaluation exactly once and private evidence must never leak publicly. | Isolate from a retained deployed interaction: inspect result/trace through chat without mutation; inspect by surface; hybrid select then explain; explicitly promote once with category/difficulty; verify exact Evaluation lineage and duplicate prevention. Capture maximized owner evidence plus mobile; public session receives no owner diagnostics. |

### Cross-feature gap analysis

1. **Authority truth is the largest structural gap.** Lounge alone is marked
   complete. Every authenticated manifest feature remains partial, Source Hub
   has no behavior mappings, and API Source is still listed as unimplemented
   despite substantial implementation. Studio and manifest must be corrected
   per row before final acceptance, without altering the owner notes.
2. **Evidence symmetry is the largest acceptance gap.** The current surface
   journey passed 36/36, the strongest current chat journey is a failed 32/36,
   and the latest hybrid journey failed at 2 checks. Older accepted horizontal
   evidence protects its historical baseline but does not accept the expanded
   current behavior.
3. **The current product blocker is semantic continuity, not CRUD.** Source
   approval can leave the active API against explicit owner intent. Until this
   is corrected in Studio semantics and isolated real-model evidence, another
   complete journey is prohibited.
4. **Most named CRUD and lifecycle controls exist but are not yet accepted.**
   Agent, Source, Evaluation, Builder runtime, Channels, Deployment, and
   Operations controls are visible in code. The remaining work is exact
   consequence alignment, dependency/review/retry behavior, interaction-mode
   proof, and usable handoffs—not simply adding forms or endpoints.
5. **One product semantic decision is still open.** Builder currently deletes
   a runtime while retaining immutable build lineage; the Behavior Note says
   delete a build. The accepted design and copy must say which product promise
   is intended before the row can close.
6. **UX acceptance is uneven.** Current Lounge renders a clear task entry,
   chat, explicit account actions, NavGraph dock, and maximize control. Other
   complex surfaces have bounded rendered evidence, but no current screenshot
   audit covers every prerequisite, empty, failure, review, mobile, and
   maximized state. Those checks belong to each isolated row, not one late
   horizontal film.
7. **Cross-cutting lineage remains load-bearing.** Every row must preserve the
   exact owner, conversation, Agent, Source revision, curation, design, build,
   evaluation, deployment, and public interaction identities. A surface may
   not silently select “latest” when an exact historical identity is required.

### Feature execution order

1. API Source semantic-continuation blocker and Source authority reconciliation.
2. Source Hub inventory/intake/description/delete acceptance.
3. Agents and selected-Agent hub minimum working lineage: create/select the
   Agent, attach the exact ready Source, and expose the downstream work areas.
   Broader Agent edit/archive/delete acceptance follows after the operational
   Agent chain works.
4. Designer isolated chat/surface/hybrid acceptance for one runnable design.
5. Builder asynchronous assembly, exact runtime lifecycle, and automatic
   exact-build evaluation generation.
6. Sandbox clarification, one-call execution, result, trace, and runtime
   isolation acceptance.
7. Evaluation generated-set, exact-build run, eligibility, retry, and required
   case management acceptance.
8. Channels minimum hosted-Web binding needed by the eligible Agent.
9. Deployment review, version activation, public Agent, retry, rollback, and
   restart acceptance.
10. Operations inspection, decision/API evidence, privacy, and promotion back
    into Evaluation.
11. Return to Agents for the remaining edit/detach/archive/delete and
    dependency-review acceptance without disturbing the proven Agent lineage.
12. Workspace file-first routing, overview, and general task navigation.
13. Complete remaining Source Hub description/delete management if those
    non-blocking controls were not required by the operational Agent chain.
14. Lounge current-family refresh and final cross-feature shell/accessibility
    checks. Lounge is last only because its current implementation and bounded
    evidence are strongest; any authentication regression discovered by another
    row returns immediately to Lounge ownership.

This is an **operational-Agent-first** order. The first acceptance milestone is
not general CRUD completeness; it is one exact owner-scoped Agent that can be
created, sourced, designed, built, run in Sandbox, evaluated, deployed,
interacted with publicly, inspected in Operations, and promoted back into
Evaluation. Non-blocking inventory and lifecycle breadth follows that working
chain. Safety, ownership, lineage, review, or authentication blockers still
interrupt immediately and return to their owning feature.

This order does not authorize a horizontal campaign between rows. Each row
ends with its own accepted artifact or retained failed blocker. Only the final
integration phase below may launch the complete journeys.

### Six one-hour delivery phases — module-isolated execution

There are **six phases**, not one phase per feature or test. Each phase is one
owner-visible product deliverable and has a hard wall-clock limit of 60 minutes
from authority read to written handoff. The feature rows above remain the
acceptance checklist inside these phases.

Each phase uses this fixed clock:

- **0–10 minutes:** confirm Behavior Note, Studio, manifest, RouteDeck, Corpus,
  retained prerequisite, and the exact deliverable boundary;
- **10–35 minutes:** implement only the missing product slice;
- **35–50 minutes:** exercise each touched module independently at its current
  node through ordinary chat, direct surface, and one hybrid continuation;
- **50–55 minutes:** capture short normal-speed maximized evidence and exact
  diagnostics for the touched modules;
- **55–60 minutes:** stop all phase activity and record accepted or failed. No
  retry starts inside the same phase.

Module-isolated means the phase may reuse an exact retained prerequisite, but
it may not start at Lounge, register another owner, replay earlier features, or
invoke the complete horizontal chat/surface/hybrid recorder. If a prerequisite
is unavailable, the phase fails with that blocker instead of rebuilding the
journey. Tests remain proportional guards and cannot replace the deliverable.

| Phase | Maximum one-hour deliverable | Feature checklist inside the phase | Isolated evidence and hard stop |
| --- | --- | --- | --- |
| **1 — Working API Source — COMPLETED** | The working Source path is delivered: stage without processing, explicitly analyze, retain durable status, render the real semantic graph/replay, save and check the protected connection, curate operations, visibly clarify, and perform one safe routed read. | Source Hub; API Source. Phase A–F artifacts plus current 36/36 surface evidence retain their exact bounded claims. | **Do not redeliver or rerun this phase.** One later semantic regression remains at the outgoing Source→Agent handoff: “stay with this API” can select return-to-Agent. That is a narrow Phase 2 entry correction, not a new Source campaign. Stale Studio/manifest labels reconcile in Phase 6. |
| **2 — Runnable draft Agent — COMPLETED** | Close only the Source→Agent stay/return handoff, then create/select one Agent, attach the exact retained Source revision, preserve the already-delivered visible grounded Designer configuration, request and asynchronously assemble one immutable build, and expose the real compiled NavGraph. | Agents minimum lineage; selected-Agent hub; Agent Designer; Builder assembly. Broader lifecycle controls remain Phase 6. | Fresh isolated run `20260812T072222Z-dd4537e463` proves an ordinary chat request remains at the exact attached API Source, performs only the real read-only inspection, asks the owner to choose access, and never dispatches `agents.return_from_source` or replays Source processing. The 12.0-second normal-speed 1440×1000 clip is maximized and has zero HTTP, console, page, or request-failure diagnostics. Exact retained Designer `20260811T171207Z-98270a1d7f` and Builder `20260811T163659Z-73c50607a2` milestone verifiers remain accepted. Focused Agent/Source contracts pass 24/24 and recorder contracts pass 5/5. |
| **3 — Tested and eligible Agent — COMPLETED** | The real draft Agent has already been proven through visible ToolRouter clarification, zero-call waiting, one validated nonempty Medusa read, redacted trace, automatic exact-build ToolRouter evaluation generation, exact-build case execution, and deployment eligibility. | Builder runtime minimum; Sandbox; Evaluation generation/run/eligibility. | Accepted isolated run `20260811T153036Z-270ee701d6`: all 21 assertions are true and the corrected isolated verifier accepts 21/21; feature film `builder-sandbox-evaluation-maximized.webm` is 60.160 seconds at 1.0x with zero unexpected diagnostics. **Do not rerun this phase.** Evaluation CRUD/recovery breadth remains Phase 5. |
| **4 — Deployed and observable Agent** | Create the hosted Web channel, deploy the eligible build through review, interact with the public Agent through clarification and one safe call, then inspect the exact interaction and promote it into Evaluation. | Channels minimum; first Deployment; public Agent; Operations inspection/promotion. | Check Channels, Deployment, public Agent, and Operations independently from retained identities. Capture public privacy, exact build/deployment/session lineage, read-only inspection, and one explicit promotion. Stop on unknown delivery, privacy leak, unintended promotion, or duplicate case. |
| **5 — Operational lifecycle and recovery** | Complete the load-bearing lifecycle controls around the now-working Agent: Builder run/pause/stop/removal semantics and retry, Evaluation case CRUD/retry, Channel availability, Deployment failure/retry/second release/rollback/restart, plus exact lineage after recovery. | Builder lifecycle; Evaluation management; Channels availability; Deployment lifecycle. | Each module gets its own isolated check and short clip; destructive/reviewed actions use disposable records where required. Do not recreate the Source/Agent/design/build chain. Stop on ambiguous delete semantics, implicit retry, unknown external outcome, or lineage drift. |
| **6 — Product breadth, shell, and truth reconciliation — COMPLETED** | Finish non-blocking Agent/Source CRUD, Workspace routing/overview, Lounge/auth/history, chat focus/scroll, maximize/mobile behavior, then reconcile Studio, manifest, Corpus, authorized RouteDeck report, architecture, indexes, evidence, and run broad gates once. | Remaining Agents; remaining Sources; Workspace; Lounge; shared shell; all authority documents. | Isolated Agent milestone `20260812T133737Z-790bea8d` proves edit/version, attach/detach, dependency guidance, archive reject/accept, and delete reject/accept in a 27.68-second normal-speed maximized film. Isolated Source run `20260812T134036Z-db4f8fab` proves description versioning, dependency-blocked delete, reject, and accepted disposable deletion in a 39.5-second normal-speed maximized film without analysis or an API call. Current authenticated Lounge/history desktop/mobile films remain the shell/auth acceptance. A real archive selection race was corrected in Corpus; focused Agent tests pass. Full chat/surface/hybrid journeys remain explicitly outside this phase and require the gate below. |

#### Gate after Phase 6

The complete chat-only, surface-only, and hybrid journeys are not phase tests
or debugging tools. After all six phases are accepted and broad gates are
green, they require a separate explicit launch decision. Each gets one attempt;
a failure returns only to the owning phase and cannot trigger an immediate full
rerun.

#### Active phase queue after evidence reconciliation

All six feature phases are accepted. They remain retained foundations and may
be loaded only by their exact identities. A later regression can add a bounded
correction to its owning phase, but cannot reopen or replay a completed feature
film unless its accepted product truth is actually invalidated. The only next
gate is the separately authorized final chat-only, surface-only, and hybrid
journeys described above.

#### Deferred product-language and surface-design gaps — 2026-08-12

- Several evidence prompts repeat the word `consequences` to elicit the
  required-review path for deployment, rollback, and channel availability.
  Consequence disclosure is a valid internal review invariant and valid review
  copy, but the repeated word is tester vocabulary that can spoonfeed the
  model. Before final interaction-mode acceptance, replace those prompts with
  varied ordinary owner language such as asking what will change or requesting
  a review, while retaining the exact review and separate-acceptance checks.
- Several later feature surfaces, including Operations, are functionally
  styled but visually under-designed. They expose the correct headings,
  controls, state, and evidence, yet often read as lightly formatted document
  text rather than intentional Corpus product surfaces. Treat visual hierarchy,
  grouping, empty/loading/error states, responsive composition, and consistent
  polish with the stronger early Corpus surfaces as unfinished product work,
  not as optional cosmetic cleanup.
- Docked non-maximized surfaces can overflow toward the wrong axis/direction.
  Preserve this as a shared-shell responsive defect to verify across complex
  surfaces at representative dock widths. Do not hide it with per-feature
  clipping that would make content inaccessible.

#### Phase 4 checkpoint — 2026-08-12

- **Implementation and focused contracts are green:** Channels retains one
  unique hosted-Web destination; Deployment accepts only an exact eligible
  immutable build through required review and durable status; the public Agent
  owns a session-scoped conversation and real clarification continuation; and
  Operations projects owner-only result/API/decision evidence and promotes one
  exact successful interaction into an Evaluation case. Focused backend gates
  passed 13/13 and focused frontend gates passed 14/14. No RouteDeck change was
  required.
- **Live public behavior passed interactively:** existing hosted Agent
  `store-taxonomy-5b1edb` accepted the ordinary question `What product taxonomy
  is available?`, asked `Should I use product tags or product types?`, accepted
  `Product types.` in the same public session, and returned the real current
  `Apparel` type. The Browser console had no warning or error. This also
  supersedes the older sparse-data observation for the current local runtime;
  the Agent did not invent or suppress the type.
- **The one isolated recorder attempt remains failed evidence:** run
  `20260812T083522Z` retained a 69.760-second normal-speed 1440x1000 raw video
  and visually reached the real `Apparel` result, but the recorder awaited one
  exact text node even though the rendered sentence and bold value are separate
  DOM nodes. It timed out after the product result. The run is not reclassified
  as accepted evidence and was not retried automatically.
- **A bounded retained Phase 4 interval is accepted as partial evidence:** the
  immutable failed source campaign `20260812T034730Z-9f675b1edb` reached ten
  exact Phase 4 assertions: first reviewed deployment, exact deployed NavGraph,
  second reviewed release, rollback, reviewed pause/resume, backend and worker
  restart, public ToolRouter clarification with zero call, one resolved public
  read, and public privacy. The continuous derived film
  `phase4-deployment-public-operations-normal-speed.webm` is the unmodified
  305.920-second 1440x1000 interval from that source recording at 1.0x. It also
  visibly reaches the owner-only Operations surface with one interaction, one
  success, and one Evaluation candidate. The source campaign truthfully remains
  `failed`: its recorder used an ambiguous Operations heading locator and
  stopped before promotion. The committed recorder now scopes feature readiness
  to the direct surface header, but the retained run is not reclassified.
- **The partial milestone is fail-closed and reproducible:**
  `scripts/verify_phase4_retained_milestone.py` checks the immutable failed
  source status and exact terminal failure, the ten passed assertions, lineage
  IDs, expected screenshots and hashes, operation chronology, zero unexpected
  diagnostics, the continuous-film hash/duration, and the absence of
  `operations.promote_evaluation_case`. It reports `status=partial` and names
  `explicit exact-owner Operations promotion into Evaluation` as the sole
  missing Phase 4 behavior.
- **Exact-owner promotion remains open after a bounded internal recovery
  attempt:** the disposable owner's password was reset only through Corpus's
  product `AuthService` using a locally generated temporary value; that value
  was never retained and was subsequently replaced by a fresh random value.
  This is test administration, not authentication evidence. Normal sign-in
  successfully reached the same owner organization and exact Agent, but its
  anonymous-conversation adoption retired the retained conversation
  `Ttzpd0t0NBNtzYcXEDSoKj3a3zl901ZA` and created new owner conversations. The
  Agent, build, deployments, public interaction, and Operations lineage remain
  intact; the retained conversation/history does not. Record this as a Corpus
  conversation-replacement regression, not as proof of data loss outside that
  conversation boundary.
- **Promotion evidence was not manufactured:** isolated recorder attempts
  `20260812T095746Z-0f4635ee`, `20260812T100314Z-5628b9b8`,
  `20260812T100420Z-a714fc22`, and `20260812T100813Z-64142230` stopped during
  setup/readiness before dispatching `operations.promote_evaluation_case`.
  Current persistence contains zero Operations-sourced Evaluation cases for
  interaction `int_78f435f2522e47c5836a0e58ce7e88ed`. The attempts exposed
  recorder readiness issues (Agent and Operations async loading) and repeated
  reset/sign-in instability; they are retained as failed diagnostics and are
  not accepted video evidence. Phase 4 therefore remains product-implemented
  and partially evidenced, with exact Operations promotion plus the newly
  exposed sign-in conversation-preservation regression still open. Earlier
  feature phases were not replayed and no tenant state was copied to another
  owner.
- **Phase 4 is now accepted.** Run `20260812T111732Z-179c335f` dispatched the
  exact supervised `operations.promote_evaluation_case` operation once for
  interaction `int_78f435f2522e47c5836a0e58ce7e88ed`; Corpus completed it
  with outcome `promoted`. That recorder truthfully remained failed because a
  post-reload check searched for a disabled control inside a collapsed details
  element. No second promotion was attempted. Read-only continuation run
  `20260812T111946Z-88961b32` opened that exact retained interaction, proved
  the promoted control disabled after reload, navigated through the declared
  Agent-to-Evaluation affordance, and found exactly one Operations-sourced case
  `d06b3b03a3034370966ac891545b1122` with exact interaction/build/API-operation
  lineage. Its 21.480-second 1440x1000, normal-speed, maximized-surface film is
  `artifacts/phase4-operations-promotion/20260812T111946Z-88961b32/phase4-operations-promotion-normal-speed.webm`
  (SHA-256 `4e1cef7561efa4b279b818761684dd22408c47f380107e4433b91ffd91b2e022`).
  The continuation retains three screenshots and zero HTTP, console, or page
  errors. This closes the sole missing Phase 4 behavior without replaying
  Source, Designer, Builder, Sandbox, Evaluation execution, or Deployment.

#### Phase 5 checkpoint — 2026-08-12

- **Builder lifecycle is accepted without rebuilding the Agent.** The retained
  exact build was started, paused, reloaded, resumed, stopped, and its draft
  runtime was removed through reject-then-accept review. Immutable build,
  Source, NavGraph, and Evaluation lineage remained unchanged. The product
  mutation run `20260812T115751Z-1f42126f` completed the lifecycle but retained
  a recorder-only terminal copy mismatch; read-only continuation
  `20260812T120029Z-0acc5777` accepted the durable removed state. Its 12.040s
  1440x1000 normal-speed maximized film is
  `artifacts/phase5-builder-lifecycle/20260812T120029Z-0acc5777/phase5-builder-lifecycle-normal-speed.webm`
  (SHA-256 `02ff798a3f56bbac4707ae9d0c60ad2ed301212e65bbdc9a1fd23b7fe50feed3`).
- **Evaluation CRUD and explicit retry are accepted.** Live evidence exposed a
  real Corpus integration gap: the Evaluation node declared
  `evaluation.retry_case_run`, but the exact selected-Agent binding omitted it,
  so RouteDeck correctly blocked the surface action before its handler. The
  binding now includes the operation and 36 focused Agent/Evaluation/Workspace
  tests pass. One explicit retry appended a distinct immutable attempt linked
  to the original and truthfully failed with the same unresolved natural
  Sandbox-answer requirement; no automatic retry occurred. Run
  `20260812T122357Z-ce380e01` then appended Evaluation case revision 2,
  rejected one removal review, accepted a fresh removal review, and preserved
  both revisions after reload. Its 25.280s 1440x1000 normal-speed maximized
  film is `artifacts/phase5-evaluation-management/20260812T122357Z-ce380e01/phase5-evaluation-management-normal-speed.webm`
  (SHA-256 `3432eeb8b36aa5c6eeaf18200a9ff4bea7163cec88a3771dfe3b3e840ca9fa88`).
- **Hosted Web availability is accepted against the real public-session
  contract.** Run `20260812T123012Z-d40850a1` rejected one pause review, then
  accepted pause and resume. Public session creation was 200 before, the exact
  intentional 503 while paused, and 200 after resume; channel ID, deployment
  ID, hosted address, and active build were restored exactly after reload. Its
  24.840s 1440x1000 normal-speed maximized film is
  `artifacts/phase5-channel-availability/20260812T123012Z-d40850a1/phase5-channel-availability-normal-speed.webm`
  (SHA-256 `86d41ecc5ddb7d4db87bec90d836a8daea25e6bdd3967aa6742b36e1dc199bbd`).
- **Deployment rollback and restart recovery are accepted.** The retained
  hosted channel has exactly two immutable successful releases. Run
  `20260812T123342Z-ca35e945` rejected one rollback, accepted rollback to the
  alternate release, restarted the backend, proved the alternate release still
  active, then accepted restoration to the original release. It created no new
  deployment and the complete channel/deployment records matched preflight at
  close. Its 66.200s 1440x1000 normal-speed maximized film is
  `artifacts/phase5-deployment-recovery/20260812T123342Z-ca35e945/phase5-deployment-recovery-normal-speed.webm`
  (SHA-256 `f4af5a138863ae5746ac77071b2a2b17f7e9e8b80bfa2c953c4ee9b787833689`).
  No retained product deployment is failed, so failed-deployment retry was not
  fabricated for browser evidence. Its real service/persistence boundary is
  covered by focused tests: only a definitely failed deployment can create one
  new reviewed lineage, and no automatic retry is permitted.
- **Retained failures remain failures.** Setup/readiness and recorder-locator
  failures under `artifacts/phase5-*` are not accepted evidence. The first
  Channel film also used the wrong public HTTP method and remains failed; the
  accepted film uses the actual `POST /api/public/agents/{slug}/sessions`
  contract. Phase 5 did not replay Source, Designer, Sandbox, public-agent
  interaction, Operations, or any full chat journey.

#### Phase 6 checkpoint — 2026-08-12

- **Agent lifecycle breadth is accepted as an isolated milestone.** Parent run
  `20260812T133737Z-790bea8d` remains failed because its later Source context
  used an ambiguous recorder heading. Its completed Agent prefix is preserved
  separately and fail-closed in `agent-milestone-result.json`: one disposable
  Agent reached immutable configuration version 2, attached and detached the
  exact retained ready Source revision, showed dependency-blocked deletion,
  rejected and accepted archive, then rejected and accepted permanent deletion.
  The 27.680s 1440x1000 normal-speed maximized film is
  `artifacts/phase6-product-breadth/20260812T133737Z-790bea8d/phase6-agents-normal-speed.webm`
  (SHA-256 `5406c28105708ff2c5b5a0dbc80de2c9a6f9650642e3ae3e075253ec220f8588`).
- **A real archive-selection race was corrected.** Accepted archive/delete
  could leave the removed Agent selected long enough for attachment,
  dependency, build, and overview refreshes to return 404. Corpus now clears
  selected detail state before accepted lifecycle execution and restores it
  only when acceptance fails. The Agent surface suite passes 18/18 and the
  full frontend suite passes 188/188.
- **Source lifecycle breadth is accepted independently.** Run
  `20260812T134036Z-db4f8fab` used the exact retained local Medusa definition
  only as owner input, never analyzed it and never called the target API. It
  showed deletion blocked for the retained Source with Agent/build lineage,
  added a disposable accepted Source, saved separate Markdown description,
  rejected its first deletion review, accepted a fresh deletion review, and
  removed only that disposable Source. The 26.200s 1440x1000 normal-speed
  maximized film is
  `artifacts/phase6-product-breadth/20260812T134036Z-db4f8fab/phase6-sources-normal-speed.webm`
  (SHA-256 `db0e4ae6a277e6e569577aa9acbd65a3ab17d682e21c928fb2c7ebd31515bce8`).
  It has zero unexpected HTTP, console, or page diagnostics.
- **Shell/auth/history retain current isolated acceptance.** Existing owner
  desktop and 390x844 normal-speed films remain at
  `artifacts/authenticated-lounge-history/20260811T151635748Z/`; they prove the
  same owner/conversation and Lounge article across Workspace -> Back ->
  owner-aware Lounge -> declared Continue to Workspace. Chat focus/stream
  pinning/deliberate-scroll preservation and dock/maximize bounds remain green
  in the current 188-test frontend suite.
- **Broad gates are green.** Backend passes 510/510 with six known dependency
  deprecation warnings. Frontend passes 35 files / 188 tests; strict typecheck
  and production build pass with the existing >500kB chunk warning. Studio
  parity, architecture boundaries, generated frontend contract currency,
  manifest JSON, recorder compile, and whitespace checks pass. No RouteDeck
  change was needed for Phase 6 and the user-owned Behavior Notes were not
  modified.
- **Retained setup/recorder failures remain failures.** The first Agent attempt
  used the review-button label inside the lifecycle card; two Source attempts
  used ambiguous names; and a later Agent-only attempt hit the fixed-hour
  sign-in limiter before Workspace. None is reclassified or used as accepted
  whole-run evidence. The two accepted module boundaries above are explicit.

### Phase 2 — close one feature at a time

For each open row, in the operational-Agent-first order above:

1. Re-read the feature note and current Studio/manifest/RouteDeck mapping.
2. Audit the live usable path and identify the smallest missing owner behavior.
3. Implement that complete slice through persistence, supervised operation,
   surface, rendered state, failure/recovery, and neighboring handoffs.
4. Prove it in isolation through ordinary chat-only, direct surface-only, and
   hybrid continuation. Sensitive credential values remain surface-only.
5. Record a short, readable, normal-speed video with the working surface
   maximized where applicable; preserve the full isolated raw recording.
6. Mark the row accepted or retain it as failed with its exact blocker. Do not
   enter another feature while a blocking handoff from the current row remains
   unresolved.

The first recovery row is the current Source/API Source boundary: an owner's
explicit request to stay with the approved API must not be interpreted as a
request to return to the Agent. Prove this with an isolated real-model Source
post-approval scenario before any horizontal replay.

#### Phase 2 attempt record — 2026-08-12

- **Mapped behavior:** accepted API update remains in API Source unless the
  owner explicitly asks to leave or requests an Agent action that cannot be
  completed there → existing RouteDeck navigation operation
  `agents.return_from_source` → Corpus Agent declaration and Source active-API
  continuation policy. No RouteDeck repository change was required.
- **Implemented correction:** the return operation no longer treats unfinished
  API access selection as an implicit reason to leave Source. The Source policy
  now returns and updates an attachment only after explicit owner intent to
  update the attachment or continue Agent setup.
- **Focused proof:** Workspace/Agent plus Source feature contracts passed 24/24.
  The isolated retained Designer verifier accepted
  `20260811T171207Z-98270a1d7f`; the isolated retained Builder verifier accepted
  `20260811T163659Z-73c50607a2`. Neither replayed Source or a full journey.
- **Failed changed-behavior evidence:** the one bounded recorder attempt
  `20260812T062617Z-f8d5b75d2b` failed before a screenshot/video could be
  accepted. Restoring retained conversation
  `Wt_OTq2NEcFOpiQ9NTW1eJH4vP3xDg72` did not expose the declared
  `Manage sources` affordance and the run observed HTTP 404 for
  `/api/routedeck/private-forms/sources-api-connection`. The run performed no
  Source processing, Agent mutation, attachment, design, build, or later-stage
  work. The phase stopped after that attempt as required.
- **Recorder correction after the stopped phase:** the Phase 2 recorder now
  separates `preflight`, `record`, and offline `verify`. Preflight resolves the
  exact authenticated conversation and RouteDeck inspection and requires the
  exact `sources.api` node before any browser or video starts. Record requires
  the canonical session-bound resume URL, captures one ordinary chat turn,
  checks the typed operation chronology for absence of
  `agents.return_from_source`, requires the Source node to remain selected,
  and finalizes video in `finally` even on failure. The original retained
  conversation no longer exists in the authoritative conversation table, so
  the corrected preflight now rejects it immediately with
  `conversation_not_found`; no replacement product action was attempted.
- **Fresh accepted evidence:** run `20260812T072222Z-dd4537e463` created a new
  conversation and legally entered the exact retained Agent
  `f751de1f-ed9f-4f59-8ad7-2c42e3b08d43`, Source `Xt4FD3TTNyNw8yL1`, and
  revision `sJiCBosgl7UHuzSM` through `workspace.open_agents`,
  `agents.select_agent`, and `agents.open_attached_source`. The one ordinary
  chat turn dispatched only `sources.inspect_current_api`, remained at
  `sources.api`, and produced owner-facing operation-access clarification.
  Four assertions passed with no Source processing, Agent mutation, design,
  build, or full-journey replay. The retained normal-speed maximized video is
  `artifacts/phase2-source-agent-handoff/20260812T072222Z-dd4537e463/raw-video/page@33e3dfe1c9bb73b24df5af92da18329f.webm`;
  duration 12.0 seconds; SHA-256
  `d13e7153771c7676c26c7a80c0c1ca4b294397b2deacb14e4165548c9ae595c4`.
  The same run's screenshot SHA-256 is
  `b8927aac17446206ed8ae551f9a2b9b69453783687e28f08f6d4e32dda19192a`.
  All retained HTTP, console, page, and request-failure diagnostic lists are
  empty. The earlier failed attempt remains disclosed above and is not
  reclassified as evidence.

### Phase 3 — proportional gates and regression handling

- Run focused contracts for the active feature and its two handoffs after the
  usable path works. Broad backend/frontend/Studio gates run once after all
  feature rows are accepted, not after every recorder correction.
- An isolated evidence campaign has a fifteen-minute hard wall-clock limit.
  On failure, stop, retain the artifact, diagnose offline, and return to the
  feature lane. No automatic campaign retry is permitted.
- Fix immediately only a regression that blocks the active behavior, violates
  ownership/safety/lineage, or makes its evidence false. Record other
  regressions in the owning ledger row and continue.
- Recorder bugs may change recorder code and focused recorder tests; they may
  not redefine product behavior or cause a full-product rerun.

### Phase 4 — final integration evidence only after feature acceptance

When every feature ledger row is current and accepted:

1. Run broad backend, frontend, Studio, generated-contract, parity,
   architecture, documentation-coverage, migration, and runtime health gates.
2. Run exactly one current ordinary-chat-only journey using natural owner
   requests, one surface-only journey, and one hybrid journey. Preserve exact
   lineage and normal-speed uncut evidence.
3. If a final journey fails, retain it as failed and return only to the owning
   isolated row. Do not loop the complete journey.
4. After all three modes pass, reconcile Studio, manifest, compiled Corpus,
   authorized RouteDeck change report, architecture, flow index, test index,
   validation log, checkpoint, and `context.md`.

### Recovery completion gate

The replacement Goal may be marked complete only when the feature ledger is
fully accepted, all three current interaction modes pass, final gates are
green, all retained failures remain disclosed, and the full owner task list is
reconciled. Progress through many features or a near-complete horizontal run is
not completion.

## Anti-drift and execution gate

- Read this document and
  `docs/corpus-agent-design/feature-behavior-notes.md` after every context
  compaction and before any new plan, source edit, narrow debugging lane, or
  evidence campaign.
- Goal Mode must explicitly reference both files.
- No implementation plan may replace or narrow the owner tasks above.
- A failing test, recorder, browser campaign, or RouteDeck issue remains a
  subtask unless it blocks the horizontal product path.
- Evidence work cannot become the main lane while known integration or UI gaps
  remain.
- Completion is assessed against this whole task list and all Behavior Notes,
  not the last repaired module or passing test.
