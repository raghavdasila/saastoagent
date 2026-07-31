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
