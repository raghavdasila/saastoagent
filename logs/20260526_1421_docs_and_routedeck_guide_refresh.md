# 2026-05-26 14:21 IST - Docs And RouteDeck Guide Refresh

## Scope

This pass refreshed stale project and RouteDeck documentation after the
RouteDeck/Corpus boundary repair.

No runtime code was intentionally changed.

## What Changed

- Replaced the obsolete root README that still described Slice 1 and port 3005.
- Added current setup/run/validation instructions for Docker, the owner builder,
  backend health, Medusa target, and browser E2E scripts.
- Rewrote the RouteDeck guide set under `docs/route-deck/` around the current
  `backend/services/app_graph` and `/api/corpus/*` architecture.
- Captured the internal navigation lane vs Corpus planning lane:
  - internal route ops remain hidden runtime/browser infrastructure
  - normal Corpus planning sees product operations, surface options, and visible
    entities
- Updated context, checkpoint, ADR, architecture vision, and system flow docs.
- Refreshed the sibling RouteDeck usage guide with the product-neutral version
  of the same boundary.

## Important Current Facts Recorded

- Primary frontend: `http://localhost:3007`
- Primary backend health: `http://localhost:8085/api/health`
- Standard surface query key: `surface_id`
- Primary app shell: `/app/*`
- Primary Corpus endpoints:
  - `GET /api/corpus/state`
  - `POST /api/corpus/action`
  - `GET /api/corpus/stream`
  - `GET /api/diagnostics/stream`
- Hidden route operations:
  - `route.open_node`
  - `route.switch_surface`
  - `route.back`
  - `route.forward`
  - `route.cancel`

## Known Debt Preserved

Public deployed chat still needs response-shaping hardening. A natural product
query can still trigger an over-technical clarification that mentions the
publishable-key header. This should be fixed before treating public chat copy as
production-safe.

## Validation Expected For Closeout

- documentation stale-string scan
- backend/frontend health checks if Docker services are running
- `cd frontend && npm run type-check`

