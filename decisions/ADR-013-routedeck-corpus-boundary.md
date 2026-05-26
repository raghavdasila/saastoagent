# ADR-013: RouteDeck And Corpus Boundary

Date: 2026-05-22
Status: Accepted
Implementation status: Backend/frontend boundary cleanup implemented on
2026-05-24; RouteDeck v2 and graph-owned Learning/instructions boundary
hardening implemented on 2026-05-25; browser E2E rerun pending

## Context

RouteDeck is intended to be reusable agentic UI state infrastructure. Corpus is
the SaaStoAgent product agent that consumes RouteDeck to drive the builder
experience.

Recent implementation made the product flow work, but code inspection exposed
that RouteDeck and Corpus are still too tightly coupled. This creates two
architecture risks:

- RouteDeck may absorb SaaStoAgent/Corpus-specific concepts and stop being a
  reusable framework layer.
- Corpus may dispatch framework operations directly without enough product
  treatment, causing UX failures such as unbound entity actions or raw
  legal-operation chips.

The intended model is integration, not fusion: Corpus should use RouteDeck, but
RouteDeck should not become Corpus.

## Decision

RouteDeck owns framework-neutral state and operation metadata. Corpus owns
SaaStoAgent-specific presentation, conversation, and product recovery.

RouteDeck responsibilities:

- graph-backed runtime/store projection
- current node, valid operations, evidence, and diagnostics metadata
- operation readiness metadata:
  `invocation_kind`, `can_dispatch_now`, `required_args`, `missing_args`
- generic dispatch legality checks
- generic diagnostics/debugger primitives
- generic surface contracts where they are reusable across products
- React-facing state/store/hooks for RouteDeck-projected app state

Decision authority:

- RouteDeck exposes the current graph-aware possibility space to the product
  agent: current node, legal operations, operation params/args metadata,
  readiness, active surfaces, guards, and diagnostics context.
- Corpus is the product agent that interprets the user turn against that
  current RouteDeck-projected context and decides what to do next.
- Corpus must choose one typed legal operation, fill allowed args, or ask a
  clarification. It must not invent hidden routes or patch graph state
  directly.
- RouteDeck does not decide intent. The graph runtime validates the selected
  operation and then commits, rejects, or asks for review.

Corpus responsibilities:

- user-facing conversation and proposal wording
- SaaSAgent list/search/card rendering
- SaaStoAgent setup surfaces, connection UX, and recovery messages
- deployed-chat product copy and public-safe result presentation
- decision on how an operation should appear to a user
- binding product entities such as `saas_agent_id` before dispatch
- keeping SaaStoAgent-specific RouteDeck ids, surfaces, and copy in
  Corpus-owned files

Frontend local state responsibilities:

- Zustand may keep UI-only state such as tabs, drafts, local selections, and a
  mirrored active SaaSAgent id.
- Zustand must not become the source of graph truth, active RouteDeck state,
  legal operations, active surfaces, or dispatch readiness.

The UI rule is:

- direct operations may execute only when `can_dispatch_now=true`
- form operations open forms/proposals
- entity-selector operations open or use a selector surface
- surface operations navigate/open the relevant surface
- hidden operations are not rendered as generic product UI

## Consequences

- Future RouteDeck changes must be reviewed for product-specific leakage.
- Future Corpus changes must not bypass RouteDeck readiness metadata for
  one-click dispatch.
- The generic `Open SaaSAgent` path must remain a selector/list flow unless an
  agent ID is already bound.
- A larger-agent-count workflow should use `saas_agent.list` and search/list
  surfaces instead of pushing all agents into conversation context.
- Builder diagnostics can expose RouteDeck internals, but deployed chat cannot.

## Current Implementation State

The behavior is now aligned for the active boundary:

- `saas_agent.list` exists as a selector-style surface operation.
- `saas_agent.open` requires a bound `saas_agent_id`.
- recent agent cards bind `saas_agent_id` before dispatch.
- RouteDeck operation readiness metadata exists.
- `/api/corpus/state` calls `route_deck_runtime.snapshot(...)`.
- `/api/corpus/action` calls `route_deck_runtime.dispatch(...)`.
- raw public `/api/routedeck/*` product routes are removed.
- `CorpusRouteDeckRuntime` is the only product-side RouteDeck runtime name.
- `SaaStoAgentRouteDeckAdapter` and `routedeck_adapter.py` have been removed.
- `AppGraphShell` derives active SaaSAgent identity from RouteDeck state.
- `saasAgentUiStore` is named and tested as UI state, not RouteDeck state.
- Learning approve/reject dispatch through AppGraph/RouteDeck operations.
- Instructions save dispatches through `instructions.save`.
- Product UI uses workflow/surface language instead of RouteDeck-node language.
- RouteDeck diagnostics no longer label navgraph edges with action ids.

Remaining implementation concerns are runtime UX and coverage rather than the
basic boundary name/path:

- Docker browser E2E needs to be rerun after the cleanup.
- No-page-navigation/no-flicker behavior for auth and active surface opening
  needs browser regression coverage.
- Public result rendering and query continuity remain open runtime/product
  issues.

## Validation

Dedicated boundary validation added on 2026-05-24:

- `python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q`
  - Result: `65 passed`
- `npm run type-check` from `frontend`
  - Result: passed
- Backend source scan confirmed no `SaaStoAgentRouteDeckAdapter`,
  `routedeck_adapter`, or old adapter contract test references.
