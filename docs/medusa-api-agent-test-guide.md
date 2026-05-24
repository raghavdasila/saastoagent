# Medusa API Agent Test Guide

This guide covers the local end-to-end Medusa validation path:

1. run the Medusa target fixture
2. run SaaStoAgent v0.1
3. set up the Medusa Store API in Corpus
4. deploy the agent
5. test the public deployed chat
6. run the automated browser harness

The Medusa fixture is only a target API. The SaaStoAgent runtime should stay OpenAPI-driven and must not branch on Medusa product names, fixture ids, or Medusa-specific endpoints.

## Paths

From the `agent-core` workspace:

```powershell
$Root = "D:\Dev\AI Projects\agent-core"
$App = "$Root\agent-lab-powered-projects\saastoagent-v0.1"
$Targets = "$Root\test_targets"
```

Important files:

- Medusa credentials: `D:\Dev\AI Projects\agent-core\test_targets\CREDS.md`
- Medusa target compose: `D:\Dev\AI Projects\agent-core\test_targets\docker-compose.yml`
- SaaStoAgent compose: `D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1\docker-compose.yml`
- Store OpenAPI schema copy: `D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1\integration_prep\openapi_toolrouter\vendor\openapi_toolrouter_benchmark\artifacts\raw_openapi\medusa_store.yaml`
- Browser harness: `D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1\frontend\scripts\e2e-medusa-docker.mjs`

## Ports

Medusa target:

- Medusa backend and admin: `http://localhost:9000`
- Medusa admin UI: `http://localhost:9000/app`
- Medusa storefront: `http://localhost:8000`
- Medusa Postgres host port: `localhost:5434`

SaaStoAgent:

- Frontend: `http://localhost:3007`
- Backend: `http://localhost:8085`
- SaaStoAgent Postgres: Docker-internal only

Manual schema server:

- Host schema server: `http://localhost:9110`
- Docker-reachable schema URL: `http://host.docker.internal:9110/medusa_store.yaml`

The automated e2e script starts its own schema server and exposes the schema as `http://host.docker.internal:9110/medusa-store.yaml`.

## Prerequisites

Required locally:

- Docker Desktop or Docker with `host.docker.internal` support
- Node.js/npm for the frontend scripts
- Python if you want the manual static schema server path
- Existing Medusa fixture credentials in `test_targets\CREDS.md`

For AI-backed chat turns, make sure `STA_OPENAI_API_KEY` is available to the SaaStoAgent backend environment before starting Docker.

## 1. Start Medusa

Run the target fixture from `test_targets`:

```powershell
cd "D:\Dev\AI Projects\agent-core\test_targets"
docker compose up -d --build
```

Check containers:

```powershell
docker compose ps
```

Expected services:

- `sta-medusa-postgres`
- `sta-medusa-redis`
- `sta-medusa-setup`
- `sta-medusa-backend`
- `sta-medusa-storefront`

Check backend health:

```powershell
Invoke-RestMethod http://localhost:9000/health
```

Check credentials:

```powershell
Get-Content "D:\Dev\AI Projects\agent-core\test_targets\CREDS.md"
```

Use the publishable API key from this line:

```text
Publishable API key: pk_...
```

If you reset volumes with `docker compose down -v`, regenerate and copy credentials:

```powershell
docker compose up -d --build
docker cp sta-medusa-setup:/shared/CREDS.generated.md CREDS.md
```

## 2. Start SaaStoAgent

From the SaaStoAgent project:

```powershell
cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1"
docker compose up -d --build backend frontend
```

Check app health:

```powershell
Invoke-RestMethod http://localhost:8085/api/health
Invoke-WebRequest http://localhost:3007 -UseBasicParsing
```

Open the app:

```text
http://localhost:3007
```

## 3. Serve The Medusa Store OpenAPI Schema For Manual UI Setup

Corpus needs a URL the backend container can fetch. For manual testing, serve the checked-in Medusa Store OpenAPI schema from the host:

```powershell
cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1\integration_prep\openapi_toolrouter\vendor\openapi_toolrouter_benchmark\artifacts\raw_openapi"
python -m http.server 9110 --bind 0.0.0.0
```

Leave this process running while activating the API connection.

Use this OpenAPI URL in the Corpus connection form:

```text
http://host.docker.internal:9110/medusa_store.yaml
```

Why not `localhost`? The backend runs in Docker. From the backend container, `localhost` is the backend container itself, not your host machine.

## 4. Create An Owner Account And Agent

In the browser, go to:

```text
http://localhost:3007/register
```

Create any local owner account, for example:

- Display name: `Medusa Test Owner`
- Email: `medusa-test-owner@example.com`
- Password: `SaaStoAgent123!`

Create a SaaS agent:

- Name: `Live Commerce Manual Test`
- Slug: `live-medusa-manual-test`

The deployed public URL will be:

```text
http://localhost:3007/a/live-medusa-manual-test
```

Use a fresh slug if the slug already exists.

## 5. Open Corpus API Setup

In the agent builder, use the Corpus chat input and send:

```text
set up the API connection
```

This should open the connection setup surface.

## 6. Configure The Medusa Store API Connection

Use these values in the connection setup form:

- Connection name: `Live Commerce Store API`
- Base URL: `http://host.docker.internal:9000`
- OpenAPI URL: `http://host.docker.internal:9110/medusa_store.yaml`
- Auth type: `api_key_header`
- Credential: the `Publishable API key` from `test_targets\CREDS.md`
- Header name: `x-publishable-api-key`

Save and activate the API.

Expected result:

- the connection activates successfully
- generated tools/catalog become available
- the readiness indicator reaches `1/1 ready`

If activation fails:

- confirm Medusa health at `http://localhost:9000/health`
- confirm schema is reachable from the host at `http://localhost:9110/medusa_store.yaml`
- confirm the OpenAPI URL in Corpus uses `host.docker.internal`, not `localhost`
- confirm the publishable key was copied without extra spaces
- check backend logs with `docker compose logs -f backend`

## 7. Deploy The Agent

In the deployment/settings area:

1. enable the deployed agent
2. set access to `anonymous`
3. save deployment

Open:

```text
http://localhost:3007/a/<your-slug>
```

For the example slug:

```text
http://localhost:3007/a/live-medusa-manual-test
```

## 8. Manual Browser Test Script

In the public deployed chat, run this sequence:

```text
what products do we have
```

Expected:

- visible product summary includes `Medusa T-Shirt`
- raw JSON is not visible by default
- `View technical details` is shown for the collapsed API payload

Then:

```text
i want to buy medusa tshirt
```

Expected:

- the agent should not ask for a bare `id`
- it may show product details or summarize the selected product

Then:

```text
add the L size to cart
```

Expected before approving the generated policy candidate:

- the agent should not ask for a bare `id`
- the agent should not ask for `variant_id`
- the agent should not ask for `quantity`
- the agent should not ask for `cart id`
- the agent should say that an owner-approved automation policy is needed before it can manage carts for visitors
- Sandbox Learning should contain a `domain_policy_gap` candidate for the generated create-cart -> add-line-item action chain

Approve the `domain_policy_gap` candidate from the owner/admin Sandbox Learning review flow, then repeat the same public chat sequence in a new visitor session.

Expected after approval:

- the agent should create or reuse the internal cart dependency without exposing it
- the agent should call the generated add-line-item action with the selected variant and quantity
- the public chat should say that the action was handled
- the public chat should not show endpoint paths, operation ids, trace ids, raw internal slot names, or cart ids

## 9. Verify Backend Trace For The Add-To-Cart Turn

From the SaaStoAgent project:

```powershell
cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1"
docker compose exec -T db psql -U postgres -d saastoagent_v0_1 -c "select tool_name, status, method, path, inputs, missing_inputs from agent_execution_traces order by created_at desc limit 5;"
```

Before policy approval, the `add the L size to cart` turn should create a policy-gap trace and learning candidate:

```text
tool_name: postcartsidlineitems
status: needs_input
method: POST
path: /store/carts/{id}/line-items
inputs: {"quantity": 1, "variant_id": "..."}
missing_inputs: ["id"]
route_node: internal_dependency_policy
```

After policy approval, a repeat of the same flow should show the generated internal dependency chain:

```text
tool_name: postcarts
status: succeeded
method: POST
path: /store/carts
missing_inputs: []

tool_name: postcartsidlineitems
status: succeeded
method: POST
path: /store/carts/{id}/line-items
inputs: {"id": "cart_...", "quantity": 1, "variant_id": "..."}
missing_inputs: []
approval_state: approved_by_policy
```

The exact `cart_...` and `variant_id` values can change if the Medusa seed data changes. The important assertions are:

- `variant_id` is present
- `quantity` is present
- the cart path id is resolved internally after approval
- product id is not used as the cart id
- no internal ids are exposed in the public transcript

## 10. Run The Automated Medusa Browser Harness

The automated harness performs the owner signup, agent creation, Corpus setup, deployment, and public product query.

Make sure both stacks are running:

```powershell
cd "D:\Dev\AI Projects\agent-core\test_targets"
docker compose up -d --build

cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1"
docker compose up -d --build backend frontend
```

Run the harness from the frontend folder:

```powershell
cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1\frontend"
npm run e2e:medusa:docker
```

Expected result:

```json
{
  "ok": true,
  "evidence": {
    "appUrl": "http://localhost:3007",
    "medusaBackendUrl": "http://host.docker.internal:9000",
    "medusaHeaderName": "x-publishable-api-key",
    "query": "list products",
    "deployedUrl": "http://localhost:3007/a/live-medusa-...",
    "screenshots": [
      "...builder-medusa-activated.png",
      "...public-medusa-products.png"
    ]
  }
}
```

Screenshots are written to:

```text
%TEMP%\saastoagent-medusa-ui-e2e-<timestamp>
```

Override the artifact directory:

```powershell
$env:SAASTOAGENT_E2E_ARTIFACT_DIR = "D:\Dev\AI Projects\agent-core\_tmp\medusa-e2e"
npm run e2e:medusa:docker
```

The harness reads the publishable key from:

```text
D:\Dev\AI Projects\agent-core\test_targets\CREDS.md
```

The harness starts its own schema server on port `9110`. If port `9110` is already occupied by your manual schema server, stop it or run the harness with another port:

```powershell
$env:E2E_MEDUSA_SCHEMA_PORT = "9111"
npm run e2e:medusa:docker
```

## 11. Optional Continuation Browser Check

The packaged harness currently validates product listing. To manually verify continuation in a rendered browser, use the deployed URL printed by the harness and send:

```text
what products do we have
i want to buy medusa tshirt
add the L size to cart
```

Then check the latest trace:

```powershell
cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1"
docker compose exec -T db psql -U postgres -d saastoagent_v0_1 -c "select tool_name, status, method, path, inputs, missing_inputs from agent_execution_traces order by created_at desc limit 1;"
```

Expected:

```text
postcartsidlineitems | needs_input | POST | /store/carts/{id}/line-items | {"quantity": 1, "variant_id": "..."} | ["id"]
```

## 12. Troubleshooting

### Medusa is not reachable

Check:

```powershell
cd "D:\Dev\AI Projects\agent-core\test_targets"
docker compose ps
docker compose logs -f medusa-backend
Invoke-RestMethod http://localhost:9000/health
```

If the database was reset, refresh `CREDS.md`:

```powershell
docker cp sta-medusa-setup:/shared/CREDS.generated.md CREDS.md
```

### Corpus cannot fetch the OpenAPI URL

Check the manual schema server:

```powershell
Invoke-WebRequest http://localhost:9110/medusa_store.yaml -UseBasicParsing
```

In Corpus, use:

```text
http://host.docker.internal:9110/medusa_store.yaml
```

Do not use:

```text
http://localhost:9110/medusa_store.yaml
```

### Credential decrypt errors after backend restart

The Docker backend uses `STA_ENCRYPTION_KEY` from `docker-compose.yml`. If you override it locally, keep it stable across backend restarts or recreate the connection credentials.

### Public chat shows raw JSON

Expected current behavior is:

- short human summary is visible
- raw payload is hidden behind `View technical details`
- raw JSON is not rendered into the closed details DOM

If raw JSON is visible in the public transcript, rerun:

```powershell
cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1\frontend"
npm run type-check
```

Then rebuild/restart frontend:

```powershell
cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1"
docker compose restart frontend
```

### Add-to-cart asks for payment collection id

This means continuation routing regressed to another write action. Check the latest trace:

```powershell
docker compose exec -T db psql -U postgres -d saastoagent_v0_1 -c "select tool_name, status, method, path, inputs, missing_inputs, candidate_summary from agent_execution_traces order by created_at desc limit 1;"
```

Expected action:

```text
postcartsidlineitems
```

If another action is selected, inspect the execution frame in the latest active session metadata and verify that selected product context was preserved across the product-detail turn.

## 13. Cleanup

Stop SaaStoAgent:

```powershell
cd "D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1"
docker compose down
```

Stop Medusa:

```powershell
cd "D:\Dev\AI Projects\agent-core\test_targets"
docker compose down
```

Reset Medusa data and generated credentials:

```powershell
cd "D:\Dev\AI Projects\agent-core\test_targets"
docker compose down -v
docker compose up -d --build
docker cp sta-medusa-setup:/shared/CREDS.generated.md CREDS.md
```

Do not reset volumes if you need to preserve existing local traces, agents, or Medusa seed state for comparison.
