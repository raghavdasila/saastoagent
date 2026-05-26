# RouteDeck + Corpus Vision

Date: 2026-05-26
Status: Canonical anti-drift vision for the current RouteDeck/Corpus boundary
Scope: SaaStoAgent v0.1 owner workbench, RouteDeck integration, Corpus planning,
and diagnostics

Framework anchors:

- `../../routedeck/docs/agentic-ui-state-runtime.md`
- `../../routedeck/docs/using-routedeck.md`

## Current Implementation Checkpoint

The current architecture is:

```text
Product graph/runtime owns truth, guards, and commits.
RouteDeck exposes validated state, surfaces, legal capabilities, and diagnostics.
Corpus interprets normal user chat against product-facing RouteDeck context.
React renders projected product surfaces and dispatches typed operations.
```

The active backend boundary:

- `GET /api/corpus/state` -> RouteDeck runtime snapshot
- `POST /api/corpus/action` -> RouteDeck runtime dispatch
- `GET /api/corpus/stream` -> Corpus turn streaming for user input, RouteDeck
  projection events for empty/state subscriptions
- `GET /api/diagnostics/stream` -> read-only RouteDeck introspection

The active frontend boundary:

- one `/app/*` shell owns the workbench mount
- RouteDeck store owns graph/runtime state and projection
- product UI renders surfaces and product controls from the projection
- local React/Zustand state may keep drafts, tabs, and display state only

## Core Rule

RouteDeck exposes what can happen. Corpus decides what the user means. The
runtime validates and commits.

Corpus must not patch graph state, infer hidden permissions, use backend phrase
tables, or ask users for internal ids when the current surface already exposes a
visible selectable entity.

RouteDeck must not absorb SaaStoAgent prompts, SaaS Agent domain behavior,
target API behavior, public chat copy, or Medusa-specific assumptions.

## Two Navigation Lanes

### Internal navigation lane

RouteDeck keeps generic navigation operations for runtime infrastructure:

- `route.open_node`
- `route.switch_surface`
- `route.back`
- `route.forward`
- `route.cancel`

These are hidden/internal operations. They support browser replay, history,
runtime plumbing, and diagnostics. They may exist in the rich projection for
framework/runtime clients, but they are not ordinary product actions and not
normal Corpus planning vocabulary.

### Corpus planning lane

Corpus receives product-facing planning context:

- current node and active surface summary
- active SaaS Agent summary
- active surfaces
- product `surface_options`
- visible selectable entities with bound typed operation args
- product legal operations
- labels, descriptions, accepted args, and readiness metadata

Corpus returns a typed product operation, a product surface intent, or a
clarification. Runtime can map a validated surface intent to an internal route
dispatch; the model does not need to emit `route.open_node` or
`route.switch_surface`.

## Ownership

### RouteDeck Owns

- product-neutral runtime state contract
- projection contracts
- legal operation metadata
- operation readiness metadata
- surface contracts
- navigation/runtime operation primitives
- diagnostics and introspection contracts
- reusable React store/hooks/debugger primitives

### RouteDeck Must Not Own

- SaaStoAgent prompts or product copy
- SaaS Agent database/domain behavior
- target API execution logic
- Medusa-specific behavior
- user account/auth semantics
- public deployed-chat response text
- raw LLM provider calls

### Corpus Owns

- SaaStoAgent product-agent behavior
- user-facing owner-workbench conversation
- product-safe clarification wording
- operation selection from product-facing legal operations
- product surface-intent selection
- binding visible entities to typed operations
- public/private safety posture for language

### Corpus Must Not Own

- graph truth
- invariant enforcement
- direct raw state mutation
- browser URL replay
- hidden route inference
- deterministic phrase routers or alias tables for normal chat

### Graph/Runtime Owns

- persistent application truth
- eligibility and guard enforcement
- permission and tenancy validation
- required args and schema checks
- pending review/approval gates
- node/surface legality
- commits, rejections, and recovery

### Product UI Owns

- product language
- visual layout
- forms and cards
- mapping projected surfaces to React components
- filtering hidden/internal operations from normal product controls
- safe public result presentation

## Surface Model

Surfaces are graph-declared and RouteDeck-projected. They are not arbitrary
local React panels that define workflow truth.

Use peer surfaces for alternate same-node views:

- Learning policy gaps
- failed executions
- active policies
- rejected candidates

Use child/detail nodes for committed nested work:

- one policy candidate review
- one execution trace review
- one active policy review

Surface choices are sticky presentation state until transition, user request, or
component event. They are validated by runtime and represented in browser URLs
with `surface_id`.

## Diagnostics

Diagnostics are read-only and can expose internals:

- graph topology
- current node and surface
- legal operations
- blocked operations and reasons
- guard explanations
- route trace
- projection version
- runtime snapshot

Diagnostics must stay separate from public deployed chat. Public chat cannot
expose operation ids, endpoint paths, trace ids, approval ids, hidden route op
names, auth headers, or raw tool labels.

## Dos

- Do treat the graph/runtime as the source of truth.
- Do let Corpus control product intent through typed legal operations.
- Do expose visible selectable entities when the surface shows selectable rows.
- Do use `surface_options` for product-facing surface switches.
- Do validate every selected operation before commit.
- Do filter hidden/internal route ops from normal product actions.
- Do keep RouteDeck framework code product-neutral.
- Do preserve diagnostics as read-only.

## Don'ts

- Do not render every legal operation as a quick action.
- Do not expose `Open node` or `Switch surface` in normal product UI.
- Do not reintroduce backend phrase tables or alias routers.
- Do not treat browser URL replay as product intent.
- Do not let Corpus directly mutate graph state.
- Do not ask visitors for connection-level API auth headers or internal ids.
- Do not document Medusa fixture behavior as product hardcoding.
- Do not continue implementation that conflicts with this vision without
  updating this document and ADR-013 together.
