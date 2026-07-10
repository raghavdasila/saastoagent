# Real Medusa API Agent Test Guide

This guide validates the standalone SaaStoAgent v0.1 repository against the
real Medusa fixture in the sibling standalone RouteDeck repository. It does not
use fixtures or mock responses in the SaaStoAgent product path.

## Repository boundary

```text
D:\Dev\AI Projects\saastoagent-v0.1
D:\Dev\AI Projects\routedeck
```

SaaStoAgent builds independently because its required RouteDeck v0 contract is
pinned under `vendor/routedeck-v0-compat`. The sibling RouteDeck checkout is
needed only for this real Medusa acceptance target.

Generated credentials are private and ignored:

```text
D:\Dev\AI Projects\routedeck\examples\medusa-agent\infra\CREDS.generated.env
```

## Prerequisites

- Docker Desktop
- Node.js 24 and npm
- Playwright Chromium (`npx playwright install chromium`)
- a real `STA_OPENAI_API_KEY` in the ignored SaaStoAgent `.env`

The public-chat portion uses the configured OpenAI model. If the key or provider
is unavailable, stop and report that dependency; do not substitute canned
responses.

## 1. Start the real Medusa target

The RouteDeck fixture normally binds Medusa to port 9100:

```powershell
cd "D:\Dev\AI Projects\routedeck"
.\examples\medusa-agent\scripts\demo-stack.ps1 Provision
.\examples\medusa-agent\scripts\demo-stack.ps1 Up -Services medusa
Invoke-RestMethod http://127.0.0.1:9100/health
```

Expected health status is HTTP 200. The generated credentials file must contain
`MEDUSA_PUBLISHABLE_KEY`; never print or commit its value.

## 2. Start standalone SaaStoAgent

```powershell
cd "D:\Dev\AI Projects\saastoagent-v0.1"
docker compose --project-name saastoagent-v01-extracted up --detach --build
Invoke-RestMethod http://127.0.0.1:8085/api/health
Invoke-WebRequest http://127.0.0.1:3007 -UseBasicParsing
```

Smoke-test URLs:

- API health: `http://127.0.0.1:8085/api/health`
- owner UI: `http://127.0.0.1:3007`

## 3. Run the browser acceptance flow

With Medusa on its normal port, the harness defaults are sufficient:

```powershell
cd "D:\Dev\AI Projects\saastoagent-v0.1\frontend"
$env:E2E_APP_URL = "http://127.0.0.1:3007"
$env:E2E_MEDUSA_BACKEND_URL = "http://host.docker.internal:9100"
$env:E2E_MEDUSA_CREDS_PATH = "D:\Dev\AI Projects\routedeck\examples\medusa-agent\infra\CREDS.generated.env"
$env:SAASTOAGENT_E2E_ARTIFACT_DIR = "$PWD\recordings\real-medusa"
$env:E2E_HEADLESS = "1"
npm run e2e:medusa:docker
```

The harness serves the checked-in Medusa Store OpenAPI document to the backend
from the host. Its schema server defaults to port 9110.

If Medusa itself is deliberately remapped to 9110, use a distinct schema port:

```powershell
$env:E2E_MEDUSA_BACKEND_URL = "http://host.docker.internal:9110"
$env:E2E_MEDUSA_SCHEMA_PORT = "9111"
npm run e2e:medusa:docker
```

## Acceptance criteria

The run is successful only if it proves all of the following:

1. A new owner registers and creates a SaaS Agent.
2. The real Medusa OpenAPI connection activates.
3. The context lens reports one ready connection and generated tools.
4. The agent is deployed for anonymous access.
5. Public chat lists and filters real Medusa products.
6. The owner explicitly approves the learned cart policy.
7. A second cart attempt succeeds against Medusa.
8. Checkout completes through the live product flow.
9. Public output does not leak tool names, operation IDs, trace IDs, internal
   paths, credentials, or approval IDs.

The harness exits non-zero and captures `failure.png` when any assertion
fails. A JSON result on stdout lists the evidence files when the flow succeeds.

## Manual connection values

For an owner-driven run in `http://127.0.0.1:3007`:

- base URL: `http://host.docker.internal:9100`
- Store OpenAPI URL: the host-served `medusa-store.yaml`
- authentication: API key header
- header name: `x-publishable-api-key`
- credential: `MEDUSA_PUBLISHABLE_KEY` from the ignored RouteDeck credentials
  file

Use `host.docker.internal`, not `localhost`, for resources that the backend
container must reach on the Windows host.

## Focused verification

```powershell
cd "D:\Dev\AI Projects\saastoagent-v0.1"
.\.venv\Scripts\python.exe -m pytest backend\tests -q

cd frontend
npm run type-check
npm run build
```

The migration-specific result and exact isolated commands are recorded in
`docs/migration/EXTRACTION_REPORT.md`.
