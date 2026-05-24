# RouteDeck Runtime Store Reset Plan

Status: Boundary cleanup implemented; browser E2E rerun pending
Date: 2026-05-24

Canonical framework doc: `../../routedeck/docs/agentic-ui-state-runtime.md`
Canonical product vision doc: `../architecture/route-deck-corpus-vision.md`

## Summary

RouteDeck is now treated as graph-backed state management for agentic UI, not as
a passive projection/debugger package. SaaStoAgent consumes RouteDeck through
`CorpusRouteDeckRuntime` and `RouteDeckStore`; Corpus remains the central
SaaStoAgent product agent.

Core rule:

```text
Graph owns truth.
RouteDeck owns the generic runtime/store over that graph.
Corpus consumes RouteDeck state and chooses legal operations.
React renders Corpus plus RouteDeck-projected contextual surfaces.
```

## Implemented This Session

- Added RouteDeck runtime/store contracts in `routedeck_core`.
- Added `RouteDeckStore`, store-backed provider support, dispatch/status/inspect hooks, and a generic HTTP/SSE store factory in `@routedeck/react`.
- Added `CorpusRouteDeckRuntime` around `CorpusGraphRuntime`.
- Rewired SaaStoAgent frontend to mount a configured RouteDeck store rather than hand-juggling projection state in the shell.
- Kept Corpus text/proposal streaming separate from RouteDeck projection/state streaming.
- Added split endpoints for Corpus, RouteDeck projection/stream, and diagnostics.
- Removed product-path dependence on raw eligible actions as default UI chips.
- Added richer RouteDeck diagnostics with a compact lane-separated focus graph
  and a root-centered navgraph full map.
- Changed the navigation graph manifest to semantic route topology instead of drawing every action as an edge.
- Fixed transition jitter by keeping the store/shell stable and replacing browser history without remounting the page.
- Added regression tests for RouteDeck runtime contracts, store behavior, adapter behavior, Corpus behavior, and semantic manifest edges.
- Carried the product shell into a single Corpus workbench with anchored
  composer, inline auth/active surfaces, fullscreen diagnostics, and updated
  debugger theming.
- Routed `/api/corpus/state` through `route_deck_runtime.snapshot(...)`.
- Routed `/api/corpus/action` through `route_deck_runtime.dispatch(...)`.
- Kept Corpus natural-language turn streaming on `CorpusGraphRuntime`, while
  RouteDeck projection subscriptions use RouteDeck stream events.
- Removed stale `SaaStoAgentRouteDeckAdapter` and `routedeck_adapter.py`.
- Reworked the frontend state boundary so RouteDeck owns agentic app state and
  `saasAgentUiStore` owns only local UI state.

## Current Runtime Shape

```text
CorpusGraphRuntime
  -> CorpusRouteDeckRuntime
    -> generic RouteDeckRuntime
      -> RouteDeckStore
        -> AppGraphShell
          -> Corpus chat
          -> frame/active surfaces
          -> read-only diagnostics
```

Primary product endpoints:

- `GET /api/corpus/state`
- `GET /api/corpus/stream`
- `POST /api/corpus/action`
- `GET /api/routedeck/projection`
- `GET /api/routedeck/stream`
- `GET /api/diagnostics/stream`

Legacy `/api/app/graph/*` endpoints are compatibility debt only and should not be used as the product UI contract.

## Diagnostics Contract

Diagnostics must make invisible failures visible without becoming the product UI.

It should expose:

- current node
- all navigation nodes
- semantic navigation route edges
- reachable nodes
- legal operations
- blocked operations and guard reasons
- route traces and why-not-reachable explanations
- surfaces and presentation state
- runtime events

The diagnostics navigation graph must not draw actions as graph edges. Actions appear only when inspecting a node or operation details.

## Next Work

1. Rerun Docker browser E2E after the RouteDeck boundary cleanup:
   - `npm run e2e:docker`
   - `npm run e2e:medusa:docker` when the Medusa target is available
2. Add no-page-navigation/no-flicker browser tests for auth and active surface
   opening.
3. Add direct tests for `RouteDeckStore.connectStream()` against projection update events.
4. Add focused browser tests for diagnostics and inline surfaces:
   - Focus map opens on current node with non-overlapping edge geometry.
   - Full map shows the navgraph topology around the root node.
   - Actions are absent from the canvas and present only in selected-node
     details.
   - Auth and inline surfaces stay inside the main Corpus shell.
5. Add LLM meta-tool adapters backed by the same introspection service as diagnostics.
6. Tighten surface role tests:
   - `frame` renders around Corpus.
   - `active` appears only after initiation, accepted proposal, or graph-required recovery.
   - `diagnostic` remains hidden/read-only.
7. Continue product-literal guard tests for RouteDeck framework source.
8. Continue purging product use of compatibility `/api/app/graph/*` routes where
   tests and unrelated callers no longer require them.

## Anti-Drift Checks

- RouteDeck framework code stays product-neutral.
- Corpus is a consumer of RouteDeck state, not the hidden owner of RouteDeck state management.
- Zustand is UI-local only and must not become the graph/app source of truth.
- Legal operations are runtime/agent context, not raw product UI.
- Graph commits state; LLMs choose typed operations.
- Diagnostics is read-only and richer than JSON.
- Navigation maps show navigation topology only.
- Focus maps use lane-separated routing; full maps use root-centered navgraph
  topology, not sitemap assumptions.
- Presentation state is ephemeral.
