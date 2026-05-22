# SaaStoAgent v0.1 Context

Last Updated: May 21, 2026 22:10
Project: SaaStoAgent v0.1
Status: The Corpus-centered builder workbench remains the RouteDeck surface, and
the horizontal sandbox path now has a repeatable Docker UI E2E harness covering
signup -> SaaSAgent creation -> OpenAPI connection -> catalog/tool activation ->
deployment -> public chat -> guarded Admin approval. Continue by deepening
module quality only after this harness stays green.
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
- Horizontal E2E guide: `docs/horizontal-e2e.md`

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
- RouteDeck operations distinguish legal from immediately dispatchable via
  `invocation_kind`, `can_dispatch_now`, `required_args`, and `missing_args`.
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

- Added the horizontal hardening pass:
  - `npm run e2e:docker` in `frontend`.
  - deterministic Storefront/Admin OpenAPI fixture on port `9109`.
  - Docker UI E2E for signup, create SaaSAgent, connect API, activate catalog,
    enable deployment, public Storefront read, Admin write approval, and cancel.
  - public leak assertions against operation names, paths, scores, trace text,
    and tool events.
- Added explicit deployed policy state contract values:
  `allowed_read`, `needs_visitor_auth`, `needs_owner_approval`, `blocked`, and
  `failed_with_recovery`.
- Added member-protected owner approval APIs:
  `GET /api/saas-agents/{id}/approvals/pending`,
  `POST /api/saas-agents/{id}/approvals/{trace_id}/approve`, and
  `POST /api/saas-agents/{id}/approvals/{trace_id}/cancel`.
- Added a builder pending-approvals card in the right context panel. Builder UI
  can show operation IDs/paths/tools because it is owner-facing; deployed chat
  remains natural-language only.
- Fixed the credentialed REST execution path uncovered by the Admin approval
  E2E: `inject_credentials` is keyword-only and the executor now calls it that
  way.
- Persisted owner approval/cancel outcomes back to the visitor session so the
  runtime has a thread-level record.
- Added deployed visitor session events:
  `GET /api/deployed-agents/{slug}/sessions/{session_id}/events`, backed by an
  in-process event bus and persisted approval-message catch-up.
- Deployed chat now subscribes to public-safe approval result events and updates
  the already-open visitor transcript after owner approve/cancel.
- Promoted RouteDeck operation readiness into the reusable framework and Corpus
  usage: unbound entity-selector actions such as `saas_agent.open` are legal but
  not rendered as one-click dispatch chips.
- Added the scalable SaaSAgent selection split:
  - `saas_agent.list` is a dispatchable RouteDeck surface operation.
  - `saas_agent.open` remains an entity-selector operation and requires a bound
    `saas_agent_id`.
  - Corpus home only carries the last two agents plus total count, avoiding
    full-list context clutter.
  - The dedicated `SaaSAgentListSurface` owns search/list rendering and binds
    `saas_agent_id` before dispatching open.
- Existing SaaSAgent dashboard cards now bind `saas_agent_id` when opening an
  agent, so incomplete agents can be resumed and configured instead of failing
  with `saas_agent_id is required`.
- Tightened `npm run e2e:docker` to assert live public approval/cancel messages,
  no public router leaks, and the Admin activation readiness wait.

## Previous Implemented Session

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

## Earlier Implemented Session

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

- `python -m pytest backend/tests/test_app_graph_contract.py -q`: 30 passed.
- `python -m pytest backend/tests -q`: 87 passed.
- SaaStoAgent frontend `npm run type-check`: passed.
- SaaStoAgent frontend `npm run build`: passed, with the existing Vite large
  chunk warning.
- Docker smoke:
  - `GET http://localhost:8085/api/health`: `{"status":"ok"}`
  - `GET http://localhost:3007`: returned `200`.
- `docker compose up -d --build backend frontend`: rebuilt and restarted
  backend/frontend successfully.
- `npm run e2e:docker`: passed against rebuilt Docker services and fixture
  `http://host.docker.internal:9109`.
  - Account: `ui-e2e-1779381777488@example.com`
  - Slug: `ui-e2e-1779381777488`
  - Evidence dir:
    `C:\Users\ragha\AppData\Local\Temp\saastoagent-ui-e2e-1779381777304`
  - Screenshots: `builder-activated.png`, `public-storefront-read.png`,
    `builder-approval-approved.png`

Important rule: future claims of "E2E passed" for this slice must include the
Docker UI harness or an equivalent browser-driven replacement. Backend tests
alone are not sufficient.

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

Deepen vertically only after keeping the horizontal harness green:

1. Deepen connection edit/reactivate recovery beyond the minimal retry path.
2. Add per-action policy overrides after the default approval rails stay stable.
3. Improve RAG/tool ranking quality against more OpenAPI fixtures.
4. Add direct UI coverage for `saas_agent.list` once the current E2E harness is
   expanded beyond the primary sandbox path.
5. Keep RouteDeck as the builder/workbench surface and keep `/a/:slug` chat-only.

## Anti-Drift Reminder

If future implementation reintroduces page-replacing auth shells, raw
legal-operation chips, or sitemap assumptions for the full map, stop and return
to `../routedeck/docs/agentic-ui-state-runtime.md`.
