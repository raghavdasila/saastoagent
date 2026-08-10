# Corpus Local Runtime Runbook

This is the authoritative procedure for running the current Corpus development
product locally. Corpus backend and frontend run in Docker, the primary Corpus
model is explicitly selectable between host Ollama and OpenAI, and the RouteDeck
Agent Design Studio runs separately with Vite. ToolRouter retains its separate
host-Ollama configuration.

The Compose `notebook` service on port `8771` is stale. The isolated R1 Studio
under `mockruns/corpus-r1` on port `8783` is also stale. Neither is the current
Agent Design Studio.

## Runtime Topology

| Process | Location | URL | Required |
| --- | --- | --- | --- |
| Ollama | Windows host | `http://127.0.0.1:11434` | Required for the Ollama primary provider and current ToolRouter paths |
| OpenAI API | Remote | `https://api.openai.com/v1` | Required only when the primary or evaluation provider is `openai` |
| Corpus backend | Docker Compose | `http://127.0.0.1:8099` | Yes |
| Corpus Source worker | Docker Compose, Huey | No HTTP surface | Yes for API-source processing |
| Corpus frontend | Docker Compose | `http://127.0.0.1:5199` | Yes |
| RouteDeck Agent Design Studio | Windows host, Vite | `http://127.0.0.1:8782` | When designing |
| Standalone Source Hub backend | Windows host, FastAPI | `http://127.0.0.1:8870` | Optional isolated capability proof |
| Standalone Source Hub frontend | Windows host, Vite | `http://127.0.0.1:5270` | Optional isolated capability proof |
| Standalone Agent Execution Studio | Windows host, ASGI | `http://127.0.0.1:8766` | Optional isolated capability proof |
| Agent Delivery Runtime API | Windows host, FastAPI/Huey | `http://127.0.0.1:8880` | Optional isolated delivery proof |
| Agent Delivery Runtime owner/public Web | Windows host, Vite preview | `http://127.0.0.1:5280` | Optional isolated delivery proof |
| RouteDeck Medusa agent API | Docker Compose from the RouteDeck checkout | `http://127.0.0.1:8098` | Required by Agent Delivery Runtime proof |
| Local Medusa target | Docker Compose from the RouteDeck checkout | `http://127.0.0.1:9100` | Required by real standalone Medusa proofs |

ToolRouter is embedded in the Corpus backend. It is not a separate service.
The backend reaches host Ollama through `host.docker.internal:11434`.

## Capability Ownership

Do not treat the API-related modules as interchangeable:

| Capability | Current owner | Corpus feature powered | Current integration state |
| --- | --- | --- | --- |
| OpenAPI ingestion, semantic graph/grouping, GRAG routing candidates, reviewed evalset generation | ToolRouter snapshot behind the Corpus API Source connector | Source Hub, API Source, and the ToolRouter portion of Evaluation | Integrated in the Corpus backend |
| Standalone source lifecycle, durable ToolRouter processing, encrypted connections, explicit real API execution, response-schema review and corrected OpenAPI schema lineage | `D:\Dev\AI Projects\source-hub-runtime`, using the sibling `api-execution-runtime` behind its executor adapter | Proven Source Hub/API Source behaviour plus foundations for future Evaluation, Sandbox and Operations | Proven separately; not imported into Corpus |
| Low-level authorized and validated HTTP execution | Private neutral `api-execution-runtime==0.1.0` snapshot under `corpus.integrations.api_execution._snapshot`; sibling remains read-only | Future Corpus execution adapter used by API Sources, Agent Builds, Sandbox, deployed Channels and Operations | Phase A dependency, provenance, import and compatibility foundation is integrated; no Corpus adapter or product path invokes it yet |
| Immutable Agent Build, Ollama intent, ToolRouter routing, capability-scoped API execution, durable trace, evaluation, and eligibility | `D:\Dev\AI Projects\agent-execution-runtime` | Future Agent Builder, Sandbox, Evaluation, and Operations execution kernel | Proven separately; not imported into or invoked by Corpus |
| Immutable deployment revisions, Web-channel activation/rollback, pinned public sessions, interaction evidence, and evaluation-candidate export | `D:\Dev\AI Projects\agent-delivery-runtime` | Future Channels/Web, Deployment, and deployed-agent Operations | Proven separately against RouteDeck Medusa and local Ollama; not imported into or invoked by Corpus |
| Product behavior, RouteDeck configuration, policies, operations, and surfaces | RouteDeck Agent Design Studio | Agent Designer | Studio exists; compiled parity is a separate gate |

The API execution runtime does not choose a tool and ToolRouter does not make
the HTTP call. The standalone Source Hub proves their source-level composition,
but it has no agent. A future Corpus path must explicitly connect an exact
Agent Build and RouteDeck policy decision to ToolRouter's operation identity,
allowed-operation enforcement and then one capability-scoped API runtime
request.

## Prerequisites

- Run commands from `D:\Dev\AI Projects\saastoagent-v0.1` in PowerShell.
- Docker Desktop must be running with its Linux container engine.
- The sibling RouteDeck source must exist at
  `D:\Dev\AI Projects\routedeck`; the Docker build consumes it read-only.
- Ollama must be installed on Windows.
- Node.js and pnpm must be installed for the Design Studio.

Check the tools and Docker configuration:

```powershell
docker version
docker compose version
docker compose config --quiet
ollama --version
node --version
pnpm --version
```

## First-Time Setup

Pull the exact models configured by Compose:

```powershell
ollama pull gemma4:latest
ollama pull qwen2.5-coder:7b
ollama list
```

Install the authoritative Design Studio dependencies:

```powershell
pnpm --dir docs/corpus-agent-design/workbench install
```

Corpus runtime data and generated development secrets are stored under the
ignored `.runtime/` directory. Do not delete it during ordinary startup,
shutdown, or rebuilds.

## Start the Complete Development Environment

### 1. Start Ollama on the host

In the first PowerShell terminal:

```powershell
ollama serve
```

If the Ollama desktop application is already serving, a second server may say
port `11434` is in use. Verify the existing server instead:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
ollama list
```

Both `gemma4:latest` and `qwen2.5-coder:7b` must be present for the current
ToolRouter paths. Corpus fails visibly when the explicitly selected primary
provider or model is unavailable; it does not select the other provider or
return synthetic success.

### 2. Start Corpus in Docker

In the second PowerShell terminal:

```powershell
docker compose up --build -d backend source-worker frontend
docker compose ps
```

Specifying `backend source-worker frontend` is intentional: it includes the
durable API-source consumer and excludes the stale Compose
`notebook` service. For an ordinary restart when no image dependency changed:

```powershell
docker compose up -d backend source-worker frontend
```

### 3. Start the authoritative Agent Design Studio

In the third PowerShell terminal:

```powershell
pnpm --dir docs/corpus-agent-design/workbench dev --host 0.0.0.0 --port 8782 --strictPort
```

Open `http://127.0.0.1:8782/`. The page title is
`RouteDeck Agent Design Studio · Corpus`, and its authoritative autosaved state
is `docs/corpus-agent-design/workbench/design-state.json`.

## Smoke Checks

```powershell
(Invoke-WebRequest http://127.0.0.1:8099/healthz -UseBasicParsing).StatusCode
(Invoke-WebRequest http://127.0.0.1:8099/readyz -UseBasicParsing).StatusCode
(Invoke-WebRequest http://127.0.0.1:5199/ -UseBasicParsing).StatusCode
(Invoke-WebRequest http://127.0.0.1:8782/ -UseBasicParsing).StatusCode
```

Each started service should return `200`. Open Corpus at
`http://127.0.0.1:5199/`, readiness at `http://127.0.0.1:8099/readyz`, and the
Agent Design Studio at `http://127.0.0.1:8782/`.

## Isolated Capability Proofs

These checks are not additional required Corpus services. Run them when
validating the module boundary they own.

### Standalone Source Hub and API Source suite

Run this suite from `D:\Dev\AI Projects\source-hub-runtime`. It is optional and
does not need to be running for the current Corpus Docker product.

First-time setup with Python 3.11 and Node.js:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[testing]"
.\.venv\Scripts\python.exe -m pip install -e "D:\Dev\AI Projects\api-execution-runtime"
npm --prefix frontend install
```

Generate and retain a 32-byte master key plus a 32-byte signing secret for the
chosen runtime directory. In both backend and worker terminals:

```powershell
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
$masterBytes = New-Object byte[] 32
$rng.GetBytes($masterBytes)
$rng.Dispose()
$masterKey = [Convert]::ToBase64String($masterBytes)
$signingSecret = '<choose-an-operator-secret-of-at-least-32-characters>'

$env:SOURCE_HUB_RUNTIME_ROOT='D:\Dev\AI Projects\source-hub-runtime\.runtime'
$env:SOURCE_HUB_MASTER_KEY=$masterKey
$env:SOURCE_HUB_SIGNING_SECRET=$signingSecret
```

Store both values in your local operator secret store and set them independently
in the worker and backend terminals; never commit them. Reuse the same master
key whenever opening this runtime directory because a different key cannot
decrypt its existing credentials.
Enter the exact `$signingSecret` value in the standalone frontend's **Proof
bootstrap secret** field. It issues only a local signed test session and is not
Corpus authentication.

Start the durable worker:

```powershell
.\.venv\Scripts\huey_consumer.exe source_hub.worker.huey -w 2
```

Start the backend in a second terminal with the same environment values:

```powershell
.\.venv\Scripts\uvicorn.exe source_hub.host.app:app --host 127.0.0.1 --port 8870
```

Start the frontend in a third terminal:

```powershell
npm --prefix frontend run dev -- --host 127.0.0.1 --port 5270
```

Smoke checks:

```powershell
(Invoke-WebRequest http://127.0.0.1:8870/healthz -UseBasicParsing).StatusCode
(Invoke-WebRequest http://127.0.0.1:8870/readyz -UseBasicParsing).StatusCode
(Invoke-WebRequest http://127.0.0.1:5270/ -UseBasicParsing).StatusCode
```

The exact setup, master-key warning, real Medusa prerequisite and current proof
counts are owned by `D:\Dev\AI Projects\source-hub-runtime\RUNBOOK.md`.
Coverage and adoption boundaries are owned by
`docs/standalone-source-hub-integration.md` in this repository and
`D:\Dev\AI Projects\source-hub-runtime\docs\CORPUS_INTEGRATION.md` in the
standalone repository.

This suite proves direct source-level routing and execution. It does not prove
Agent Designer, an Agent Build, Sandbox, deployment eligibility, a public Web
channel or deployed-agent Operations.

### ToolRouter through the Corpus API Source connector

Focused deterministic gates, run from the Corpus root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\integrations\toolrouter -q
.\.venv\Scripts\python.exe -m pytest backend\tests\sources -q
```

For real product evidence, keep Corpus and Ollama running, open
`http://127.0.0.1:5199/sources` as a local owner, then:

1. Upload a real OpenAPI JSON or YAML collection and build the graph.
2. Confirm endpoint, graph-node, graph-edge, and card counts are shown.
3. Run a natural-language retrieval and inspect the explicit decision, reason,
   ranking, and trace.
4. Generate a one-case evalset and confirm accepted/quarantined counts, exact
   generator/reviewer identities, and token evidence.
5. Reload and confirm the owner-scoped Source and artifacts remain available.

This proves API Source ingestion, semantic graph/index construction, GRAG
retrieval, and independently reviewed candidate generation. It does not prove
real API execution, an agent choosing the operation, or human-gold quality.

### RouteDeck Agent Design Studio

The Studio is independently runnable at `http://127.0.0.1:8782/` and its local
contract suite is:

```powershell
pnpm --dir docs/corpus-agent-design/workbench test
```

The separate compiled-design mapping gate is:

```powershell
.\.venv\Scripts\python.exe scripts\check_agent_design_parity.py
```

Treat these as two claims. A green Studio suite proves its product-semantic
editor state; only a green parity command proves that accepted design maps to
the current RouteDeck contracts. If parity crashes or reports drift, Agent
Designer integration is blocked even when the Studio UI itself works.

### Isolated Lounge product journeys

Run all Studio-owned Lounge product journeys from the Corpus repository:

```powershell
.\.venv\Scripts\python.exe scripts\run_lounge_product_journeys.py
```

Run one journey or use a visible browser when diagnosing a rendered failure:

```powershell
.\.venv\Scripts\python.exe scripts\run_lounge_product_journeys.py --journey lounge-journey-password-reset
.\.venv\Scripts\python.exe scripts\run_lounge_product_journeys.py --headed
```

The runner starts disposable Corpus backends on `8109` and `8110`, frontends
on `5209` and `5210`, and fresh owned SQLite databases. It uses official
Playwright Chromium, Mail.tm public mailboxes, and the configured real Gmail
SMTP adapter. Results, sanitized transcripts, screenshots, and traces are
written under `.runtime/evaluations/<run-id>/`; isolated processes and
databases are removed afterward. Failures remain failed artifacts.

Prerequisites are the backend virtual environment, Playwright Chromium, valid
ignored mail configuration, and internet access to Mail.tm and the configured
SMTP service. This is evaluation infrastructure, not an ordinary Corpus
startup dependency.

### Standalone Agent Execution Runtime

Run from `D:\Dev\AI Projects\agent-execution-runtime`. This suite is optional
for ordinary Corpus startup and is not a Corpus service.

Prerequisites:

- local Ollama at `http://127.0.0.1:11434` with `gemma4:latest` and
  `qwen2.5-coder:7b`;
- the configured local Medusa proof instance at
  `http://127.0.0.1:9100/health`;
- the standalone repository's `.venv` and documented, hash-pinned local
  ToolRouter/API Runtime references.

Verify prerequisites:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
(Invoke-WebRequest http://127.0.0.1:9100/health -UseBasicParsing).StatusCode
```

Start the acceptance dependency and Studio in separate PowerShell terminals:

```powershell
cd 'D:\Dev\AI Projects\agent-execution-runtime'
.\scripts\run_acceptance_api.ps1
```

```powershell
cd 'D:\Dev\AI Projects\agent-execution-runtime'
.\scripts\run_medusa_studio.ps1
```

Open `http://127.0.0.1:8766/`; readiness is
`http://127.0.0.1:8766/readyz`. The acceptance API uses ports `9200` and `9201`.
The explicit invalid-credential lane is separate:

```powershell
.\scripts\run_invalid_credential_studio.ps1
```

Its Studio URL is `http://127.0.0.1:8767/`.

Run every standalone machine gate:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q src demo acceptance scripts tests
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts\build_proof_manifest.py
.\.venv\Scripts\python.exe scripts\build_assembly_proof.py
.\.venv\Scripts\python.exe scripts\check_behavior_coverage.py
```

The proof manifest validates recorded real runs; it does not generate a fresh
browser run. To prove the interactive path personally, use Build Assembly in
the running Studio, review the operation catalogue, explicitly authorize the
intended writes, create the immutable build, open Sandbox, interact, inspect
the model/routing/API timeline, promote the run to an eval case, run it, and
inspect eligibility.

Claim limits:

- this proves the isolated execution/evidence kernel, not a current Corpus
  integration, RouteDeck compilation, deployment, or public channel;
- `model.decision` chooses direct response versus API search requests;
  ToolRouter ranks operations and the immutable build grants authority;
- real `GetProducts` currently returns HTTP 200 but fails the approved response
  schema, so that run is correctly displayed as schema drift rather than API
  success;
- local ToolRouter and API Runtime references remain development-only.

Architecture and future integration are documented in
`architecture/components/standalone-agent-execution-runtime-reference.md`.
The standalone repository owns the detailed coverage matrix in
`docs/corpus-behavior-coverage.md` and proof semantics in
`test_index/README.md`.

### Standalone Agent Delivery Runtime

Run from `D:\Dev\AI Projects\agent-delivery-runtime`. This suite is optional
for ordinary Corpus startup and is not a Corpus service. It currently proves
delivery of the RouteDeck Medusa example, not delivery of a Corpus-built agent.

Prerequisites:

- Docker Desktop with the Linux engine running;
- local Ollama at `http://127.0.0.1:11434` with `qwen3.5:4b`;
- the provisioned RouteDeck Medusa stack from
  `D:\Dev\AI Projects\routedeck`;
- the standalone repository's Python 3.11 environment and built `web/dist`.

Start the RouteDeck Medusa dependency from the RouteDeck checkout. `Provision`
is first-time setup; ordinary restarts use only `Up`:

```powershell
cd 'D:\Dev\AI Projects\routedeck'
powershell -NoProfile -ExecutionPolicy Bypass -File .\examples\medusa-agent\scripts\demo-stack.ps1 -Action Provision
powershell -NoProfile -ExecutionPolicy Bypass -File .\examples\medusa-agent\scripts\demo-stack.ps1 -Action Up -Services all
```

Build the trusted local bundle when it is missing or the verified RouteDeck
source changed, then start Delivery:

```powershell
cd 'D:\Dev\AI Projects\agent-delivery-runtime'
.\.venv\Scripts\python.exe .\scripts\build_medusa_bundle.py --routedeck-root 'D:\Dev\AI Projects\routedeck' --output '.\.runtime\proof\medusa-bundle.json'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-local.ps1 -RouteDeckRoot 'D:\Dev\AI Projects\routedeck'
```

The launcher creates `.runtime/owner-token.txt`. Copy it without printing it,
then unlock the local owner Studio:

```powershell
Get-Content '.\.runtime\owner-token.txt' -Raw | Set-Clipboard
```

Smoke checks:

```powershell
Invoke-RestMethod http://127.0.0.1:8880/readyz
(Invoke-WebRequest http://127.0.0.1:5280/ -UseBasicParsing).StatusCode
(Invoke-WebRequest http://127.0.0.1:5280/w/medusa-buyer -UseBasicParsing).StatusCode
```

Readiness must report persistence, worker, and active runtime ready. Owner
Studio is `http://127.0.0.1:5280/`; the public proof channel is
`http://127.0.0.1:5280/w/medusa-buyer`.

Stop only Delivery-owned processes, then optionally stop its RouteDeck Medusa
dependency. `Down` retains the protected Medusa volumes; never use `Reset` for
ordinary shutdown:

```powershell
cd 'D:\Dev\AI Projects\agent-delivery-runtime'
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\stop-local.ps1

cd 'D:\Dev\AI Projects\routedeck'
powershell -NoProfile -ExecutionPolicy Bypass -File .\examples\medusa-agent\scripts\demo-stack.ps1 -Action Down
```

Do not stop the shared Ollama server while Corpus or another local module needs
it. The exact ownership map, adoption gates, and claim limits are documented in
`docs/standalone-agent-delivery-runtime-integration.md` and in the standalone
repository's `docs/INTEGRATION.md`.

## Logs and Diagnosis

```powershell
docker compose ps
docker compose logs --tail 200 backend
docker compose logs --tail 200 frontend
docker compose logs -f backend
```

Diagnose failures in this order:

1. If Docker commands fail, start Docker Desktop and confirm `docker version`.
2. If the backend is unhealthy or not ready, inspect `CORPUS_MODEL_PROVIDER`.
   For `ollama`, confirm its API and exact model; for `openai`, confirm the key
   and exact model. Then inspect backend logs.
3. If the frontend is not running, inspect `docker compose ps`; it waits for
   the backend health check to pass.
4. If the Studio refuses to start, another process owns port `8782` or its
   dependencies are missing. Keep `--strictPort`; do not silently move the
   authoritative Studio to another port.
5. If the Docker build cannot find RouteDeck, verify its exact sibling path.
   Do not copy RouteDeck behavior into Corpus as a workaround.
6. If backend import fails because an `Operation` lacks `allowed_sources`, stop.
   This is Studio/Corpus-to-RouteDeck contract drift, not a Docker problem.
   Map each affected operation to its legal agent, surface, or route invocation
   sources and pass the parity gate; do not assign a permissive default merely
   to make the container start.

## Rebuild, Restart, and Stop

After backend, frontend, Dockerfile, or sibling RouteDeck source changes:

```powershell
docker compose up --build -d backend source-worker frontend
```

Restart one service with `docker compose restart backend` or
`docker compose restart frontend`.

Stop Corpus without deleting runtime data:

```powershell
docker compose stop frontend backend
```

Stop the Studio with `Ctrl+C` in its terminal. Stop `ollama serve` with
`Ctrl+C` only when no other local application needs Ollama.

`docker compose down` also removes the Compose network but retains the
repository-mounted `.runtime/` data. Never remove `.runtime/` as routine
cleanup: it contains local accounts, conversations, source artifacts,
databases, and persistent development secrets.

## Runtime Configuration

The primary and evaluation providers are independently selected in ignored
`.env.local` with `CORPUS_MODEL_PROVIDER` and `CORPUS_EVAL_PROVIDER`. Each must
be `ollama` or `openai`. Model names use `OLLAMA_MODEL`,
`CORPUS_OPENAI_MODEL`, `CORPUS_EVAL_TESTER_MODEL`, and
`CORPUS_EVAL_JUDGE_MODEL`; `OPENAI_API_KEY` is required for an OpenAI
selection. A failed provider never invokes the other one.

Compose continues to provide these container-specific Ollama defaults:

- Ollama endpoint: `http://host.docker.internal:11434`
- primary and ToolRouter generator model: `gemma4:latest`
- ToolRouter reviewer model: `qwen2.5-coder:7b`

Explicit overrides are available through `CORPUS_DOCKER_OLLAMA_URL`,
`CORPUS_DOCKER_PRIMARY_MODEL`, `CORPUS_DOCKER_GENERATOR_MODEL`, and
`CORPUS_DOCKER_REVIEWER_MODEL` before the Compose start command. Verify the
exact endpoint and model before using an override.

This runbook describes a local development environment, not a production
deployment.
