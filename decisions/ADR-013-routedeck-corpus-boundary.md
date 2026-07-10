# ADR-013: RouteDeck And Corpus Boundary

Date: 2026-05-22
Amended: 2026-07-10
Status: Accepted
Implementation status: The direct-contract/package cleanup is committed in
`189a6559`; the Full Flow compiler/runtime migration is planned and not yet
implemented.

## Context

Corpus is the SaaStoAgent product agent and application definition. RouteDeck is
the reusable full-stack framework that will compile and run that definition over
LangGraph while supplying state and interaction management, guards, review,
projections, surfaces, typed events/SSE, diagnostics, and React state.

The boundary prevents two costly failures:

- RouteDeck absorbs SaaStoAgent-specific concepts and stops being reusable.
- Corpus reimplements generic framework mechanics and becomes a second
  RouteDeck runtime.

The intended model is consumption, not fusion or wrapper rebranding.

## Decision

```text
Corpus declares product behavior and product meaning.
RouteDeck validates, compiles, coordinates, and projects it.
LangGraph executes the first-class backend flow.
Product UI renders Corpus language and surface components.
Diagnostics expose sanitized internals read-only.
```

The RouteDeck application specification is the single public interaction source
of truth for Corpus nodes, flows/outcomes, operations, surface identity and
placement, affordances, and declared events. Corpus context/surface providers
resolve live domain facts and props; they do not repeat the contract in parallel
catalogs.

## RouteDeck Responsibilities

RouteDeck owns product-neutral:

- application validation and Full Flow compilation over LangGraph
- server-authoritative session state, projection versions, dispatch claims, and
  idempotency
- operation/input validation, guard and review lifecycle, and recovery
- declared flow outcome validation, navigation, projection, and surface hosting
- typed event payloads, channels, visibility, sequencing, persistence, replay,
  and SSE framing
- FastAPI transport factories and the React store/event/surface runtime
- diagnostics/debugger primitives and two-mode conformance tests

RouteDeck does not own SaaStoAgent prompts, domain data, auth policy, business
side effects, provider calls, product copy, or React product components.

## Corpus Responsibilities

Corpus owns:

- Corpus-specific state fields and domain models
- user-facing flows, operations, product guards, and declared surfaces
- prompts, model choices, conversation meaning, clarification, and response copy
- context queries, tenancy/auth facts, domain handlers, database work, and
  external side effects
- dynamic surface props and product React components
- product-safe entity binding and redaction

Corpus must not:

- subclass generic RouteDeck runtime behavior after Full Flow migration
- assemble generic projections, navigation stacks, reviews, or diagnostics
- allocate event sequence numbers, own generic subscriber queues, or format SSE
- accept client graph state as authoritative
- re-export RouteDeck primitives under Corpus or Entry names
- duplicate nodes, targets, operations, or surface identity in backend/frontend
  catalogs
- expose internal route operations, ids, traces, credentials, or auth details in
  public chat

## Navigation And Product Interaction

Internal operations such as `route.open_node`, `route.switch_surface`,
`route.back`, `route.forward`, and `route.cancel` remain hidden runtime plumbing.
They may support replay/diagnostics but are not ordinary product quick actions.

Surface clicks and chat-selected capabilities converge on the same typed
RouteDeck dispatch boundary. Direct operations execute only when currently
legal; form/review/entity selection behavior is derived from the current
projection and validated by the server-authoritative runtime.

## Event Boundary

Corpus owns assistant meaning, prompts, and product-safe payload content.
RouteDeck owns the common `assistant`, `runtime`, `tool`, `surface`, and
`diagnostic` event architecture, including schema validation, correlation,
ordering, visibility, persistence, replay, and SSE transport. Filtered streams
must not leak diagnostics or private graph state into public assistant clients.

## Current Transitional State

Implemented in `189a6559`:

- active backend Corpus code lives under `backend/corpus/`
- active Entry persistence/contracts and `backend/services/corpus/` are retired
- active Corpus backend imports RouteDeck contracts directly
- `/api/corpus/*` routes use the product-owned Corpus package
- source-boundary tests protect the direct-contract package shape

Remaining:

- `backend/corpus/graph/app.py` still owns generic runtime, projection, event,
  SSE, diagnostics, and planning orchestration
- pass-through Corpus surface/navigation wrappers and frontend Entry aliases
  remain
- duplicate `ACTION_TARGETS`/flow/catalog truth remains
- active execution does not yet use the target RouteDeck Full Flow compiler

The migration must move one real vertical operation through RouteDeck at a time
and delete compatibility paths only after call-site and regression proof. A file
split is not success unless framework mechanics actually leave Corpus.

## Consequences

- RouteDeck must be proven independently through Full Flow and Core Integration
  standalone examples; Corpus is not the only framework example.
- Corpus keeps product behavior but becomes much lighter.
- Missing real models, stores, APIs, or invariants fail loudly. Product paths do
  not substitute fixtures, canned output, or heuristic success.
- Runtime/browser verification must use the user-selected location: local, Mac
  mini LAN, or Mac mini Tailscale.

## Validation

Current commands and evidence are maintained in
`../test_index/route-deck-contract.md`. The full target matrix is maintained in
`../../routedeck/docs/superpowers/plans/2026-07-10-routedeck-full-stack-framework-refactor.md`.
