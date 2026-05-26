# SaaStoAgent v0.1 Context

Last Updated: May 26, 2026 02:21 PM IST
Project: SaaStoAgent v0.1
Status: Documentation and RouteDeck context refreshed after the RouteDeck/Corpus boundary repair. Runtime code is not changed by this docs pass.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

## Start Here

- Project README and setup: `README.md`
- Latest checkpoint: `context_checkpoints/context_checkpoint_26-05-2026-02-21PM.md`
- Previous context archived at:
  `context_history/20260526_1421_context_before_docs_refresh.md`
- Closeout log for this docs refresh:
  `logs/20260526_1421_docs_and_routedeck_guide_refresh.md`
- RouteDeck product guide:
  `docs/route-deck/route-deck-overview.md`
- RouteDeck sibling framework guide:
  `../routedeck/docs/using-routedeck.md`
- RouteDeck framework anchor:
  `../routedeck/docs/agentic-ui-state-runtime.md`
- Boundary ADR:
  `decisions/ADR-013-routedeck-corpus-boundary.md`
- System flow source of truth:
  `SYSTEM_FLOW_INDEX.md`
- Medusa validation guide:
  `docs/medusa-api-agent-test-guide.md`

## Current Runtime Model

The active owner workbench follows this contract:

```text
AppGraph state
  -> RouteDeck projection
    -> Corpus planning_context
      -> Corpus chooses product op, surface intent, or clarification
        -> runtime validates against current projection
          -> graph commits, rejects, or opens review
```

The boundary rule:

- RouteDeck exposes validated app state, surfaces, diagnostics, and legal capabilities.
- Corpus interprets normal chat against product-facing context.
- The graph/runtime validates and commits typed operations.
- React renders the projected product surfaces and dispatches typed operations.

## Current App Setup

Docker app ports:

- frontend: `http://localhost:3007`
- backend health: `http://localhost:8085/api/health`
- Medusa target backend/admin: `http://localhost:9000`
- Medusa storefront: `http://localhost:8000`

Primary app routes:

- `/app/home`
- `/app/:nodeId`
- `/app/agents/:saasAgentId`
- `/app/agents/:saasAgentId/:nodeId`
- deployed public chat: `/a/{slug}`

Primary RouteDeck/Corpus endpoints:

- `GET /api/corpus/state`
- `POST /api/corpus/action`
- `GET /api/corpus/stream`
- `GET /api/diagnostics/stream`

The standard active-surface query parameter is `surface_id`.

## What Is Current After The Boundary Repair

### Hardcoded Chat Routing Removed

- Python phrase routing and alias-router fallbacks were removed from the owner-workbench Corpus path.
- Corpus now receives structured `planning_context` and chooses typed legal operations or product-safe clarifications.
- Normal chat should not depend on backend phrase tables such as "open learning" or "show rejected".

### Planning Context Is Product-Facing

Normal Corpus planning context includes:

- current node and active surface
- active SaaS Agent summary
- active surfaces
- product-facing surface options
- visible selectable entities with bound operation payloads
- product legal operations and accepted args

Normal Corpus planning context excludes:

- hidden internal route operations
- blocked operations
- raw endpoint paths
- trace ids
- approval ids
- credential values or visitor-fillable API auth headers

### Route Operations Are Internal

The app graph still defines hidden route operations:

- `route.open_node`
- `route.switch_surface`
- `route.back`
- `route.forward`
- `route.cancel`

These are runtime/browser/history infrastructure. They may exist in the richer
RouteDeck projection for framework clients and diagnostics, but they are not
normal Corpus planning vocabulary and must not render as ordinary product quick
actions.

Product surface intents can still be mapped to validated internal route
dispatch by runtime code after Corpus chooses a valid `surface_options` entry.

### Clicks And Chat Share The Typed Operation Path

- Product buttons dispatch typed operations from the current RouteDeck projection.
- Chat chooses product operations or surface intents from the same projected
  context.
- The runtime validates operation ids, args, node/surface legality, active
  SaaS Agent context, and pending review state before commit.

### Recent Regression Fixes To Preserve

- Hidden/internal `route.*` operations are filtered out of normal quick-action chips.
- Chat-driven navigation should not remount the whole app shell or refresh the full page.
- Frontend/backend surface query handling uses `surface_id`.
- Browser URL replay is treated as validated location replay, not product intent.
- Pending approval polling should stay gated to approval-relevant UI/state rather than global two-second shell polling.

## Medusa Setup Status

Medusa remains an acceptance fixture, not product hardcoding.

Recent manual setup under the provided owner account created and verified:

- SaaS Agent: `Live Commerce Raghav 1779776944731`
- Public URL: `http://localhost:3007/a/live-commerce-raghav-1779776944731`
- Connection: `Live Commerce Store API`
- Activation: ready, with 64 generated actions/tools
- Deployment: enabled, anonymous access
- Public prompt `list products`: returned `Medusa T-Shirt`, `Medusa Sweatshirt`,
  `Medusa Sweatpants`, and `Medusa Shorts`

Do not write account passwords, publishable keys, OpenAI keys, approval ids, or
trace ids into repo docs.

## Known Debt To Carry Forward

### Public Chat Response Shaping

Public deployed chat can still phrase some natural requests poorly. A browser
smoke showed `just list the product names we sell` caused a clarification and
mentioned the publishable-key header. The explicit guide prompt `list products`
worked.

This is not a RouteDeck owner-workbench boundary failure, but it is a product
safety/response-shaping issue. Public chat must not ask visitors for
connection-level API auth details.

### Compatibility Surfaces

Some compatibility endpoints/routes remain for older callers and tests. New
work should use `/api/corpus/*`, `/api/diagnostics/stream`, and the `/app/*`
shell.

### Docs Need To Stay Coupled To Runtime Claims

If a doc says a behavior is current, rerun at least:

```powershell
Invoke-RestMethod http://localhost:8085/api/health
Invoke-WebRequest http://localhost:3007 -UseBasicParsing
cd frontend
npm run type-check
```

For runtime behavior changes, also rerun the backend RouteDeck/Corpus suite and
the Docker browser E2E scripts listed in `README.md`.

## Anti-Drift Reminder

- RouteDeck exposes current legal context; Corpus decides; AppGraph validates and commits.
- RouteDeck shared code stays product-neutral.
- Corpus must not reintroduce phrase routing, alias tables, or hidden navigation heuristics.
- Legal operations are not automatically generic product buttons.
- Hidden/internal route ops are diagnostics/runtime infrastructure, not normal product planning vocabulary.
- Public deployed chat must not expose internal resource ids, endpoint paths, trace ids, operation ids, approval ids, API auth headers, or raw tool labels.
- Medusa remains an acceptance fixture only.
