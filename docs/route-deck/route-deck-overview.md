# RouteDeck Overview

RouteDeck is the graph-backed state runtime that SaaStoAgent uses to make an
agentic UI safe, inspectable, and testable.

In SaaStoAgent v0.1, RouteDeck does not decide product intent and it is not the
chatbot. Corpus is the SaaStoAgent product agent. The graph/runtime is the final
authority. RouteDeck sits between them and exposes what is currently true and
what is currently legal.

```text
Product graph/runtime
  -> RouteDeck runtime state and projection
    -> Corpus planning context, React store, diagnostics
      -> user or agent chooses a typed operation
        -> runtime validates and commits/rejects/reviews
```

## Why RouteDeck Exists

Agentic product UIs have a specific state problem:

- the user can talk naturally
- the user can click controls
- the browser can replay URLs and history
- the graph has guards, permissions, required arguments, review gates, and
  surface constraints
- diagnostics must explain what is possible without becoming the product UI

RouteDeck solves that by projecting graph-owned state into a single contract:

- current node and current surface
- legal operations and readiness metadata
- blocked operations for diagnostics
- active surfaces and surface options
- navigation state and browser location
- diagnostics and introspection data

The important rule is that a legal operation is not automatically a product
button. A legal operation can be direct, form-backed, selector-backed,
surface-opening, review-required, blocked, or hidden/internal.

## SaaStoAgent Integration

The active SaaStoAgent integration lives under:

- backend graph/runtime: `backend/services/app_graph/`
- Corpus routes: `backend/routes/corpus_graph.py`
- frontend shell: `frontend/src/components/appGraph/AppGraphShell.tsx`
- RouteDeck client helpers:
  `frontend/src/components/appGraph/corpusRouteDeckClient.ts`
- product quick-action filtering:
  `frontend/src/components/appGraph/corpusOperations.tsx`

Primary endpoints:

- `GET /api/corpus/state`
- `POST /api/corpus/action`
- `GET /api/corpus/stream`
- `GET /api/diagnostics/stream`

Compatibility app-graph endpoints may still exist for older tests or callers,
but new product UI work should target the Corpus/RouteDeck boundary above.

## RouteDeck vs Corpus vs Graph

RouteDeck owns framework-neutral state and capability projection:

- operation contracts
- surface contracts
- runtime state shape
- route/navigation runtime primitives
- diagnostics and introspection contracts
- React store and hooks in the sibling `@routedeck/react` package

Corpus owns SaaStoAgent product behavior:

- user-facing conversation
- product-specific prompts and response style
- interpretation of normal chat against the current planning context
- product-safe clarifications
- product surface descriptions
- binding visible product entities to typed operations

The graph/runtime owns authority:

- persistent state
- eligibility checks
- permissions and tenancy checks
- required argument validation
- surface/node legality
- review and approval gates
- commits, rejection, recovery, and browser replay validation

## Two Navigation Lanes

SaaStoAgent uses two navigation lanes. Keeping them separate prevents the
framework from leaking into product chat.

### Internal navigation lane

Internal route operations exist for runtime plumbing, browser URLs, history, and
diagnostics:

- `route.open_node`
- `route.switch_surface`
- `route.back`
- `route.forward`
- `route.cancel`

These operations are hidden. Normal product quick actions should not render them
as generic buttons, and normal Corpus planning context should not ask the model
to emit them directly.

Runtime code may still dispatch these after validating a browser replay or after
mapping a product-facing surface intent to a concrete route operation.

### Corpus planning lane

Corpus sees product-facing context:

- current node and surface summary
- active SaaS Agent summary
- active surfaces and valid `surface_options`
- visible selectable entities with bound typed operation payloads
- product legal operations
- labels, descriptions, accepted args, and readiness metadata

Corpus should choose one product operation, choose a valid product surface
intent, or ask a product-safe clarification. It must not infer hidden routes,
hidden permissions, internal ids, endpoint paths, or auth headers.

## Operations

RouteDeck operation metadata should answer two questions:

1. Is this operation legal from the current graph state?
2. How should a product client interact with it?

Important fields:

- `id`
- `label`
- `description`
- `category`
- `input_schema`
- `invocation_kind`
- `can_dispatch_now`
- `required_args`
- `missing_args`
- `accepted_arg_keys`
- `safety_class`
- `execution_mode`
- `target_node`

Common invocation kinds:

- `direct` - one-click dispatch is allowed when `can_dispatch_now=true`
- `form` - open/fill a form or review surface before dispatch
- `entity_selector` - select or bind a visible entity first
- `surface` - open a product surface
- `hidden` - runtime/diagnostic-only; do not render as normal product UI

## Surfaces

Surfaces are graph-projected UI regions. They let the runtime declare what can
be shown without making React local state the source of graph truth.

Roles:

- `frame` - stable context around the active work
- `active` - current work surface
- `diagnostic` - read-only debugging/inspection

Kinds:

- `peer` - alternate same-node view, such as Learning policy gaps vs rejected
- `detail` - nested/review view, such as one execution trace review
- `embedded` - supporting inline surface

Corpus can choose among valid product surface options. The runtime maps that
choice to validated internal route dispatch.

## Browser URLs And Replay

Browser URLs are location replay, not product intent.

Current primary routes:

- `/app/home`
- `/app/:nodeId`
- `/app/agents/:saasAgentId`
- `/app/agents/:saasAgentId/:nodeId`

The standard active surface query key is `surface_id`.

Direct URL loads and browser back/forward must be validated by the backend
against the current graph state. Unknown node/surface combinations, injected
review surfaces, and invalid active-agent combinations should be rejected or
recovered according to runtime policy rather than treated as normal user
intent.

## Diagnostics

Diagnostics may expose RouteDeck internals. Public product chat must not.

Diagnostics should show:

- current graph node and surface
- legal operations
- blocked operations and reasons
- route trace
- active surfaces
- selected-node details
- runtime snapshot and projection version
- graph reachability and guard explanations

Diagnostics should not make action ids look like topology. Route edges belong
to graph navigation; actions belong in selected-node operation details.

## Public Chat Safety

Public deployed chat is not a diagnostics surface. It must not expose:

- operation ids
- endpoint paths
- trace ids
- approval ids
- cart ids
- raw API auth headers
- internal slot names
- raw graph state
- hidden route operation names

Visitors can be asked for natural missing details such as size, color, email,
address, region, shipping choice, or confirmation. They should not be asked for
connection-level API keys or generated tool internals.

## Anti-Patterns

Avoid:

- rendering every `legal_operation` as a quick action
- showing `Open node` or `Switch surface` as normal product chips
- adding backend phrase tables or alias routers for normal chat
- letting React local state become graph truth
- letting Corpus patch graph state directly
- calling product side-effect APIs directly when a graph operation exists
- exposing RouteDeck terms in public deployed chat
- treating browser URL replay as normal product intent
- documenting Medusa fixture behavior as product hardcoding

## Related Docs

- `../../../routedeck/docs/route-deck-whitepaper.md`
- `../../architecture/route-deck-corpus-vision.md`
- `../../decisions/ADR-013-routedeck-corpus-boundary.md`
- `../../SYSTEM_FLOW_INDEX.md`
- `../../../routedeck/docs/using-routedeck.md`
- `../../../routedeck/docs/agentic-ui-state-runtime.md`
