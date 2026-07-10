# SaaStoAgent v0.1 Context

Last updated: 2026-07-10 08:51 IST
Project: SaaStoAgent v0.1
Branch: `saastoagent`
Current boundary checkpoint: `189a6559 refactor(corpus): use RouteDeck contracts directly`
Status: Backend identity/package cleanup is committed; the full RouteDeck
framework refactor is planned but not yet implemented.

## Start Here

1. `critical_prompt.md`
2. `context.md`
3. `context_checkpoints/context_checkpoint_10-07-2026-08-51AM.md`
4. `../routedeck/decisions/ADR-001-langgraph-native-routedeck.md`
5. `../routedeck/decisions/ADR-002-two-adoption-modes-one-kernel.md`
6. `../routedeck/docs/superpowers/plans/2026-07-10-routedeck-full-stack-framework-refactor.md`
7. `architecture/route-deck-corpus-vision.md`
8. `architecture/code-map.md`
9. `test_index/route-deck-contract.md`

## Locked Vision

Corpus is the SaaStoAgent application definition. It imports RouteDeck and
defines domain state, user-facing flows and interaction nodes, operations,
product guards, domain handlers, prompts/context, and surfaces.

RouteDeck implements that definition as the full-stack framework: application
validation/compilation, LangGraph execution integration, generic runtime and
interaction mechanics, review, projection, navigation, typed events, SSE
channel views, diagnostics, and React store/surface hosting.

LangGraph remains the execution substrate. Corpus must stay product-specific
and light; it must not become a second RouteDeck runtime.

```text
Corpus application definition and domain behavior
  -> RouteDeck Full Flow compiler/runtime
    -> LangGraph execution
      -> RouteDeck event, projection, diagnostics, and store pipeline
        -> Corpus product conversation and surfaces
```

## Current Committed State

The 2026-07-10 boundary checkpoint moved active backend Corpus code to:

```text
backend/corpus/
  graph/app.py
  graph/definitions.py
  schemas/graph.py
```

Completed in that checkpoint:

- retired `backend/services/corpus/`
- retired active Entry persistence models
- retired `backend/core/schemas/corpus.py` and Entry contract aliases
- updated `/api/corpus/*` routes to import the product-owned Corpus package
- changed compatibility RouteDeck catalogs to use RouteDeck action contracts
  directly
- updated backend boundary/structure tests for the active package

## Current Reality And Remaining Gap

The identity boundary is substantially cleaner, but the architecture is still
transitional:

- `backend/corpus/graph/app.py` is approximately 2,545 lines and still contains
  business handlers, context queries, guard/eligibility logic, surface registry,
  projection enrichment, diagnostics, LLM planning, event sequencing, and
  Corpus SSE orchestration.
- active Corpus execution does not yet run through the first-class RouteDeck
  LangGraph compiler target
- pass-through Corpus surface/navigation wrappers remain
- active frontend Corpus types still depend on some Entry-named contracts
- `ACTION_TARGETS`, manifest edges, capability rail, runtime eligibility, and
  frontend catalogs duplicate portions of interaction truth
- compatibility RouteDeck catalogs/endpoints still need explicit canonical,
  compatibility, or retired status

Do not split `app.py` merely for aesthetics. The next refactor must first move
generic compiler/runtime/event responsibilities into RouteDeck and prove them
through a real vertical flow.

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

Hidden route operations remain runtime plumbing and must not render as ordinary
product actions:

- `route.open_node`
- `route.switch_surface`
- `route.back`
- `route.forward`
- `route.cancel`

## Validation Snapshot

Fresh checkpoint validation on 2026-07-10:

- Python 3.12 `compileall`: passed for the moved Corpus package and changed
  backend files.
- Dependency-free source boundary checks: `32` passed (`29` runtime-structure,
  `3` surface-structure).
- `git diff --check` for the scoped refactor: passed.
- Prior Mac mini Tailscale smoke from the handoff: backend health, Corpus state,
  container compilation, Entry-boundary assertions, and browser
  register-to-create-agent flow passed.

Full dependency-backed pytest was not rerun locally because the bundled Python
does not contain the backend dependency set. Do not reinterpret compilation and
source-boundary checks as the full runtime suite.

The context/architecture closeout additionally passed both documentation
coverage scripts, all `13` dependency-free RouteDeck reference guards, a
relative-link check over `39` changed/new Markdown files with `0` missing, and a
scoped whitespace check. No services were started.

## Next Goal

Execute the RouteDeck full-stack framework refactor plan. The goal includes:

1. one shared RouteDeck application/interaction kernel
2. Full Flow compilation over LangGraph for ordinary/vibe developers
3. Core Integration for existing/custom agents through an executor adapter
4. one typed event architecture with assistant, runtime, tool, surface, and
   diagnostic channels plus robust SSE ordering/replay/terminal behavior
5. one backend-derived client contract for Corpus nodes, flows, operations,
   surfaces, affordances, and declared events
6. atomic dispatch claims plus a durable coordinated state/event/outbox backend
7. migration of generic runtime/projection/event mechanics out of Corpus
8. contract, integration, durability, SSE, React, and browser tests
9. `examples/full-flow-change-planner` and
   `examples/core-integration-document-review`, independent of Corpus

No fallback fixtures, synthetic product behavior, or fake success paths may be
introduced into product examples. Test fixtures remain isolated to tests.

## Runtime Location Rule

No services were started during this checkpoint. Before future runtime or
browser verification, ask whether to use local, Mac mini LAN, or Mac mini
Tailscale and report the exact command and smoke URL.

## Context Architecture Closeout

- Log: `logs/20260710_0851_corpus_routedeck_boundary_checkpoint.md`
- Checkpoint: `context_checkpoints/context_checkpoint_10-07-2026-08-51AM.md`
- Archived context:
  `context_history/20260710_context_before_routedeck_full_refactor_goal.md`
- Validated architecture note:
  `architecture/dev_validated_docs/2026-07-10_corpus_routedeck_contract_cleanup.md`

Unrelated research, evaluation, and playground work remains outside this
checkpoint and was intentionally not staged or committed with Corpus.
