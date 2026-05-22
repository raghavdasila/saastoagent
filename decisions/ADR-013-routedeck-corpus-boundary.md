# ADR-013: RouteDeck And Corpus Boundary

Date: 2026-05-22
Status: Accepted
Implementation status: Partially implemented, boundary cleanup required

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

Corpus responsibilities:

- user-facing conversation and proposal wording
- SaaSAgent list/search/card rendering
- SaaStoAgent setup surfaces, connection UX, and recovery messages
- deployed-chat product copy and public-safe result presentation
- decision on how an operation should appear to a user
- binding product entities such as `saas_agent_id` before dispatch

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

## Current Implementation Gap

The behavior is partially aligned:

- `saas_agent.list` exists as a selector-style surface operation.
- `saas_agent.open` requires a bound `saas_agent_id`.
- recent agent cards bind `saas_agent_id` before dispatch.
- RouteDeck operation readiness metadata exists.

But the implementation remains too intertwined between Corpus/app graph shell
code and RouteDeck usage. The next session should split framework helpers and
Corpus-specific surface/rendering code before deepening feature modules.

## Validation

Validated indirectly through the horizontal E2E path and the incomplete-agent
recovery work. A dedicated boundary refactor and tests are still pending.
