# SaaStoAgent v0.1 Context

Last updated: 2026-07-10
Project: SaaStoAgent v0.1
Branch: `saastoagent`
Current boundary checkpoint: `189a6559 refactor(corpus): use RouteDeck contracts directly`
Status: Corpus remains the working feature baseline. RouteDeck extraction is
governed by ADR-003; the former full-framework refactor plan is retired.

## Start Here

1. [Critical prompt](./critical_prompt.md)
2. [ADR-003: RouteDeck Governs Agentic Interaction State](../routedeck/decisions/ADR-003-agentic-interaction-state-governor.md)
3. [Current context](./context.md)
4. [RouteDeck/Corpus historical vision](./architecture/route-deck-corpus-vision.md) for the historical ownership
   analysis, subject to ADR-003 where target language conflicts
5. [Architecture code map](./architecture/code-map.md)
6. [RouteDeck contract test index](./test_index/route-deck-contract.md)
7. [RouteDeck context](../routedeck/context.md)

Do not resume the
[retired full-stack refactor plan](../routedeck/docs/superpowers/plans/2026-07-10-routedeck-full-stack-framework-refactor.md).

## Pre-Implementation Review Gate

> **Temporary gate — remove this entire section when implementation begins.**
> The user must thoroughly review and approve
> [RouteDeck ADR-003](../routedeck/decisions/ADR-003-agentic-interaction-state-governor.md)
> before any RouteDeck or Corpus implementation starts. Until that review is
> complete, keep work in documentation/analysis only.

## Locked RouteDeck/Corpus Vision

Corpus is the SaaStoAgent product agent and the first behavioral reference for
RouteDeck.

RouteDeck is the reusable state-management and interaction-governance layer. It
owns the mechanics that keep an agent grounded: navgraph state, scoped context,
tool-call supervision, real-ID allowlists, guards and feedback, surface state,
navigation/deep links, tool-result observation, SSE interaction updates, and
read-only diagnostics.

Corpus owns SaaStoAgent domain records, product tools, tool execution, prompts,
model calls, product language, domain data, and surface components.

```text
Corpus supplies trusted product facts, guards, tools, and UI components
  -> RouteDeck builds scoped context and supervises every tool call
    -> Corpus/host agent runtime executes an allowed tool
      -> RouteDeck observes the result and updates interaction state,
         surfaces, events, and feedback
```

RouteDeck does not execute Corpus tools. It allows, blocks, requests input, or
requires review before the host runtime executes them.

## Corpus Feature Baseline

The first extraction must preserve the existing product behavior rather than
replace it with speculative framework infrastructure.

Baseline capabilities include:

- 26 interaction nodes and 40 operations spanning auth, SaaS Agent setup,
  connection/catalog activation, entities/actions, execution, approval,
  results, knowledge, memory, learning, QA, and recovery
- planning context limited to the current node, active surface, active SaaS
  Agent, visible selectable entities, surface options, and legal operations
- real IDs attached to visible entities and action arguments
- authentication, membership, selected-agent, connection/tool readiness, and
  pending-trace guards
- hidden internal route operations and safe clarification for illegal model
  output
- active, frame, peer, detail, form, and review surfaces
- dirty-form handling, surface selection, back/forward/cancel/recovery, and
  product-owned deep links
- review-gated execution, needs-input, tool-result evidence, and result review
- Corpus status, message delta, projection update, completion, error, and
  operation SSE behavior
- frontend projection/surface synchronization and public/internal redaction
- read-only introspection, blocked-action reasons, and guard explanations

Where current ownership is tangled, the behavior still counts as the oracle.

## Real Identifier Rule

The first extraction continues using real IDs. RouteDeck must validate that an
agent-supplied ID is currently visible and allowed for the selected tool and
session state. Fabricated, stale, hidden, or ineligible IDs are blocked with
structured feedback before the host tool runner sees them.

## Active Runtime Interfaces

- `GET /api/corpus/state`
- `POST /api/corpus/action`
- `GET /api/corpus/stream`
- `GET /api/diagnostics/stream`
- `/app/home`
- `/app/:nodeId`
- `/app/agents/:saasAgentId`
- `/app/agents/:saasAgentId/:nodeId`
- public deployed chat at `/a/{slug}`

Hidden route operations remain interaction plumbing and never appear as normal
product-agent tools or UI actions:

- `route.open_node`
- `route.switch_surface`
- `route.back`
- `route.forward`
- `route.cancel`

## Current Reality

The active backend Corpus package lives under `backend/corpus/`, but
`backend/corpus/graph/app.py` still combines product behavior with generic
context filtering, guard evaluation, projection/surface assembly, navigation,
diagnostics, agent planning, result observation, and SSE orchestration.

This is a boundary problem, not permission to redesign the behavior. The next
implementation must extract one working vertical capability at a time and keep
the active routes compatible.

## First Extraction Boundary

Included only when already demonstrated by Corpus:

- interaction/session state
- navgraph and guarded navigation
- scoped context and real-ID allowlisting
- before/after supervision for every application-semantic tool call
- legal/blocked/needs-input/review feedback
- surfaces, selections, deep links, recovery, diagnostics, and existing SSE
  behavior

Deferred:

- RouteDeck executing product tools
- opaque IDs
- required LangGraph/compiler work
- new SQLite/outbox/durable replay systems
- multiple framework modes or independent examples

Medusa is the later portability proof, not a prerequisite for the first Corpus
parity extraction.

## Validation Rule

The committed boundary checkpoint previously passed Python compilation, 32
dependency-free source-boundary checks, and the documented Mac mini runtime and
browser smoke. Those checks predate later abandoned RouteDeck WIP and are not a
fresh live baseline.

Before extracting code:

1. choose local, Mac mini LAN, or Mac mini Tailscale for runtime work
2. prove current Corpus state, action, stream, and representative browser flows
3. preserve that evidence as the baseline
4. after every slice, rerun the affected backend and browser behavior

Compilation or RouteDeck-only test counts do not prove Corpus parity.
