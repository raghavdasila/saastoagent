# SaaStoAgent v0.1 Context

Last Updated: May 24, 2026 10:32 IST
Project: SaaStoAgent v0.1
Status: RouteDeck/Corpus state boundary cleanup is implemented and validated by
backend contract tests plus frontend type-check. Docker browser E2E still needs
to be rerun after the next runtime-facing change.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

## Start Here

- Latest checkpoint: `context_checkpoints/context_checkpoint_24-05-2026-10-32AM.md`
- Previous context archived at:
  `context_history/20260524_1032_context_before_routedeck_boundary_closeout.md`
- Closeout log:
  `logs/20260524_1032_routedeck_boundary_state_closeout.md`
- Framework RouteDeck anchor: `../routedeck/docs/agentic-ui-state-runtime.md`
- Product anti-drift vision: `architecture/route-deck-corpus-vision.md`
- Boundary ADR: `decisions/ADR-013-routedeck-corpus-boundary.md`
- Dev validation:
  `architecture/dev_validated_docs/2026-05-24_routedeck_boundary_state_validation.md`
- Current plan/status: `plans/routedeck_runtime_store_reset_plan.md`
- RouteDeck test index: `test_index/route-deck-contract.md`
- Horizontal E2E guide: `docs/horizontal-e2e.md`

## Current Architecture

RouteDeck is the reusable state management layer for agentic apps. Corpus is
the SaaStoAgent product/application layer that consumes RouteDeck. LangGraph and
backend services remain the execution/runtime truth until Corpus navgraph
execution is explicitly modeled as a LangGraph graph.

```text
LangGraph/backend services
  -> CorpusGraphRuntime
    -> CorpusRouteDeckRuntime
      -> generic RouteDeckRuntime state/projection/dispatch contract
        -> RouteDeckStore / @routedeck/react
          -> AppGraphShell
            -> Corpus conversation
            -> inline setup/execution surfaces
            -> docked/fullscreen diagnostics

Deployed visitor chat
  -> /api/deployed-agents/{slug}
  -> /api/deployed-agents/{slug}/chat
  -> public-safe session event stream
  -> shared chat/runtime/execution services
```

Core rules:

- Graph/runtime services own truth, guards, and commits.
- RouteDeck owns generic agentic app state: projections, operations, operation
  readiness, active surfaces, runtime snapshots, events, diagnostics, and
  React-facing store/hooks.
- Corpus owns SaaStoAgent-specific conversation, prompts, setup behavior,
  SaaSAgent selection, recovery wording, public chat behavior, and product
  surface interpretation.
- Zustand is not the agentic app state layer. `saasAgentUiStore` owns only
  ephemeral UI concerns such as tabs, drafts, local selections, and a mirrored
  active SaaSAgent id for shell ergonomics.
- RouteDeck operations expose `invocation_kind`, `can_dispatch_now`,
  `required_args`, and `missing_args`; UI must not dispatch unbound operations.
- Builder diagnostics may expose graph internals, tool IDs, paths, traces, and
  approval metadata.
- Public deployed chat must not expose router internals, scores, endpoint paths,
  operation IDs, trace IDs, approval IDs, or raw tool labels.
- ToolRouter is a backend-local adapter. It owns route/top-k/missing-param/
  policy/unsafe decisions; REST execution traces remain the executor of record.
- Product runtime must remain OpenAPI/user-config driven. Medusa is an
  acceptance fixture only, not hardcoded product logic.

## Implemented Since Last Closeout

- Clarified RouteDeck as reusable agentic app state management, not only
  navigation/debugging.
- Introduced named Corpus-owned RouteDeck runtime boundaries:
  - `CorpusRouteDeckRuntime`
  - `CorpusRouteDeckStateProjector`
  - `CorpusOperationPolicy`
  - `CorpusSurfaceRegistry`
  - Corpus navgraph helpers
- Removed stale backend SaaStoAgent RouteDeck adapter naming and deleted
  `backend/services/app_graph/routedeck_adapter.py`.
- Routed `/api/corpus/state` through `route_deck_runtime.snapshot(...)`.
- Routed `/api/corpus/action` through `route_deck_runtime.dispatch(...)`.
- Kept `/api/corpus/stream` split by responsibility:
  - RouteDeck projection streaming for empty state subscriptions
  - `CorpusGraphRuntime` natural-language streaming for user turns
- Added route-local conversion helpers from RouteDeck runtime/dispatch results
  into Corpus response DTOs.
- Added backend contract tests for the RouteDeck runtime boundary and stale
  adapter-name removal.
- Reworked frontend RouteDeck/Zustand boundary:
  - `AppGraphShell` derives active SaaSAgent identity from RouteDeck state
  - `api.withSaaSAgent(...)` makes SaaSAgent context explicit per request
  - `saasAgentUiStore` replaces `saasAgentStore` for UI-only state
  - `corpusRouteDeckCatalog.ts` centralizes Corpus RouteDeck ids and surface
    component names
- Preserved the RouteDeck surface-opening hook path so surface transitions can
  show "Opening surface" without page navigation.

Earlier horizontal work remains active:

- deployed chat at `/a/:slug`
- public-safe approval event stream
- owner approval/cancel delivery back to visitor sessions
- RouteDeck dispatch-readiness metadata
- `saas_agent.list` selector surface and bound `saas_agent.open`
- Docker UI E2E for signup -> create agent -> connect OpenAPI -> activate ->
  deploy -> public chat -> guarded approval
- Medusa as acceptance fixture only, not product runtime logic

## Verification

- Backend boundary suite:
  `python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q`
  - Result: `65 passed`
- SaaStoAgent frontend:
  `npm run type-check`
  - Result: passed
- Backend source scan for stale adapter names:
  - no `SaaStoAgentRouteDeckAdapter`
  - no `routedeck_adapter`
  - no `test_routedeck_adapter_contract`

Important rule: future claims of "E2E passed" for this slice must include the
Docker UI harness or an equivalent browser-driven replacement. Backend tests
alone are not sufficient.

## Known Issues To Carry Forward

### Browser E2E Not Rerun

Docker browser E2E was not rerun after the RouteDeck boundary cleanup. Before
claiming the whole product path is still green, rerun:

- `npm run e2e:docker`
- `npm run e2e:medusa:docker` when the Medusa target is available

### Surface Transition Flicker

The architectural boundary is now cleaner, but the observed surface/auth
flicker still needs browser-level regression coverage. The rule remains:
surface opening must stay inside React and must not cause full page navigation.

### Raw JSON Public Result UX

Deployed chat still exposes raw JSON directly for product results. Add a
collapsible stopgap before final product-card design:

- show a natural summary first
- hide raw JSON behind an expandable detail control
- keep builder diagnostics free to expose full raw payloads
- keep public chat free of operation IDs, paths, scores, trace IDs, and tool
  labels

### Query Continuity And Cart Follow-Up Bug

The runtime still needs conversation-grounded continuity for list -> select
product -> choose variant -> cart flows:

- use prior tool results as entity candidates
- resolve product title -> product ID -> variant/option
- orchestrate cart creation/add-item steps instead of asking for internal IDs
- suppress credential/header names from public clarifications
- ask natural missing details only, such as size, quantity, region, shipping, or
  confirmation
- keep the flow OpenAPI-driven and avoid Medusa-specific runtime logic

## Next Concrete Step

Start with validation, then move to runtime UX:

1. Re-run backend boundary suite and frontend type-check if the worktree has
   changed.
2. Run Docker browser E2E for the current RouteDeck boundary.
3. Add no-page-navigation/no-flicker browser coverage for auth and surface
   opening.
4. Fix public result rendering and query continuity.

## Anti-Drift Reminder

If future implementation reintroduces hardcoded Medusa routing, raw
legal-operation chips, direct unbound `saas_agent.open`, storage-backed app
state, stale adapter names, or public router internals, stop and return to the
RouteDeck/Corpus architecture before adding more features.
