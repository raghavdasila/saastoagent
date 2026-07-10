# SaaStoAgent v0.1

SaaStoAgent v0.1 is a local product-runtime prototype for turning an
OpenAPI-described SaaS surface into a configured, deployable SaaS Agent.

The current app is not a generic chatbot demo. It is a graph-owned builder and
deployed-agent runtime:

- owners sign in, create a SaaS Agent, connect an OpenAPI API, generate tools,
  inspect catalog/actions/entities, configure deployment, and review learning or
  approval surfaces
- visitors use the deployed public chat at `/a/{slug}`
- generated API execution stays OpenAPI-driven; Medusa is only the acceptance
  fixture used to prove the system works against a real target
- RouteDeck owns graph-backed app state, legal capabilities, surfaces,
  navigation/runtime diagnostics, and React store plumbing
- Corpus is the SaaStoAgent product agent that interprets normal user chat
  against RouteDeck-projected context and chooses typed legal operations

## Current Mental Model

```text
Product graph owns truth, guards, and commits.
RouteDeck exposes validated state, surfaces, diagnostics, and legal capabilities.
Corpus interprets normal chat against product-facing context.
Runtime validates the typed operation and commits, rejects, or opens review.
React renders the projected surfaces and dispatches typed operations.
```

RouteDeck exposes more than Corpus should normally speak. Internal navigation
operations such as `route.open_node`, `route.switch_surface`, `route.back`,
`route.forward`, and `route.cancel` exist for runtime/browser replay and
diagnostics, but they are hidden from ordinary Corpus planning and product quick
actions. Normal chat and clickable UI actions should converge on product-facing
typed operations such as opening a SaaS Agent, configuring an API, saving
instructions, approving learning, or opening a named surface option.

## Repository Layout

Key project paths:

- `backend/` - FastAPI app, graph runtime, RouteDeck/Corpus integration, SaaS
  Agent services, generated tool execution, learning, memory, and QA APIs
- `frontend/` - React/Vite workbench, RouteDeck store integration, owner shell,
  diagnostics, deployed-agent chat, and browser E2E harnesses
- `docs/` - operator/developer guides, including RouteDeck and Medusa setup
- `architecture/` - architecture vision and validation records
- `decisions/` - accepted ADRs, including the RouteDeck/Corpus boundary
- `context.md` - current restart/status handoff for future sessions
- `SYSTEM_FLOW_INDEX.md` - current flow and architecture index
- `vendor/routedeck-v0-compat/` - pinned RouteDeck v0 compatibility snapshot
  required by this mature product runtime; see its `PROVENANCE.md`
- `../routedeck/` - optional sibling standalone RouteDeck repository containing
  the real Medusa acceptance fixture used by the browser E2E

## Prerequisites

Required locally:

- Docker Desktop or compatible Docker with `host.docker.internal`
- Node.js/npm for frontend scripts and browser harnesses
- Python for backend tests and optional schema serving
- An OpenAI API key for AI-backed Corpus and deployed-agent chat turns

The app builds only from this repository. RouteDeck v0 compatibility code is
vendored explicitly, so a sibling checkout is not required to build or test the
product. Run commands from this directory unless noted otherwise:

```powershell
cd "D:\Dev\AI Projects\saastoagent-v0.1"
```

Useful environment variables:

- `STA_OPENAI_API_KEY` - required for real model-backed owner/deployed chat
- `STA_DEFAULT_MODEL` - defaults to `gpt-5-mini`
- `STA_OPENAI_REASONING_EFFORT` - defaults to `minimal`
- `STA_AUTH_SECRET` - defaults to a local dev secret
- `STA_ENCRYPTION_KEY` - defaults to a local dev Fernet key for fixture/dev use

Do not commit real credentials. For the optional real-Medusa acceptance run,
the sibling RouteDeck fixture generates its ignored credentials at
`..\routedeck\examples\medusa-agent\infra\CREDS.generated.env`.

## Run The App

Start SaaStoAgent:

```powershell
docker compose up -d --build backend frontend
```

Open:

- Owner builder: `http://localhost:3007`
- Backend health: `http://localhost:8085/api/health`

Check health:

```powershell
Invoke-RestMethod http://localhost:8085/api/health
Invoke-WebRequest http://localhost:3007 -UseBasicParsing
```

Expected ports:

- frontend preview: `3007`
- backend API: `8085`
- app Postgres: Docker-internal only

The frontend image installs from `package-lock.json`; the container runs
`npm run build && npm run preview`. For local frontend-only development, use:

```powershell
cd frontend
npm ci
npm run dev
```

## First Owner Flow

From `http://localhost:3007`:

1. Register or sign in.
2. Create a SaaS Agent with a name and slug.
3. Ask Corpus to set up the API connection, or click the product action for API
   setup.
4. Provide an OpenAPI URL, base URL, auth type, credential, and header/query
   metadata.
5. Activate the connection and confirm catalog readiness.
6. Configure deployment and enable anonymous or login-required public access.
7. Open the deployed URL at `/a/{slug}` and test visitor chat.

The owner workbench should use product language. Generic internal route
operations should not appear as quick actions in normal UI.

## Medusa Fixture Path

Medusa is the main local acceptance target. It proves that SaaStoAgent can
connect to a real commerce API from OpenAPI, generate actions/tools, execute
read operations, stage policy gaps, approve learning, and complete a public chat
flow without hardcoding Medusa behavior into the product runtime.

Provision and start the target fixture from the sibling RouteDeck repository.
RouteDeck's extraction report records the isolated port override used during
this migration; its normal demo port is 9100:

```powershell
cd "D:\Dev\AI Projects\routedeck"
.\examples\medusa-agent\scripts\demo-stack.ps1 Provision
.\examples\medusa-agent\scripts\demo-stack.ps1 Up -Services medusa
Invoke-RestMethod http://127.0.0.1:9100/health
```

Medusa ports:

- backend/admin API: `http://127.0.0.1:9100`
- fixture Postgres and Redis: Docker-internal only

Use the detailed guide for schema serving, publishable key setup, and public
chat validation:

- `docs/medusa-api-agent-test-guide.md`

## Validation Commands

Fast contract checks:

```powershell
python -m pytest backend/tests/test_corpus_turn_planning.py backend/tests/test_corpus_graph_contract.py backend/tests/test_app_graph_contract.py -q
cd frontend
npm run type-check
```

Broader RouteDeck/Corpus backend checks:

```powershell
python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q
```

Docker browser flows:

```powershell
cd frontend
npm run e2e:docker
npm run e2e:medusa:docker
```

The Medusa E2E starts its own schema server on port `9110` by default and
expects both the real Medusa target and SaaStoAgent Docker services to be
reachable. Set `E2E_MEDUSA_BACKEND_URL` when the target is mapped to a port
other than 9100, and set `E2E_MEDUSA_SCHEMA_PORT` to a distinct port when
needed.

## Troubleshooting

- If Corpus chat answers without acting, confirm `STA_OPENAI_API_KEY` is present
  in the backend container environment and restart the backend.
- If API activation cannot fetch the schema, remember the backend runs in
  Docker. Use `http://host.docker.internal:<port>/...` for host-served schemas,
  not `localhost`.
- If public chat asks visitors for API headers or internal IDs, treat it as a
  product-safety bug. Connection-level auth details must be handled privately.
- If `Open node` or `Switch surface` appears as a normal quick action, the UI is
  leaking hidden/internal RouteDeck operations.
- If a chat navigation refreshes the full page, verify the app still mounts one
  `/app/*` shell route and uses RouteDeck state updates rather than React Router
  remounts for graph navigation.
- If approval polling appears every two seconds from unrelated surfaces, check
  that pending approvals polling is gated to approval-relevant UI/state.

## Read Next

- Current restart/status handoff: `context.md`
- Flow index: `SYSTEM_FLOW_INDEX.md`
- RouteDeck/Corpus vision: `architecture/route-deck-corpus-vision.md`
- Boundary ADR: `decisions/ADR-013-routedeck-corpus-boundary.md`
- RouteDeck product guide: `docs/route-deck/route-deck-overview.md`
- Vendored compatibility provenance:
  `vendor/routedeck-v0-compat/PROVENANCE.md`
- Medusa setup guide: `docs/medusa-api-agent-test-guide.md`
