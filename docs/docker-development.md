# Docker Development Runtime

The supported one-command local development runtime is Docker Compose. It
starts the Corpus backend, Vite frontend, and design notebook while keeping
Ollama on the Windows host and ToolRouter embedded inside the backend.

## Prerequisites

- Docker Desktop with the Linux container engine running.
- The sibling RouteDeck checkout at `D:\Dev\AI Projects\routedeck`.
- Ollama running on the host with `gemma4:latest` and
  `qwen2.5-coder:7b` installed.

The build uses the local Corpus and RouteDeck source trees. It does not copy or
mount the sibling `openapi-toolrouter-benchmark` checkout: Corpus runs its
repository-contained, hash-manifested ToolRouter snapshot.

## Start Everything

From `D:\Dev\AI Projects\saastoagent-v0.1`:

```powershell
docker compose up --build
```

For a detached terminal:

```powershell
docker compose up --build -d
docker compose logs -f
```

The local development URLs are:

- Corpus UI and Sources debug: `http://127.0.0.1:5199/`
- Backend health/readiness: `http://127.0.0.1:8099/healthz` and
  `http://127.0.0.1:8099/readyz`
- Design notebook Structure explorer: `http://127.0.0.1:8771/#structure`

All published ports bind to host loopback. Vite proxies product API requests to
the Compose backend service. Backend and frontend source directories are
mounted for development reload.

## ToolRouter And Ollama

ToolRouter is not a fourth container. The Sources API connector calls the
embedded `ToolRouterAdapter` in the backend container for OpenAPI parsing,
resource-first graph construction, MiniLM indexing, GRAG retrieval, and
reviewed evalset generation.

Compose points ToolRouter's generator/reviewer clients and the primary Corpus
chat client to `http://host.docker.internal:11434`. Override the external
endpoint or model names explicitly when needed:

```powershell
$env:CORPUS_DOCKER_OLLAMA_URL = 'http://host.docker.internal:11434'
$env:CORPUS_DOCKER_PRIMARY_MODEL = 'gemma4:latest'
$env:CORPUS_DOCKER_GENERATOR_MODEL = 'gemma4:latest'
$env:CORPUS_DOCKER_REVIEWER_MODEL = 'qwen2.5-coder:7b'
docker compose up --build
```

No alternate model, cached answer, fixture, or synthetic success is selected
when Ollama or a required model is unavailable. The request/readiness path
fails visibly and the backend logs retain the upstream error.

## Persistence And Secrets

RouteDeck SQLite, Corpus auth SQLite, generated development secrets, uploaded
Sources, graphs, indexes, retrieval evidence, and evalsets live under the
ignored repository `.runtime/` directory. They survive container recreation
and image rebuilds. The notebook's authored Markdown remains under `docs/`.

The backend entrypoint creates only missing development secrets in
`.runtime/docker-runtime-secrets.env`, reuses them thereafter, runs the auth
migration, and then replaces itself with Uvicorn. It does not recover from a
failed migration or dependency by choosing another path.

The backend gives Uvicorn five seconds for graceful shutdown inside Docker's
explicit ten-second stop grace. If an SSE subscriber or model task is still
active during recreation, Uvicorn cancels it before Docker's final kill so the
ASGI lifespan can close the RouteDeck runtime and release its instance lease.
This is local process-lifecycle configuration; it does not change RouteDeck's
lease, interruption, or restart-recovery semantics.

## Inspect And Stop

```powershell
docker compose ps
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f notebook
docker compose down
```

`docker compose down` stops the services but retains `.runtime`. To rebuild one
target after a dependency/Dockerfile change:

```powershell
docker compose build backend notebook
docker compose up -d backend notebook
```

Removing `.runtime` deletes local accounts, conversations, Sources artifacts,
and persistent development secrets. That is destructive and is not part of the
normal start/stop procedure.

## Failure Diagnosis

- Docker connection errors: start Docker Desktop's Linux engine, then rerun
  `docker version` and `docker compose up --build`.
- Backend not ready: inspect `docker compose logs backend`; verify host Ollama
  at `http://127.0.0.1:11434` and the two required model names with
  `ollama list`.
- Frontend waiting: `docker compose ps` will show whether its backend health
  dependency has become healthy.
- ToolRouter evalset failure: inspect the UI error and backend log. The
  configured external Ollama URL must include an explicit HTTP port.

This is a local development topology, not a production deployment definition.
