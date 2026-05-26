# ADR-013: RouteDeck And Corpus Boundary

Date: 2026-05-22
Status: Accepted
Implementation status: Boundary cleanup, hardcoding removal, internal-route
filtering, `surface_id` URL alignment, and chat-navigation remount regression
repair are implemented as of 2026-05-26. Public deployed-chat response shaping
still has known debt.

## Context

RouteDeck is reusable graph-backed state infrastructure for agentic UI. Corpus
is the SaaStoAgent product agent that consumes RouteDeck to drive the owner
builder experience.

The boundary exists because two failure modes are costly:

- RouteDeck absorbs SaaStoAgent-specific concepts and stops being reusable.
- Corpus or the product UI leaks framework operations directly to users, such
  as generic `Open node` / `Switch surface` controls, hidden ids, or endpoint
  paths.

The intended model is integration, not fusion.

## Decision

RouteDeck exposes validated app state and legal capabilities. Corpus interprets
normal chat against product-facing context. The graph/runtime validates and
commits typed operations.

```text
RouteDeck exposes.
Corpus decides.
Runtime validates and commits.
Product UI renders product language.
Diagnostics expose internals read-only.
```

## RouteDeck Responsibilities

RouteDeck owns:

- graph-backed runtime/store projection
- current node and active surface metadata
- operation metadata and readiness:
  `invocation_kind`, `can_dispatch_now`, `required_args`, `missing_args`,
  `accepted_arg_keys`
- surface contracts
- hidden/internal navigation operation primitives
- generic dispatch result contracts
- generic diagnostics/debugger primitives
- reusable React store and hooks

RouteDeck does not decide user intent and does not own SaaStoAgent product
behavior.

## Corpus Responsibilities

Corpus owns:

- user-facing conversation
- product-safe clarification and response wording
- interpreting normal chat against current planning context
- selecting product legal operations
- selecting product surface intents from `surface_options`
- binding visible entities such as SaaS Agent rows to typed operation payloads
- keeping SaaStoAgent-specific prompts, ids, surfaces, and copy outside reusable
  RouteDeck framework code

Corpus must not:

- mutate graph state directly
- infer hidden routes or hidden permissions
- use deterministic phrase routers or alias tables for normal chat
- ask for hidden internal ids when visible entities are projected
- expose internal operation ids, endpoint paths, trace ids, approval ids, or API
  auth details in public chat

## Two Navigation Lanes

Internal navigation lane:

- `route.open_node`
- `route.switch_surface`
- `route.back`
- `route.forward`
- `route.cancel`

These remain in RouteDeck/runtime for browser replay, history, diagnostics, and
validated runtime plumbing. They are `hidden` and must not appear as ordinary
product quick actions.

Corpus planning lane:

- product legal operations
- active surface summaries
- `surface_options`
- visible entities with bound operation args
- labels, descriptions, and accepted args

Corpus may choose a product operation or product surface intent. Runtime maps a
validated surface intent to internal route dispatch where needed.

## Product UI Rule

- direct operations may execute only when `can_dispatch_now=true`
- form operations open forms or review surfaces
- entity-selector operations bind a selected product entity before dispatch
- surface operations open product surfaces
- hidden operations are not rendered as generic product actions
- legal operations are not automatically quick-action chips

## Consequences

- Future RouteDeck changes must be reviewed for product-specific leakage.
- Future Corpus changes must not bypass RouteDeck readiness metadata.
- Clickable UI controls and chat-driven actions must converge on the same typed
  operation validation path.
- Browser URL replay is validated location replay, not product intent.
- Owner diagnostics may expose internals; deployed public chat cannot.
- Public chat result formatting must be tested separately from owner workbench
  planning because it has stricter safety requirements.

## Current Implementation State

Implemented:

- `/api/corpus/state` calls RouteDeck runtime snapshot.
- `/api/corpus/action` dispatches through RouteDeck runtime.
- `/api/corpus/stream` handles Corpus turn streaming and projection updates.
- `CorpusPlanningContext` is product-facing.
- Hidden/internal route operations are excluded from normal planning context.
- Blocked operations are not part of normal planning context.
- Product `surface_options` represent valid surface switches for Corpus.
- Visible entities can expose bound product operations such as `saas_agent.open`.
- Product quick actions filter hidden/internal route operations.
- The frontend uses one `/app/*` shell to avoid chat-navigation remounts.
- Frontend/backend URL handling standardizes on `surface_id`.
- Medusa remains an acceptance fixture, not product hardcoding.

Known debt:

- Public deployed chat can still ask over-technical clarifying questions in some
  natural product queries.
- Public chat must be hardened so it never asks visitors for connection-level
  API auth headers or internal ids.
- Compatibility endpoints/routes should continue to shrink as tests and callers
  move to the primary Corpus/RouteDeck boundary.

## Validation

Relevant validation commands:

```powershell
python -m pytest backend/tests/test_corpus_turn_planning.py backend/tests/test_corpus_graph_contract.py backend/tests/test_app_graph_contract.py -q
python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q
cd frontend
npm run type-check
npm run e2e:docker
npm run e2e:medusa:docker
```
