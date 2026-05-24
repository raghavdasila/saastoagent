# Context Checkpoint - 24-05-2026 10:32AM IST

## Session Result

RouteDeck/Corpus boundary cleanup is implemented for the active backend and
frontend state-management path.

The architectural target is now explicit in code and tests:

```text
LangGraph/backend services
  -> CorpusGraphRuntime
    -> CorpusRouteDeckRuntime
      -> RouteDeck runtime state/projection/dispatch contract
        -> RouteDeckStore / @routedeck/react
          -> Corpus workbench React surfaces
```

Corpus remains the SaaStoAgent product layer. RouteDeck is the reusable
agentic-app state layer. Zustand remains UI-local state only.

## Backend State

- `/api/corpus/state` calls `route_deck_runtime.snapshot(...)`.
- `/api/corpus/action` calls `route_deck_runtime.dispatch(...)`.
- `/api/corpus/stream` uses RouteDeck projection streaming when no natural
  language input is present.
- Natural-language turn streaming still uses `CorpusGraphRuntime`.
- `/api/diagnostics/stream` still reads from RouteDeck snapshot/inspect.
- Route-local conversion helpers preserve graph state, projection,
  `replace_path`, active surface, messages, and projection version.
- `SaaStoAgentRouteDeckAdapter` and `routedeck_adapter.py` are removed.

## Frontend State

- `AppGraphShell` reads active SaaSAgent identity from RouteDeck state.
- `saasAgentUiStore` replaces `saasAgentStore` and only owns UI concerns:
  active tab, drafts, local selections, and mirrored active id.
- Product API calls that need SaaSAgent context use
  `api.withSaaSAgent(saasAgentId)`.
- `storage.getSaaSAgentId()` is no longer used as an implicit request context.
- RouteDeck ids and Corpus surface component names are centralized in
  `corpusRouteDeckCatalog.ts`.

## Verification

- Backend focused suite:
  `python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q`
  - Result: `65 passed`
- Frontend:
  `npm run type-check`
  - Result: passed
- Source scan:
  - no backend `SaaStoAgentRouteDeckAdapter`
  - no backend `routedeck_adapter`
  - no old adapter contract test file

## Known Remaining Problems

1. Docker browser E2E was not rerun after this boundary cleanup.
2. Surface/auth transition flicker still needs browser-level regression
   coverage.
3. Public deployed chat still needs collapsible/raw JSON result handling.
4. Query continuity still needs runtime work for product list -> product
   selection -> variant -> cart flows.
5. Compatibility `/api/app/graph/*` routes still exist and should not be used
   as the product UI contract.

## Resume Prompt

Start by verifying the current worktree and then run browser-level validation
for the RouteDeck state boundary:

1. `git status --short`
2. `python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q`
3. `cd frontend && npm run type-check`
4. `cd frontend && npm run e2e:docker`
5. `cd frontend && npm run e2e:medusa:docker` if the Medusa target is
   available

After validation, the next implementation target should be query/result
continuity, not another naming-only pass.
