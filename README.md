# Corpus

Corpus is a chat-first agentic app for designing, building, evaluating,
deploying, operating, and improving agents. RouteDeck supplies the legal
interaction topology and scopes the Corpus agent to the prompt, context, tools,
operations, and surfaces of the active node.

The fresh-project framework, Corpus owner identity, Workspace, and the first
Sources connector are runnable locally. An authenticated owner can upload a
real OpenAPI collection, build a persisted resource-first semantic graph and
MiniLM index, inspect GRAG retrieval, and generate independently reviewed
evalset candidates through the local Gemma/Qwen factory. This is an
experimental debug path; Agent Designer, Sandbox, public Web deployment, and
Operations remain later work in the launch milestone.

## Start Here

- `AGENTIC_CODING_GUIDE.md` - start, completion, and closeout sequence
- `critical_prompt.md` - product north star and non-negotiable boundaries
- `context.md` - concise current restart state
- `docs/corpus-product-definition.md` - locked layout and feature set
- `docs/corpus-behavior-reference.md` - verified legacy behavior reference
- `docs/toolrouter-integration-requirements.md` - implemented Sources/API and
  ToolRouter integration contract plus exact evidence
- `architecture/components/toolrouter-source-integration.md` - every folder,
  file, boundary, flow, and failure owner

## Local Setup

The primary development path is one local Docker Compose command. Docker
Desktop's Linux engine, the sibling `..\routedeck` checkout, and host Ollama
with the two configured models are required:

```powershell
ollama pull gemma4:latest
ollama pull qwen2.5-coder:7b
docker compose up --build
```

Smoke URLs:

- Product: `http://127.0.0.1:5199/`
- Backend readiness: `http://127.0.0.1:8099/readyz`
- Design notebook: `http://127.0.0.1:8771/#structure`

ToolRouter runs inside the backend container; Ollama stays on the host at the
explicit Compose-configured endpoint. Runtime state persists under `.runtime`.
See `docs/docker-development.md` for logs, overrides, rebuilds, shutdown, and
failure diagnosis.

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
