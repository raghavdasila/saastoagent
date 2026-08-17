# Corpus

Corpus is a chat-first agentic app for designing, building, evaluating,
deploying, operating, and improving agents. RouteDeck supplies the legal
interaction topology and scopes the Corpus agent to the prompt, context, tools,
operations, and surfaces of the active node.

The current development product spans owner identity, Workspace, Sources,
Agents, Designer, Builder, Sandbox, Evaluation, Channels, Deployment, hosted
Web sessions, and Operations. Its accepted ecommerce path uses real OpenAPI
ingestion, persisted ToolRouter evidence, reviewed API execution, immutable
build/deployment lineage, and explicit write review. That path does not prove
every external API, exhaustive feature breadth, multi-host scaling, or an SLA;
see `context.md` for current evidence and claim boundaries.

## Start Here

- `AGENTIC_CODING_GUIDE.md` - start, completion, and closeout sequence
- `critical_prompt.md` - product north star and non-negotiable boundaries
- `context.md` - concise current restart state
- `docs/local-runtime-runbook.md` - authoritative fresh-checkout, Docker,
  Ollama/OpenAI, and Agent Design Studio startup and diagnosis
- `docs/corpus-product-definition.md` - locked layout and feature set
- `docs/corpus-behavior-reference.md` - verified legacy behavior reference
- `docs/toolrouter-integration-requirements.md` - implemented Sources/API and
  ToolRouter integration contract plus exact evidence
- `architecture/components/toolrouter-source-integration.md` - every folder,
  file, boundary, flow, and failure owner

## Local Setup

The primary development path runs Corpus backend, application worker, and
frontend in Docker, with the authoritative Agent Design Studio separately.
Generative models may run through host Ollama or OpenAI. A complete image build
also requires the exact sibling RouteDeck, Agent Execution Runtime, and Agent
Delivery Runtime source directories described in the runbook.

After cloning Corpus, authenticated organization members can create those
exact pinned sibling checkouts with:

```powershell
.\scripts\clone-development-dependencies.ps1
```

Default Ollama lane:

```powershell
ollama pull gemma4:latest
ollama pull qwen2.5-coder:7b
docker compose up --build -d backend source-worker frontend
pnpm --dir docs/corpus-agent-design/workbench dev --host 0.0.0.0 --port 8782 --strictPort
```

OpenAI lane, for systems that cannot run the local Gemma/Qwen models:

```powershell
# First create ignored .env.local exactly as documented in the runbook.
docker compose --env-file .env.local up --build -d backend source-worker frontend
pnpm --dir docs/corpus-agent-design/workbench dev --host 0.0.0.0 --port 8782 --strictPort
```

Smoke URLs:

- Product: `http://127.0.0.1:5199/`
- Backend readiness: `http://127.0.0.1:8099/readyz`
- RouteDeck Agent Design Studio: `http://127.0.0.1:8782/`

ToolRouter runs inside the backend container. It uses the explicitly selected
Ollama or OpenAI generation/review provider and always retains the pinned local
CPU MiniLM embedding path. Runtime state persists under `.runtime`.
See `docs/local-runtime-runbook.md` for prerequisites, exact startup order,
health checks, logs, rebuilds, shutdown, and failure diagnosis. The Compose
`notebook` service on port `8771` is stale and is deliberately excluded.

The direct-host setup remains available for focused development without
containers.

Verified versions on 2026-07-23:

- Python 3.11.9
- Node.js 24.3.0 and pnpm 11.7.0
- Ollama 0.21.0 with `gemma4:latest` and `qwen2.5-coder:7b`
- RouteDeck 0.1.0 from the sibling `..\routedeck` checkout
- FastAPI 0.136.3, Uvicorn 0.48.0, LangGraph 1.2.9, LangChain 1.3.13,
  React 19.2.7, Vite 8.1.4, and TypeScript 7.0.2

```powershell
ollama pull gemma4:latest
ollama pull qwen2.5-coder:7b
.\scripts\init-local.ps1
```

The setup creates an ignored `.venv`, `.env.local`, and SQLite database path.
It installs the approved local RouteDeck source and locked frontend
dependencies, pins the ToolRouter Python dependency versions, and caches the
exact MiniLM revision used by retrieval. It fails if RouteDeck, Ollama,
`gemma4:latest`, `qwen2.5-coder:7b`, or the pinned embedding model is
unavailable.

Direct-host mode starts the two product processes in separate terminals:

```powershell
.\scripts\run-backend.ps1
.\scripts\run-frontend.ps1
```

Smoke URL: `http://127.0.0.1:5199/`. Sign in or create an owner, then use
`http://127.0.0.1:5199/sources` through the Home **Open Sources debug** action.

Backend health/readiness: `http://127.0.0.1:8099/healthz` and
`http://127.0.0.1:8099/readyz`.

## Validation

With both processes running, exercise the real guest/model path:

```powershell
.\.venv\Scripts\python.exe scripts\smoke_live.py
```

Focused suites:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
pnpm --dir frontend typecheck
pnpm --dir frontend test
pnpm --dir frontend build
python -m unittest discover -v
python scripts/validate_design_notebook.py
python scripts/check_doc_coverage.py
```

The ignored `benchmark/saastoagent-v0.1/` remains read-only visual/behavior
evidence. The sibling ToolRouter checkout is also not a runtime dependency;
Corpus carries an exact private namespaced snapshot with per-file hashes and a
replaceable facade. See `test_index/README.md` for exact claim boundaries.
