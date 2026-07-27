# 2026-07-27 Docker Development Stack

## Delivered

- One local `docker compose up --build` command for backend, frontend, and the
  design notebook.
- Filtered local Corpus/RouteDeck build context; no sibling ToolRouter runtime
  dependency.
- Persistent `.runtime` bind for RouteDeck, auth, Source artifacts, and stable
  development secrets.
- Explicit external host Ollama boundary for primary chat and ToolRouter
  generator/reviewer clients.
- Backend migration/secret entrypoint, Vite service proxy, guarded notebook
  container bind, health checks, and loopback-only published ports.
- Structure explorer entries for every implemented Docker/runtime file with
  responsibility and exclusion explanations.

## Runtime Proof

Command: `docker compose up --build -d`

- Backend: healthy, `http://127.0.0.1:8099/readyz` -> 200
- Frontend: healthy, `http://127.0.0.1:5199/` -> 200
- Notebook: healthy, `http://127.0.0.1:8771/#structure` -> 200
- Backend/notebook image: 2.39 GB (CPU PyTorch)
- Frontend image: 1.14 GB

The authenticated Sources UI uploaded the real Ory Kratos `api.yaml` from the
sibling ToolRouter evidence repository. It produced 56 endpoints, 477 nodes,
876 edges, and 477 cards. Retrieval returned `ASK_DISAMBIGUATE` with
`low_score_margin`. The real host-Ollama evalset run accepted 1/1, quarantined
zero, and recorded 3,823 offline tokens. Backend recreation retained the
Source, artifacts, and retrieval evidence.

## Automated Proof

- Backend host lane: 59 passed; one upstream Starlette deprecation warning.
- Frontend image: 19 passed; typecheck and production build passed; only the
  existing non-failing Vite chunk-size advisory.
- Repository unittest suite: 15 passed.
- Design notebook: 15 features, 53 nodes, 146 edges, zero missing targets.
- `docker compose config --quiet`, Python dependency check, and context
  coverage advisory passed.
- The isolated backend image passes 57 environment-independent tests. Two live
  tests deliberately use `127.0.0.1` for the host Ollama reference and are run
  on the host; the actual container boundary is proven by the UI pipeline.

## Evidence

- `C:\Users\ragha\.codex\visualizations\2026\07\22\019f895d-bb32-7f31-94ab-df128085c19c\corpus-docker-toolrouter-e2e.png`
- `C:\Users\ragha\.codex\visualizations\2026\07\22\019f895d-bb32-7f31-94ab-df128085c19c\corpus-docker-structure-explorer.png`

No Git operation was performed.
