# SaaStoAgent v0.1 Context

Last Updated: May 22, 2026 14:18 IST
Project: SaaStoAgent v0.1
Status: Horizontal sandbox slice is verified against Docker UI E2E and a real
Medusa target. The next session should not deepen modules until the remaining
horizontal architecture issues below are addressed.
Repository: `agent-lab-powered-projects/saastoagent-v0.1`

## Start Here

- Latest checkpoint: `context_checkpoints/context_checkpoint_22-05-2026-2-18PM.md`
- Previous context archived at:
  `context_history/20260522_1418_context_before_medusa_hardening_closeout.md`
- Closeout log:
  `logs/20260522_1418_sandbox_hardening_medusa_e2e_closeout.md`
- Framework RouteDeck anchor: `../routedeck/docs/agentic-ui-state-runtime.md`
- Product anti-drift vision: `architecture/route-deck-corpus-vision.md`
- ADR: `decisions/ADR-012-openapi-driven-target-fixtures.md`
- ADR: `decisions/ADR-013-routedeck-corpus-boundary.md`
- Dev validation:
  `architecture/dev_validated_docs/2026-05-22_openapi_driven_medusa_e2e_validation.md`
- Knowledgebase:
  `knowledgebase/patterns/openapi-driven-fixture-validation.md`
- Known gap:
  `knowledgebase/patterns/deployed-chat-result-continuity-gap.md`
- Current plan/status: `plans/routedeck_runtime_store_reset_plan.md`
- Horizontal E2E guide: `docs/horizontal-e2e.md`

## Current Architecture

RouteDeck is graph-backed state management for agentic UI. SaaStoAgent consumes
RouteDeck through the Corpus workbench, while deployed visitor chat at
`/a/:slug` remains a separate chat-only surface.

```text
CorpusGraphRuntime
  -> SaaStoAgent RouteDeck adapter
    -> generic RouteDeckRuntime
      -> RouteDeckStore
        -> AppGraphShell
          -> Corpus conversation
          -> inline setup/execution surfaces
          -> docked/fullscreen diagnostics

Deployed visitor chat
  -> /api/deployed-agents/{slug}
  -> /api/deployed-agents/{slug}/chat
  -> public-safe session event stream
  -> shared chat/runtime/execution services
```

Core rules:

- Graph owns truth, guards, and commits.
- RouteDeck owns generic operation/state metadata over the graph.
- Corpus owns SaaStoAgent-specific conversation, surfaces, and proposals.
- RouteDeck operations expose `invocation_kind`, `can_dispatch_now`,
  `required_args`, and `missing_args`; UI must not dispatch unbound operations.
- Builder diagnostics may expose graph internals, tool IDs, paths, traces, and
  approval metadata.
- Public deployed chat must not expose router internals, scores, endpoint paths,
  operation IDs, trace IDs, approval IDs, or raw tool labels.
- ToolRouter is a backend-local adapter. It owns route/top-k/missing-param/
  policy/unsafe decisions; REST execution traces remain the executor of record.
- Product runtime must remain OpenAPI/user-config driven. Medusa is an
  acceptance fixture only, not hardcoded product logic.

## Implemented Since Last Closeout

- Removed Medusa hardcoding from product runtime and UI:
  - generic connection placeholders and labels in app graph manifests/surfaces
  - removed the API target dropdown from setup
  - added raw OpenAPI schema textarea support
  - kept Medusa references only in fixtures, scripts, datasets, and E2E names
- Added generic raw OpenAPI activation:
  - connection config persists `raw_spec`
  - REST adapter discovers from `raw_spec` before `spec_url`
  - RouteDeck/form schemas support textarea fields
- Fixed credential/header leakage in generated tool inputs:
  - OpenAPI header/cookie params are excluded from generated tool schemas
  - REST missing-input prompts no longer ask for credential headers directly
- Fixed bare list query extraction:
  - `list products` no longer binds the full utterance into optional search
    fields like `q`
  - explicit search utterances can still bind search/query text
- Stabilized route/surface hydration:
  - browser path replacement now emits navigation state changes
  - E2E setup can reliably open `connection_configure`
  - existing/incomplete agents can be resumed through bound agent actions
- Added `npm run e2e:medusa:docker`:
  - starts/uses the real Medusa Docker target under `test_targets`
  - serves the Medusa Store OpenAPI fixture locally on port `9110`
  - uploads/configures schema through the UI
  - executes deployed chat through SaaStoAgent only
  - does not validate by direct target API calls

Earlier horizontal work in this slice remains active:

- deployed chat at `/a/:slug`
- public-safe approval event stream
- owner approval/cancel delivery back to visitor sessions
- RouteDeck dispatch-readiness metadata
- `saas_agent.list` selector surface and bound `saas_agent.open`
- Docker UI E2E for signup -> create agent -> connect OpenAPI -> activate ->
  deploy -> public chat -> guarded approval

## Verification

- `python -m pytest backend/tests/test_rest_catalog.py backend/tests/test_app_graph_contract.py -q`
  - Result: `45 passed in 19.28s`
- SaaStoAgent frontend `npm run type-check`
  - Result: passed
- `docker compose up -d --build frontend`
  - Result: rebuilt/restarted frontend/backend successfully
  - Existing Vite large chunk warning remains
- SaaStoAgent UI E2E:
  - Command: `npm run e2e:docker` from `frontend`
  - Result: passed
  - Account: `ui-e2e-1779437248299@example.com`
  - Password: `SaaStoAgent123!`
  - Slug: `ui-e2e-1779437248299`
  - Evidence dir:
    `C:\Users\ragha\AppData\Local\Temp\saastoagent-ui-e2e-1779437248116`
  - Screenshots: `builder-activated.png`, `public-storefront-read.png`,
    `builder-approval-approved.png`
- Real Medusa UI E2E:
  - Command: `npm run e2e:medusa:docker` from `frontend`
  - Result: passed
  - SaaStoAgent account: `medusa-ui-e2e-1779437277860@example.com`
  - SaaStoAgent password: `SaaStoAgent123!`
  - Slug: `live-medusa-1779437277860`
  - Deployed URL: `http://localhost:3007/a/live-medusa-1779437277860`
  - Medusa backend: `http://host.docker.internal:9000`
  - Medusa schema served for UI upload:
    `http://host.docker.internal:9110/medusa-store.yaml`
  - Evidence dir:
    `C:\Users\ragha\AppData\Local\Temp\saastoagent-medusa-ui-e2e-1779437277844`
  - Screenshots: `builder-medusa-activated.png`,
    `public-medusa-products.png`
- Latest DB trace check for real Medusa:
  - status: `succeeded`
  - approval: `not_required`
  - request inputs: `{"limit": 5}`
  - returned 4 seeded products including `Medusa T-Shirt`
- Product code scan for `medusa|Medusa|MEDUSA` under backend services/providers
  and frontend source returned no product-runtime matches.

Important rule: future claims of "E2E passed" for this slice must include the
Docker UI harness or an equivalent browser-driven replacement. Backend tests
alone are not sufficient.

## Known Issues To Carry Forward

### RouteDeck/Corpus Boundary

RouteDeck is still too tied into Corpus in implementation. This should be fixed
architecturally before more module depth:

- RouteDeck should remain a framework/runtime layer for graph state, legal
  operations, dispatch readiness, diagnostics, and generic surface contracts.
- Corpus should integrate RouteDeck but own SaaStoAgent-specific conversation,
  proposal wording, agent list/search rendering, setup surfaces, and recovery
  UX.
- Avoid pushing Corpus domain concepts into RouteDeck core just because Corpus
  is the first consumer.

### Raw JSON Public Result UX

Deployed chat still exposes raw JSON directly for product results. Do not solve
the final product-card flow yet, but the next pass should add a collapsible UI
as a stopgap:

- show a natural summary first
- hide raw JSON behind an expandable detail control
- keep builder diagnostics free to expose full raw payloads
- keep public chat free of operation IDs, paths, scores, trace IDs, and tool
  labels

### Query Continuity And Cart Follow-Up Bug

Observed real Medusa conversation failure:

1. Visitor asked `what products do we have`.
2. Agent returned raw product JSON including `Medusa T-Shirt`.
3. Visitor asked `i want to buy medusa tshirt`.
4. Agent asked for internal `id`.
5. Visitor said `idk`.
6. Agent recovered partially and identified the T-shirt plus sizes.
7. Visitor asked `add the L size to cart`.
8. Agent fell back to a generic missing-detail prompt asking about unrelated
   routes and `x publishable api key`.

Do not fix this in the closeout. Next session should treat it as a runtime
query/action-continuity issue:

- use prior tool results as conversation-grounded entity candidates
- resolve product title -> product ID -> variant/option
- orchestrate cart creation/add-item steps instead of asking for internal IDs
- suppress credential/header names from public clarifications
- ask natural missing details only, such as size, quantity, region, shipping, or
  confirmation
- keep the flow OpenAPI-driven and avoid Medusa-specific runtime logic

## Next Concrete Step

Start the next session with horizontal cleanup, not feature depth:

1. Split RouteDeck framework concerns from Corpus product concerns.
2. Add collapsible public result rendering for JSON payloads.
3. Fix query continuity for list -> select product -> choose variant -> cart
   action.
4. Re-run `npm run e2e:docker` and `npm run e2e:medusa:docker` after the fixes.

## Credentials From Latest Verified Runs

- SaaStoAgent Medusa E2E owner:
  `medusa-ui-e2e-1779437277860@example.com` / `SaaStoAgent123!`
- SaaStoAgent mock E2E owner:
  `ui-e2e-1779437248299@example.com` / `SaaStoAgent123!`
- Medusa fixture admin:
  `admin@saastoagent.local` / `Admin123!`
- Medusa publishable API key used by the fixture:
  `pk_b876cb7077c42ef6e7506b2b64a57f21a6f80db392bfd2e962e6690a242f732b`

## Anti-Drift Reminder

If future implementation reintroduces hardcoded Medusa routing, raw
legal-operation chips, direct unbound `saas_agent.open`, or public router
internals, stop and return to the RouteDeck/Corpus architecture before adding
more features.
