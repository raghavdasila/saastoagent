# Corpus Local Runtime Runbook

This is the authoritative procedure for running the current Corpus development
product locally. Corpus backend and frontend run in Docker, Ollama runs on the
Windows host, and the RouteDeck Agent Design Studio runs separately with Vite.

The Compose `notebook` service on port `8771` is stale. The isolated R1 Studio
under `mockruns/corpus-r1` on port `8783` is also stale. Neither is the current
Agent Design Studio.

## Runtime Topology

| Process | Location | URL | Required |
| --- | --- | --- | --- |
| Ollama | Windows host | `http://127.0.0.1:11434` | Yes |
| Corpus backend | Docker Compose | `http://127.0.0.1:8099` | Yes |
| Corpus frontend | Docker Compose | `http://127.0.0.1:5199` | Yes |
| RouteDeck Agent Design Studio | Windows host, Vite | `http://127.0.0.1:8782` | When designing |

ToolRouter is embedded in the Corpus backend. It is not a separate service.
The backend reaches host Ollama through `host.docker.internal:11434`.

## Capability Ownership

Do not treat the API-related modules as interchangeable:

| Capability | Current owner | Corpus feature powered | Current integration state |
| --- | --- | --- | --- |
| OpenAPI ingestion, semantic graph/grouping, GRAG routing candidates, reviewed evalset generation | ToolRouter snapshot behind the Corpus API Source connector | Source Hub, API Source, and the ToolRouter portion of Evaluation | Integrated in the Corpus backend |
| One authorized, validated HTTP operation; concurrency/isolation; redacted execution trace | Standalone `D:\Dev\AI Projects\api-execution-runtime` | Future Agent Builder runtime used by Sandbox, deployed Channels, and Operations | Proven separately; not imported into Corpus |
| Live-response drift review and immutable effective OpenAPI revisions | Contract Revision Studio in the standalone API runtime | Future API Source contract maintenance supporting safe Sandbox/deployed execution | Proven separately; not imported into Corpus |
| Product behavior, RouteDeck configuration, policies, operations, and surfaces | RouteDeck Agent Design Studio | Agent Designer | Studio exists; compiled parity is a separate gate |

The API execution runtime does not choose a tool and ToolRouter does not make
the HTTP call. A future agent path must explicitly connect RouteDeck/agent
selection to ToolRouter's operation identity and then to one capability-scoped
API runtime request.

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

Both `gemma4:latest` and `qwen2.5-coder:7b` must be present. Corpus fails
visibly when Ollama or a configured model is unavailable; it does not select a
fallback model or return synthetic success.

### 2. Start Corpus in Docker

In the second PowerShell terminal:

```powershell
docker compose up --build -d backend frontend
docker compose ps
```

Specifying `backend frontend` is intentional: it excludes the stale Compose
`notebook` service. For an ordinary restart when no image dependency changed:

```powershell
docker compose up -d backend frontend
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

### API execution and contract revision

Run from `D:\Dev\AI Projects\api-execution-runtime`. The exact standalone
commands, Medusa prerequisites, and proof limits are owned by that repository's
`README.md` and `test_index/README.md`.

Core contracts:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Contract Revision Studio smoke URL after starting its documented server:
`http://127.0.0.1:8765/`. The target Medusa smoke URL is
`http://127.0.0.1:9100/health`.

This proves the execution boundary intended for Sandbox, deployed Web agents,
and Operations traces. It does not prove that Corpus currently has an Agent
Builder or an agent-to-runtime integration.

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

## Logs and Diagnosis

```powershell
docker compose ps
docker compose logs --tail 200 backend
docker compose logs --tail 200 frontend
docker compose logs -f backend
```

Diagnose failures in this order:

1. If Docker commands fail, start Docker Desktop and confirm `docker version`.
2. If the backend is unhealthy or not ready, confirm the Ollama API responds,
   confirm both exact models with `ollama list`, then inspect backend logs.
3. If the frontend is not running, inspect `docker compose ps`; it waits for
   the backend health check to pass.
4. If the Studio refuses to start, another process owns port `8782` or its
   dependencies are missing. Keep `--strictPort`; do not silently move the
   authoritative Studio to another port.
5. If the Docker build cannot find RouteDeck, verify its exact sibling path.
   Do not copy RouteDeck behavior into Corpus as a workaround.

## Rebuild, Restart, and Stop

After backend, frontend, Dockerfile, or sibling RouteDeck source changes:

```powershell
docker compose up --build -d backend frontend
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

Compose defaults to:

- Ollama endpoint: `http://host.docker.internal:11434`
- primary and ToolRouter generator model: `gemma4:latest`
- ToolRouter reviewer model: `qwen2.5-coder:7b`

Explicit overrides are available through `CORPUS_DOCKER_OLLAMA_URL`,
`CORPUS_DOCKER_PRIMARY_MODEL`, `CORPUS_DOCKER_GENERATOR_MODEL`, and
`CORPUS_DOCKER_REVIEWER_MODEL` before the Compose start command. Verify the
exact endpoint and model before using an override.

This runbook describes a local development environment, not a production
deployment.
