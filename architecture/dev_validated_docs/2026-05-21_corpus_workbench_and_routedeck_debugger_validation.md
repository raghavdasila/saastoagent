# Corpus Workbench And RouteDeck Debugger Validation

Date: 2026-05-21
Status: Validated against repo tests plus local browser evidence from this session

## Scope

This note captures the implementation-backed behavior for the current
SaaStoAgent workbench shell and the shared RouteDeck debugger pass.

It covers:

- single-shell Corpus workbench behavior
- auth/signup/login surface handling inside the workbench
- diagnostics docking and fullscreen behavior
- RouteDeck focus-graph edge de-overlap
- RouteDeck full-map topology after rejecting the sitemap pass

## Validated Product Behavior

### 1. Corpus remains the permanent interaction spine

- The main composer stays anchored at the bottom of the workbench.
- Active surfaces render inline below the conversation instead of replacing the
  shell.
- Auth no longer opens a second transcript/composer surface.

### 2. Diagnostics stays read-only and can expand fullscreen

- The docked diagnostics rail and fullscreen diagnostics view use the same
  shared RouteDeck debugger.
- Fullscreen diagnostics does not break the main chat composer.

### 3. Focus graph uses compact lane-separated routing

- Incoming and outgoing edges use distinct lanes.
- Opposite-direction pairs do not reuse the same path geometry.
- The layout stays compact and curved rather than switching to large orthogonal
  elbows.

### 4. Full map uses a root-centered hub topology

- `home` is the visual center when present.
- First-hop hubs sit on the primary ring.
- Deeper descendants expand outward within branch sectors.
- Detached components sit on outer spokes instead of pretending to belong to a
  false sitemap hierarchy.

## Canonical Files

- SaaStoAgent shell: `frontend/src/components/appGraph/AppGraphShell.tsx`
- Composer shell: `frontend/src/components/agent/CommandComposer.tsx`
- Shared debugger: `../routedeck/react/src/RouteDeckDebugger.tsx`
- Debugger routing helpers: `../routedeck/react/src/routeDeckDebuggerRouting.ts`
- Debugger topology helpers: `../routedeck/react/src/routeDeckDebuggerTopology.ts`
- Framework runtime doc: `../routedeck/docs/agentic-ui-state-runtime.md`

## Fresh Verification Commands

```powershell
python -m pytest backend/tests/test_app_graph_contract.py -q
cd ..\routedeck\react
npm test
cd ..\..\saastoagent-v0.1\frontend
npm run type-check
npx tsc -p tsconfig.json
npx vite build --outDir dist_verify
```

## Fresh Verification Results

- `python -m pytest backend/tests/test_app_graph_contract.py -q` -> 16 passed
- `npm test` in `../routedeck/react` -> 6 passed
- `npm run type-check` -> passed
- `npx tsc -p tsconfig.json && npx vite build --outDir dist_verify` -> passed

## Browser Evidence From This Session

- Signup/login stayed inside the main workbench shell.
- Diagnostics fullscreen remained functional while preserving the main chat
  experience.
- Focus graph rendered separate `auth_register <-> home` paths instead of one
  overlapping arc.
- Full map rendered the accepted radial hub copy and kept `29` painted edges as
  `29` unique routed paths.

## Accepted Architectural Conclusions

- The sitemap pass was the wrong model for this graph. The accepted full-map
  visualization is a root-centered radial hub map.
- RouteDeck debugger behavior belongs in shared framework code, while
  SaaStoAgent owns the shell composition and product presentation.
- The RouteDeck runtime-store model remains intact: graph truth, RouteDeck
  runtime/store, Corpus consumption, read-only diagnostics.

## Follow-Up

1. Add semantic branch labels and stronger capability grouping to the radial hub
   map.
2. Add repo-native browser coverage for auth surface opening and
   docked/fullscreen diagnostics.
3. Continue the `/api/app/graph/*` compatibility purge.
