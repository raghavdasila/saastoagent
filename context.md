# SaaStoAgent v0.1 Context

Last Updated: May 21, 2026 15:30
Project: SaaStoAgent v0.1
Status: The Corpus-centered builder workbench remains the RouteDeck surface, and
the first deployed-agent web-chat slice is now implemented at `/a/:slug`.
Continue by deepening deployed-agent acceptance fixtures and execution policy,
not by replacing the builder shell or hardcoding Medusa behavior.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

## Start Here

- Latest checkpoint: `context_checkpoints/context_checkpoint_21-05-2026-11-07AM.md`
- Previous context archived at:
  `context_history/20260521_1107_context_before_corpus_workbench_and_routedeck_debugger_closeout.md`
- Closeout log:
  `logs/20260521_1107_corpus_workbench_and_routedeck_debugger_closeout.md`
- Validated architecture note:
  `architecture/dev_validated_docs/2026-05-21_corpus_workbench_and_routedeck_debugger_validation.md`
- Framework RouteDeck anchor: `../routedeck/docs/agentic-ui-state-runtime.md`
- Product anti-drift vision: `architecture/route-deck-corpus-vision.md`
- Current plan/status: `plans/routedeck_runtime_store_reset_plan.md`

## Current Architecture

RouteDeck is graph-backed state management for agentic UI, and SaaStoAgent now
consumes it through a single Corpus workbench shell.

```text
CorpusGraphRuntime
  -> SaaStoAgent RouteDeck adapter
    -> generic RouteDeckRuntime
      -> RouteDeckStore
        -> AppGraphShell
          -> topbar and rails
          -> Corpus conversation with fixed composer
          -> inline active surfaces
          -> docked or fullscreen diagnostics
```

The core rules are:

- Graph owns truth, guards, and commits.
- RouteDeck owns the generic runtime/store over the graph.
- Corpus is the central SaaStoAgent product agent and consumes RouteDeck state.
- Auth and active surfaces stay inside the single workbench shell.
- Legal operations are not rendered as raw product UI.
- Visible choices are Corpus-authored proposals, initiated surfaces, or
  diagnostics.
- Diagnostics is read-only and exposes graph/runtime internals when opened.
- The focus debugger uses lane-separated routing; the full map uses a
  root-centered radial hub layout around `home`.
- Deployed agent chat is a separate visitor surface, not a RouteDeck workbench.
  It resolves by SaaSAgent slug, fetches deployment policy, and streams through
  the same agent chat/SSE runtime.
- ToolRouter is now represented by a backend-local adapter. It owns route/top-k/
  missing-param/policy/unsafe decisions; existing REST execution traces remain
  the executor of record.

## Implemented This Session

- Added deployed-agent deployment state with owner-managed settings:
  `enabled`, `visitor_auth_mode`, `execution_mode`, `default_write_policy`, and
  `welcome_message`.
- Added public deployed-agent APIs:
  `GET /api/deployed-agents/{slug}` and
  `POST /api/deployed-agents/{slug}/chat`.
- Added the `/a/:slug` chat-only frontend surface with inline visitor auth gate,
  existing chat bubbles/tool cards, and no RouteDeck rail/debugger.
- Added a deployment card to the builder context panel so owners can enable and
  configure the public URL from the current SaaSAgent context.
- Added backend-local `ToolRouterAdapter` and wired it into the existing
  `rest_operator` path for route, top-k, missing-parameter, policy-confirmation,
  and unsafe destructive decisions.
- Added tests covering deployed access policy, public route registration,
  ToolRouter decisions, and REST-operator top-k formatting.

## Previous Implemented Session

- Refined the Corpus workbench shell, including auth/signup/login flow and
  authenticated topbar/surface behavior.
- Tightened the visual system across the shell, surfaces, buttons, fields, and
  composer container.
- Added fullscreen diagnostics and aligned the graph theme with the new shell.
- Added compact lane-separated routing in shared RouteDeck debugger code so
  sibling and opposite-direction edges do not overlap on the same path.
- Replaced the rejected sitemap full-map layout with a root-centered radial hub
  map.
- Added debugger routing/topology tests in `../routedeck/react/tests/`.
- Updated the RouteDeck runtime doc, plan, flow index, test note, architecture
  validation note, and closeout artifacts.

## Verification

- `python -m pytest backend/tests`: 65 passed.
- SaaStoAgent frontend `npm run type-check`: passed.
- SaaStoAgent frontend `npm run build`: passed, with the existing Vite large
  chunk warning.
- `docker compose up -d --build`: backend/frontend/db started successfully.
- Docker smoke:
  - `GET http://localhost:8085/api/health`: `{"status":"ok"}`
  - `GET http://localhost:3007/a/not-enabled-yet`: returned the SPA.
  - Browser smoke on `/a/not-enabled-yet`: rendered “Agent unavailable” with no
    console errors.

### Previous Verification

- `python -m pytest backend/tests/test_app_graph_contract.py -q`: 16 passed.
- `npm test` in `agent-lab-powered-projects/routedeck/react`: 6 passed.
- SaaStoAgent frontend `npm run type-check`: passed.
- SaaStoAgent frontend `npx tsc -p tsconfig.json && npx vite build --outDir dist_verify`:
  passed.
- Session browser QA showed:
  - signup/login stayed inside the workbench shell
  - diagnostics fullscreen did not break the composer
  - `auth_register <-> home` rendered as separate focus-graph paths
  - the radial hub full map rendered `29` unique routed paths

## Current Cleanup Status

Keep for now:

- Compatibility `/api/app/graph/*` paths remain debt until tests and remaining
  callers are migrated.
- Historical `OperatorGateway` sections in `SYSTEM_FLOW_INDEX.md` remain as
  compatibility notes, with the active status section superseding them.

## Next Concrete Step

Continue the deployed-agent sandbox slice:

1. Seed deterministic Storefront and Admin OpenAPI fixture flows without
   hardcoding product routing logic.
2. Add end-to-end tests that create a SaaSAgent, activate Storefront, enable
   deployment, chat through `/a/:slug`, then repeat with Admin write approval.
3. Deepen visitor-auth policy into per-action and per-connection overrides.
4. Add richer deployed result/approval cards after the text-first flow is stable.
5. Keep RouteDeck as the builder/workbench surface and keep `/a/:slug` chat-only.

## Anti-Drift Reminder

If future implementation reintroduces page-replacing auth shells, raw
legal-operation chips, or sitemap assumptions for the full map, stop and return
to `../routedeck/docs/agentic-ui-state-runtime.md`.
