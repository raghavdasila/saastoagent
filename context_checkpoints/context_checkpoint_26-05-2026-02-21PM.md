# Context Checkpoint - 26 May 2026 02:21 PM IST

## Current State

This checkpoint supersedes `context_checkpoint_26-05-2026-08-56AM.md` for
documentation and restart purposes.

The runtime behavior was not changed in this pass. The work refreshed the stale
project README, RouteDeck guide set, context handoff, ADR, vision doc, flow
index, and sibling RouteDeck usage guide to match the current RouteDeck/Corpus
boundary.

## Current Architecture Summary

```text
RouteDeck exposes validated app state and legal capabilities.
Corpus interprets normal chat against product-facing context.
The graph/runtime validates and commits typed operations.
React renders projected product surfaces.
```

Internal route operations remain available for runtime/browser/history replay
and diagnostics:

- `route.open_node`
- `route.switch_surface`
- `route.back`
- `route.forward`
- `route.cancel`

They are hidden from normal Corpus planning and product quick actions.

## Current Setup Summary

- frontend: `http://localhost:3007`
- backend health: `http://localhost:8085/api/health`
- Medusa target backend/admin: `http://localhost:9000`
- Medusa storefront: `http://localhost:8000`
- primary owner shell: `/app/*`
- deployed public chat: `/a/{slug}`
- standard active surface query key: `surface_id`

## Verified Runtime Context From This Thread

Recent runtime work before this docs pass verified:

- hidden/internal route ops are filtered from normal product quick actions
- chat navigation does not refresh/remount the whole shell
- frontend/backend surface query handling uses `surface_id`
- the Medusa fixture agent `Live Commerce Raghav 1779776944731` is connected,
  activated, deployed anonymously, and responds to `list products`

Known product issue:

- the public prompt `just list the product names we sell` triggered a
  clarification and mentioned the publishable-key header; this remains a public
  response-shaping/safety issue.

## Files Refreshed

- `README.md`
- `docs/README.md`
- `docs/route-deck/route-deck-overview.md`
- `docs/route-deck/authoring-guide.md`
- `docs/route-deck/debugging-guide.md`
- `docs/route-deck/manifest-reference.md`
- `docs/route-deck/migration-notes.md`
- `architecture/route-deck-corpus-vision.md`
- `decisions/ADR-013-routedeck-corpus-boundary.md`
- `SYSTEM_FLOW_INDEX.md`
- `../routedeck/docs/using-routedeck.md`

## Next Step

If continuing implementation, prioritize public deployed-chat response shaping
so visitors are never asked for connection-level API auth details and product
results are summarized safely by default.

