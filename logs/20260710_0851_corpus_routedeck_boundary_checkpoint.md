# 2026-07-10 08:51 IST - Corpus RouteDeck Boundary Checkpoint

## Summary

Committed the existing Corpus/RouteDeck backend boundary cleanup, then updated
the context architecture for the next full framework refactor.

Commit:

```text
189a6559 refactor(corpus): use RouteDeck contracts directly
```

## Accomplished

- Moved active backend Corpus code into `backend/corpus/`.
- Removed the active Entry persistence and backend contract alias layer.
- Updated Corpus routes and compatibility catalogs to import RouteDeck contracts
  directly.
- Updated boundary/structure tests for the new package.
- Locked Corpus as a lightweight application definition and RouteDeck as the
  LangGraph-native full-stack compiler/runtime.
- Locked one shared RouteDeck event architecture with separate assistant,
  runtime, tool, surface, and diagnostic channels.
- Locked two RouteDeck developer modes over one kernel: Full Flow and Core
  Integration.
- Required standalone examples for both modes independent of Corpus.
- Required a backend-derived frontend contract and durable transactional
  session/event/outbox backend so Corpus does not recreate either concern.

## Files And Architecture Owners

The committed source files belong to the `Corpus application definition and
RouteDeck boundary`, `Backend core`, and `Test and validation harness` rows in
`architecture/code-map.md`.

Context/architecture updates include:

- `critical_prompt.md`
- `context.md` and archived context
- `architecture/code-map.md`
- `architecture/route-deck-corpus-vision.md`
- `architecture/components/routedeck-corpus-boundary.md`
- `architecture/changelog.md`
- `architecture/dev_validated_docs/`
- `test_index/route-deck-contract.md`

## Validation

- Python 3.12 `compileall`: passed for moved/changed backend files.
- Dependency-free source-boundary tests: `32` passed.
- Scoped `git diff --check`: passed.
- Prior Mac mini Tailscale backend/browser smoke from the handoff: passed.

Full dependency-backed pytest was not rerun locally because the available
bundled Python lacks the backend dependency set.

Context/architecture closeout evidence:

- RouteDeck and SaaStoAgent documentation coverage scripts exited `0`.
- `13` dependency-free RouteDeck reference guards passed.
- `39` changed/new Markdown files had `0` missing relative links.
- Scoped `git diff --check` passed with line-ending notices only.

## Issues And Boundaries

- `backend/corpus/graph/app.py` remains a transitional 2,545-line module.
- Active Corpus does not yet execute through the target RouteDeck LangGraph
  compiler.
- Frontend Entry aliases and duplicate interaction catalogs remain.
- Unrelated research/evaluation/playground changes were intentionally left
  unstaged and uncommitted.

## Next Steps

Execute the RouteDeck full-stack framework refactor plan with tests and two
standalone examples. Do not start services until the user selects local, Mac
mini LAN, or Mac mini Tailscale.
