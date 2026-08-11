# Corpus Final Integration Tasks and Process

Date: 2026-08-11

Status: controlling owner task and process authority for the final integration stage

This document records the owner's tasks first and the mandatory execution
process second. It is not an implementation plan or a status report. It does
not replace the owner-authored
`docs/corpus-agent-design/feature-behavior-notes.md`.

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
