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

The supported complete-product path runs the Corpus backend, application
worker, and frontend in Docker, with the authoritative Agent Design Studio as
a separate host process. Generative models may run through host Ollama or
OpenAI. Start from an empty parent directory so Docker receives the required
four-repository sibling layout:

```powershell
New-Item -ItemType Directory -Path C:\dev\corpus-development
Set-Location C:\dev\corpus-development
git clone https://github.com/saastoagent/saastoagent.git saastoagent-v0.1
Set-Location saastoagent-v0.1

# Required for the two private runtime repositories.
gh auth login
gh auth setup-git
gh auth status

# Clones RouteDeck and both runtimes at reviewed immutable commits.
.\scripts\clone-development-dependencies.ps1
```

The resulting layout is:

```text
corpus-development/
|-- saastoagent-v0.1/
|-- routedeck/
|-- agent-execution-runtime/
`-- agent-delivery-runtime/
```

These repositories are source-build dependencies, not Git submodules or
separately started Corpus services. Compose uses `corpus-development/` as its
build context. The backend image installs RouteDeck plus the two runtime Python
packages from the pinned sibling sources; the frontend image builds and links
RouteDeck's `@routedeck/core` and `@routedeck/react` packages. Corpus uses the
execution and delivery packages through Corpus-owned adapters.

Install the Design Studio dependencies once:

```powershell
pnpm --dir docs/corpus-agent-design/workbench install
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

### Local Medusa target

Medusa is source-complete inside the pinned sibling RouteDeck checkout; do not
clone a separate Medusa repository. Provision it once, then start only the
Medusa service for Corpus acceptance work:

```powershell
Set-Location ..\routedeck
powershell -NoProfile -ExecutionPolicy Bypass -File .\examples\medusa-agent\scripts\demo-stack.ps1 -Action Provision
powershell -NoProfile -ExecutionPolicy Bypass -File .\examples\medusa-agent\scripts\demo-stack.ps1 -Action Up -Services medusa
(Invoke-WebRequest http://127.0.0.1:9100/health -UseBasicParsing).StatusCode
```

Stop it without deleting its protected data:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\examples\medusa-agent\scripts\demo-stack.ps1 -Action Down
Set-Location ..\saastoagent-v0.1
```

`-Action Reset` destroys the protected demo data and is not part of normal
first-time setup, restart, or shutdown.

ToolRouter runs inside the backend container. It uses the explicitly selected
Ollama or OpenAI generation/review provider and always retains the pinned local
CPU MiniLM embedding path. Runtime state persists under `.runtime`.
See `docs/local-runtime-runbook.md` for prerequisites, exact startup order,
health checks, direct-host focused development, logs, rebuilds, shutdown, and
failure diagnosis. The Compose `notebook` service on port `8771` is stale and
is deliberately excluded.

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
