# Corpus Docker Development Design

Date: 2026-07-27
Status: Approved and implemented

## Objective

Provide one repeatable local command that starts the complete current Corpus
development experience without requiring separate PowerShell windows for the
backend, frontend, and design notebook:

```powershell
docker compose up --build
```

The stack must preserve the existing Sources and ToolRouter boundaries, use the
host Ollama installation through an explicit URL, retain runtime data across
container recreation, support backend/frontend hot reload, and fail visibly
when a required dependency is unavailable.

## Approved Boundaries

- Docker Compose owns Corpus process orchestration only.
- Ollama remains outside the Compose stack. Local development uses
  `http://host.docker.internal:11434`; deployment may provide an API or a
  dedicated Ollama-compatible server through configuration.
- ToolRouter remains an embedded backend integration, not an independent
  container or HTTP service.
- The existing `ApiSourceEngine` boundary remains the replacement seam for a
  future standalone ToolRouter service.
- RouteDeck remains a sibling source dependency supplied through a filtered
  parent Docker build context. `Dockerfile.dockerignore` admits only the exact
  Corpus and RouteDeck files the images need; RouteDeck is not copied into
  Corpus source or fetched from an unpinned remote dependency.
- Corpus runtime data persists outside image layers.
- The setup is development-oriented. It favors hot reload and direct logs over
  a production web-server topology.

## Considered Approaches

### Separate Compose services (selected)

Run the backend, Vite frontend, and design notebook as separate services built
from one multi-target Dockerfile. This preserves independent lifecycle, logs,
health, and restart behavior while retaining one user command.

### One supervised container (rejected)

Running all processes under a supervisor would mix lifecycle and failure
semantics. A frontend or notebook restart would affect the backend, and one
container health check could not describe the three user-visible surfaces.

### Containerize only the product application (rejected)

Leaving the notebook on the host would retain a second manual command and fail
the stated usability objective.

## Service Architecture

```text
browser
  |-- 127.0.0.1:5199 -> frontend-dev -> http://backend:8099
  |-- 127.0.0.1:8099 -> backend-dev
  `-- 127.0.0.1:8771 -> design-notebook

backend-dev
  |-- /data/routedeck.sqlite
  |-- /data/corpus-auth.sqlite3
  |-- /data/sources/**
  |-- embedded ToolRouter + pinned MiniLM
  `-- http://host.docker.internal:11434 -> host Ollama
```

### Backend

- Use Python 3.11, matching `backend/pyproject.toml`.
- Install RouteDeck from the filtered sibling source with its declared FastAPI,
  LangGraph, persistence, and testing extras required by Corpus.
- Install Corpus in editable mode.
- Cache the pinned MiniLM revision during image build so container startup does
  not perform a silent network lookup.
- Run owner-auth migrations before Uvicorn starts.
- Run Uvicorn on `0.0.0.0:8099` with reload enabled and the backend source
  mounted into the container.
- Store RouteDeck SQLite, auth SQLite, and Source artifacts below `/data`.
- Publish the backend only on host loopback.

### Frontend

- Use Node 22 and the repository-pinned pnpm version.
- Build the linked RouteDeck core/react packages from the sibling build
  context.
- Install the Corpus frontend from its frozen lockfile.
- Run Vite on `0.0.0.0:5199` with source mounted for hot reload.
- Read the development proxy destination from configuration and default it to
  the Compose service URL `http://backend:8099` inside the container.
- Publish Vite only on host loopback.

### Design notebook

- Reuse the backend Python image rather than maintaining a third dependency
  image.
- Run `scripts/feature_behavior_notebook.py` on `0.0.0.0:8771`.
- Require an explicit container-bind flag for the non-loopback bind; preserve
  the current loopback-only default for direct host execution.
- Mount the notebook HTML and notes path so the global Save action continues to
  update the repository-owned Markdown file.
- Publish the notebook only on host loopback.

## ToolRouter Runtime

ToolRouter runs within the backend service through the existing ownership path:

```text
Sources
  -> API connector
    -> ApiSourceEngine
      -> ToolRouter bridge
        -> ToolRouter adapter/private snapshot
```

- OpenAPI parsing, graph construction, graph persistence, MiniLM indexing,
  retrieval, and evalset orchestration execute in the backend container.
- The pinned MiniLM embedding model runs on CPU inside the backend container.
- Normalized API documents, graph/index artifacts, retrieval evidence, and
  evalsets persist below `/data/sources`.
- Generator and reviewer requests use the ToolRouter-owned Ollama URL and model
  settings, pointed at the host Ollama service for local development.
- Compose supplies environment values but does not redefine ToolRouter defaults
  or move them into generic Sources configuration.
- The sibling `openapi-toolrouter-benchmark` checkout is not a build context,
  mount, or runtime dependency. Corpus uses its repository-contained,
  hash-manifested ToolRouter snapshot.

## Configuration And Secrets

- Container process environment overrides host-specific paths from
  `.env.local` with `/data` paths and container service URLs.
- Existing local secrets may be read from `.env.local` when present.
- A small backend entrypoint creates only missing development encryption/reset
  secrets in a file on the persistent runtime volume, then reuses them across
  container recreation.
- Secret generation is explicit setup behavior, not a fallback for failed
  authentication or model services.
- SMTP credentials remain optional external configuration; mail-dependent
  product behavior must still fail visibly when they are absent or invalid.
- No model, API, fixture, canned answer, alternate provider, or mock success is
  introduced.

## Persistence

Use a host bind mount from `.runtime/` to `/data` so evidence remains directly
inspectable from Windows and survives `docker compose down` and image rebuilds.
The Compose configuration must never write database or Source artifacts inside
an ephemeral image layer.

The notes document remains a separate bind-mounted repository file because it
is authored documentation, not runtime state.

## Startup And Failure Semantics

The expected command is:

```powershell
docker compose up --build
```

Expected startup order:

1. Build or reuse the backend/frontend development images.
2. Start the backend entrypoint, ensure persistent development secrets, and run
   migrations.
3. Start Uvicorn and expose backend health/readiness.
4. Start Vite and the notebook independently.
5. Surface all logs in the invoking terminal.

The backend readiness endpoint must remain unready when Ollama or another
required dependency is unavailable. Compose must not substitute a model,
fixture, or cached response. Container exits and health failures remain visible
in Compose status and logs.

Docker Desktop's Linux engine is a prerequisite. The implementation cannot
start it silently; documentation will identify this prerequisite and the
resulting connection error.

## Planned Files And Ownership

| File | Responsibility |
| --- | --- |
| `Dockerfile` | Multi-target backend and frontend development images. |
| `Dockerfile.dockerignore` | Restrict the parent context to exact Corpus and RouteDeck image inputs. |
| `.dockerignore` | Exclude local environments, runtime state, caches, evidence, and build outputs from a direct Corpus context. |
| `compose.yaml` | Orchestrate backend, frontend, notebook, loopback ports, health, mounts, and external Ollama URLs. |
| `scripts/docker-backend-entrypoint.py` | Create/reuse persistent development secrets, run migrations, and exec the requested backend command. |
| `frontend/vite.config.ts` | Accept an explicit backend proxy URL and container bind host without changing direct-host defaults. |
| `scripts/feature_behavior_notebook.py` | Permit an explicitly requested container bind while retaining loopback-only host defaults. |
| `docs/docker-development.md` | Own prerequisites, one-command use, URLs, logs, rebuild/reset procedures, and failure guidance. |
| Architecture/context/test owners | Record the new runtime topology and its validation meaning. |

## Verification

### Static and automated gates

- Validate `docker compose config`.
- Build every Compose target without relying on host `.venv` or
  `frontend/node_modules`.
- Run the backend suite in the backend image.
- Run frontend tests, typecheck, and build in the frontend image.
- Run repository notebook tests and design-notebook validation.
- Run dependency checks and context-architecture coverage.

### Runtime gates

- Start the complete stack locally with `docker compose up --build`.
- Confirm Compose health and exact process ownership.
- Confirm HTTP 200 from:
  - `http://127.0.0.1:8099/readyz`
  - `http://127.0.0.1:5199/`
  - `http://127.0.0.1:8771/#structure`
- Stop and restart the stack, then prove SQLite, Sources artifacts, and saved
  behavior notes persist.
- Prove an unavailable host Ollama produces an explicit readiness/product
  failure rather than a fallback success.

### Requested UI end-to-end smoke

Using the running Compose frontend and the real authenticated product path:

1. sign in or create the smoke owner;
2. open Sources;
3. upload a real OpenAPI YAML collection;
4. wait for normalization, graph construction, and MiniLM indexing;
5. run a retrieval query and inspect its decision/trace;
6. generate a real reviewed evalset through the configured host Ollama models;
7. reload and confirm the persisted Source/evidence remains;
8. inspect the Structure explorer's planned/implemented state.

Capture screenshots at the meaningful completed states, including the Sources
pipeline result and the updated Structure explorer. Screenshots are evidence of
the UI path; backend logs, persisted artifacts, and HTTP results remain the
integration proof.

## Completion Criteria

- A developer with Docker Desktop and the required host Ollama models can start
  all current Corpus surfaces with one command.
- Ordinary backend/frontend edits reload without manually restarting services.
- ToolRouter completes the real upload-to-graph-to-retrieval-to-evalset path
  inside the backend container.
- Runtime state and authored notes survive container recreation.
- Required dependency failures stay explicit.
- The documented commands, URLs, Compose health, automated gates, and UI
  screenshots all correspond to the same verified local run.
