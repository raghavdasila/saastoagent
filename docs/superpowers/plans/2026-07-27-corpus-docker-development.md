# Corpus Docker Development Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Start the backend, frontend, and design notebook with one development-mode Docker Compose command while retaining the embedded ToolRouter pipeline and host Ollama boundary.

**Architecture:** One multi-target Dockerfile builds separate Python backend and Node frontend development images. Compose runs backend, frontend, and notebook services, mounts source for hot reload, persists runtime state under `.runtime`, and connects ToolRouter/Ollama clients to `host.docker.internal:11434`.

**Tech Stack:** Docker Desktop Linux engine, Docker Compose v5, Python 3.11, Node 22, pnpm 11.9, FastAPI/Uvicorn, Vite, SQLite, embedded ToolRouter, host Ollama.

## Global Constraints

- No Git operations.
- ToolRouter remains embedded in the backend and owns its settings.
- The sibling OpenAPI ToolRouter checkout is not mounted or copied.
- RouteDeck is supplied only through the filtered parent Docker build context.
- Product dependency failures remain visible; no model or data fallback.
- Published ports bind to host loopback only.
- Runtime state persists under the repository `.runtime` directory.

---

### Task 1: Container images and build contexts

**Files:**
- Create: `Dockerfile`
- Create: `.dockerignore`

**Interfaces:**
- Consumes: exact Corpus and RouteDeck files admitted by `Dockerfile.dockerignore` from the parent context.
- Produces: `backend-dev` and `frontend-dev` image targets.

- [x] Create a Python 3.11 backend target that installs RouteDeck and Corpus, includes migrations/notebook files, pins CPU PyTorch, and caches the pinned MiniLM revision.
- [x] Create a Node 22 frontend target that installs/builds linked RouteDeck packages and installs Corpus with its frozen lockfile.
- [x] Exclude host virtual environments, node modules, runtime data, caches, recordings, benchmark evidence, and unrelated sibling projects from the build context.
- [x] Build both targets and resolve only actual dependency/build failures.

### Task 2: Explicit development startup configuration

**Files:**
- Create: `scripts/docker-backend-entrypoint.py`
- Modify: `frontend/vite.config.ts`
- Modify: `scripts/feature_behavior_notebook.py`

**Interfaces:**
- Consumes: `/data`, process environment, requested backend command, `CORPUS_BACKEND_PROXY_URL`, and explicit notebook container-bind flag.
- Produces: stable development secrets, idempotent migrations, configurable Vite proxying, and guarded container notebook binding.

- [x] Implement an entrypoint that creates or reloads stable encryption/reset/verification secrets at `/data/docker-runtime-secrets.env`, exports missing values, runs `python -m corpus.auth.migrations`, and `exec`s the requested Uvicorn command.
- [x] Make Vite use `CORPUS_BACKEND_PROXY_URL` when supplied and retain `http://127.0.0.1:8099` for direct host use.
- [x] Add an explicit `--allow-container-bind` notebook argument that permits only `0.0.0.0`; preserve the loopback-only default otherwise.
- [x] Exercise entrypoint secret reuse, Vite configuration loading, and notebook argument validation through focused commands.

### Task 3: Compose orchestration

**Files:**
- Create: `compose.yaml`

**Interfaces:**
- Consumes: Dockerfile targets, optional `.env.local`, host Ollama, `.runtime`, and repository source directories.
- Produces: `backend`, `frontend`, and `notebook` services on ports 8099, 5199, and 8771.

- [x] Define the backend service with container-specific database/source paths, ToolRouter-owned model values, host Ollama URLs, loopback port publishing, source mounts, a readiness health check, and the backend entrypoint.
- [x] Define the frontend service with its internal backend proxy URL, source hot-reload mount, loopback port publishing, and backend-health dependency.
- [x] Define the notebook service using the backend image, explicit container bind, writable docs mount, scripts mount, and loopback port publishing.
- [x] Validate the fully resolved Compose model with `docker compose config`.

### Task 4: Runtime and product-path verification

**Files:**
- Modify only if a real runtime defect is found in the new container boundary.

**Interfaces:**
- Consumes: running Compose services and host Ollama models `gemma4:latest` and `qwen2.5-coder:7b`.
- Produces: healthy local services and real ToolRouter UI evidence.

- [x] Start Docker Desktop's Linux engine locally and wait for `docker version` to report a server.
- [x] Run `docker compose up --build -d` and inspect service health/logs.
- [x] Verify HTTP 200 at `/readyz`, the frontend root, and the Structure notebook.
- [x] Run backend tests/dependency checks and frontend tests/typecheck/build against the final source or built images.
- [x] Through the running browser UI, authenticate, upload a real OpenAPI YAML, complete graph/index creation, run retrieval, generate a reviewed evalset through host Ollama, reload, and confirm persistence.
- [x] Capture screenshots of the completed Sources pipeline and Structure explorer.
- [x] Restart the backend container and confirm persisted Source/runtime evidence remains.

### Task 5: Runtime documentation and context closeout

**Files:**
- Create: `docs/docker-development.md`
- Modify: `README.md`
- Modify: `architecture/code-map.md`
- Modify: `architecture/components/corpus-routedeck-boundary.md`
- Modify: `architecture/components/toolrouter-source-integration.md`
- Modify: `SYSTEM_FLOW_INDEX.md`
- Modify: `test_index/README.md`
- Modify: `context.md`
- Create: `logs/20260727_docker_development_stack.md`
- Create: `context_checkpoints/2026-07-27-docker-development-stack.md`

**Interfaces:**
- Consumes: exact verified commands, URLs, Compose health, pipeline metrics, screenshots, and failure observations.
- Produces: one authoritative local Docker procedure plus current architecture/test/restart records.

- [x] Document Docker Desktop and host Ollama prerequisites, `docker compose up --build`, URLs, logs, rebuilds, shutdown, persistence, and failure diagnosis.
- [x] Record the Compose runtime owner without changing Source/ToolRouter product ownership.
- [x] Record exact automated and UI evidence with screenshot paths.
- [x] Run `python scripts/check_doc_coverage.py` and the applicable notebook validators.
- [x] Self-review changed documentation for stale multi-window startup instructions and unsupported production claims.
