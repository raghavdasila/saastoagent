# Corpus RouteDeck Contract Cleanup - Validated 2026-07-10

## Scope

This note records the implementation-backed boundary checkpoint committed as:

```text
189a6559 refactor(corpus): use RouteDeck contracts directly
```

The checkpoint is intentionally narrower than the planned full RouteDeck
framework refactor.

## Implemented Boundary

- Active Corpus backend code moved from `backend/services/corpus/` to the
  product-owned `backend/corpus/` package.
- Product graph definitions and surface declarations live in
  `backend/corpus/graph/definitions.py`.
- Runtime extension wiring, domain handlers, context queries, planning, and
  streaming currently live in `backend/corpus/graph/app.py`.
- Corpus schemas live in `backend/corpus/schemas/graph.py`.
- `/api/corpus/*` routes import the active product package.
- Entry persistence models and active backend Entry schema aliases were removed.
- Compatibility RouteDeck catalogs now use RouteDeck action contracts directly.

## Validation Evidence

Fresh checks before the commit:

```text
Python 3.12 compileall: passed
test_corpus_runtime_structure.py: 29 dependency-free source checks passed
test_corpus_surface_structure.py: 3 dependency-free source checks passed
git diff --check: passed
```

The prior Mac mini Tailscale smoke supplied in the session handoff also proved:

- backend health returned `{"status":"ok"}`
- `/api/corpus/state` returned the expected home/main state
- touched backend files compiled in the Python 3.13 container
- active Entry schema/model boundary assertions passed
- browser flow passed from registration through Corpus home and Create SaaS
  Agent review

## Explicit Limits

- Full dependency-backed pytest was not rerun locally; the bundled Python lacks
  the backend dependency set.
- No service or browser runtime was started during this checkpoint.
- The large Corpus app module still contains generic runtime, projection,
  guard, event, and SSE responsibilities that belong in the planned RouteDeck
  Full Flow framework.
- Frontend Entry-named contract cleanup is not part of commit `189a6559`.

## Next Architecture Step

Implement the RouteDeck full-stack framework plan with one shared interaction
kernel, Full Flow LangGraph compilation, Core Integration adapters, typed event
and SSE infrastructure, Corpus migration, and two standalone examples.
