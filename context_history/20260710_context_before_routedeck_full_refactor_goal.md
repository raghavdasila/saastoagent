# SaaStoAgent v0.1 Context - Archived 2026-07-10 Before RouteDeck Full Refactor Goal

Last Updated: June 10, 2026
Project: SaaStoAgent v0.1
Status: Setup-time fusion ToolRouter indexing is implemented for arbitrary OpenAPI-backed SaaS Agents, and runtime candidate selection now reads the ready index directly.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`
Current branch: `saastoagent`
Recent baseline commit: `f15139c3 RouteDeck updates`

## Start Here

- Project README and setup: `README.md`
- Latest checkpoint: `context_checkpoints/context_checkpoint_26-05-2026-3-37PM.md`
- Previous context archived at:
  `context_history/20260526_1537_context_before_routedeck_whitepaper_closeout.md`
- Closeout log for this session:
  `logs/20260526_1537_routedeck_whitepaper_closeout.md`
- RouteDeck whitepaper:
  `../routedeck/docs/route-deck-whitepaper.md`
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
- Fusion ToolRouter implementation plan:
  `docs/superpowers/plans/2026-06-10-saastoagent-fusion-rag-toolrouter.md`

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

The generated API routing rule:

- API activation builds a per-SaaS-Agent fusion router index from current
  `ActionNode` and `GeneratedTool` rows after tools are generated.
- Runtime candidate selection uses that ready index through
  `find_tool_candidates()` and does not rebuild indexes during owner or public
  chat usage.
- The ranker only scores candidates; missing-parameter handling, approvals,
  unsafe destructive blocking, execution frames, traces, learning, and public
  response safety stay downstream.

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

### Fusion ToolRouter Is Setup-Time

Catalog activation now streams a `router_index` step after generated tools:

- `Building fusion router index`
- `Fusion router index ready`
- router document and endpoint counts

The Catalog surface shows router index readiness, router document count, and
router version. The index is dynamic for each arbitrary API collection and must
not contain Medusa-specific endpoint maps, phrase routers, credentials, or
visitor auth material.

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

## RouteDeck Whitepaper Status

The RouteDeck whitepaper now exists at:

- `../routedeck/docs/route-deck-whitepaper.md`

It explains:

- why RouteDeck exists
- graph-backed state runtime mental model
- manifest, runtime state, projection, operations, surfaces, diagnostics
- internal navigation lane versus product planning lane
- one dispatch path for clicks and chat
- browser replay as location replay, not product intent
- diagnostics without public product leakage
- SaaStoAgent as a reference integration
- testing expectations and open-framework direction

## RouteDeck Open-Source Readiness Snapshot

Estimated readiness: 55-60% of a credible public alpha.

Already in place:

- Reusable package split exists: `routedeck_core`, `routedeck_langgraph`, and `@routedeck/react`.
- Core reusable source scan found no SaaStoAgent/Corpus/Medusa literals.
- Python and React tests pass.
- Minimal examples exist.
- Framework docs now include the whitepaper and practical usage guides.

Primary blockers:

- No `LICENSE` in `agent-lab-powered-projects/routedeck`.
- `@routedeck/react` is still `"private": true`.
- npm package needs real build/declaration output before publication.
- Python package metadata needs license, authors, URLs, classifiers, changelog, and release policy.
- CI/release automation is not yet established for isolated RouteDeck tests/builds.
- Public scrub/repo export plan is needed so ignored local artifacts never ship.
- Clean install smoke tests are still needed for PyPI/npm-style consumption and examples.

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

### Corpus Human-Like Testing

Next session should test Corpus through real owner-workbench behavior:

- create/open/publish a Medusa-backed SaaS Agent through normal chat and clicks
- verify navigation works without backend phrase tables or alias routers
- verify chat navigation does not remount or refresh the whole page
- verify hidden/internal route ops do not render as normal quick-action chips
- verify clicks and chat converge on the typed operation validation path

### Public Chat Response Shaping

The fusion router replacement is intended to improve natural product/API
candidate selection, including product-list and typo-tolerant read queries.
Public deployed chat still must be verified through browser/runtime smoke tests
for phrasing. It must not ask visitors for connection-level API auth details.

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

## Last Validation Evidence

Fusion ToolRouter implementation checks from June 10, 2026:

```powershell
python -m pytest backend/tests/test_toolrouter_documents.py backend/tests/test_toolrouter_index_builder.py backend/tests/test_toolrouter_fusion_ranker.py backend/tests/test_toolrouter_activation.py -q
```

Result: `13 passed`.

```powershell
python -m pytest backend/tests/test_rest_catalog.py backend/tests/test_toolrouter_adapter.py -q
```

Result: `35 passed`.

```powershell
python -m pytest backend/tests/test_api_orchestration.py backend/tests/test_execution_frames.py -q
```

Result: `35 passed`.

```powershell
python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py -q
```

Result: `77 passed`.

```powershell
cd frontend
npm run type-check
```

Result: passed.

RouteDeck package validation from the whitepaper closeout:

```powershell
python -m pytest agent-lab-powered-projects/routedeck/tests -q
```

Result: `17 passed in 0.54s`.

```powershell
npm test
```

Run from `agent-lab-powered-projects/routedeck/react`.

Result: `16 passed`.

```powershell
git diff --check
```

Result: no whitespace errors; only existing LF-to-CRLF warnings.

## Anti-Drift Reminder

- RouteDeck exposes current legal context; Corpus decides; AppGraph validates and commits.
- RouteDeck shared code stays product-neutral.
- Corpus must not reintroduce phrase routing, alias tables, or hidden navigation heuristics.
- Legal operations are not automatically generic product buttons.
- Hidden/internal route ops are diagnostics/runtime infrastructure, not normal product planning vocabulary.
- Public deployed chat must not expose internal resource ids, endpoint paths, trace ids, operation ids, approval ids, API auth headers, or raw tool labels.
- Medusa remains an acceptance fixture only.
