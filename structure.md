# Corpus Repository Structure

Status: runnable Workspace plus Sources/API ToolRouter debug slice

```text
saastoagent-v0.1/
|-- Dockerfile                       # backend-dev and frontend-dev images
|-- Dockerfile.dockerignore          # exact filtered Corpus/RouteDeck context
|-- .dockerignore                    # direct-context local/generated exclusions
|-- compose.yaml                     # backend/frontend/notebook development stack
|-- .env.example                    # explicit local configuration contract
|-- backend/
|   |-- pyproject.toml              # Python manifest
|   |-- src/corpus/
|   |   |-- app/                    # host plus concrete composition roots
|   |   |-- auth/                   # owner identity, sessions, claims, mail
|   |   |-- runtime/                # SQLAlchemy and Ollama-backed agent runtime
|   |   |-- features/workspace/     # seven owner/guest Workspace nodes
|   |   |-- features/sources/       # generic lifecycle + neutral HTTP
|   |   |   `-- connectors/api/     # API config/HTTP/port + ToolRouter bridge
|   |   |-- integrations/toolrouter/# facade + private exact engine snapshot
|   |   |-- shared/environment.py   # allowlisted env parsing primitive
|   |   |-- composition.py          # Workspace/Sources/entry selection
|   |   |-- bindings.py
|   |   |-- session.py
|   |   `-- main.py                 # ASGI factory
|   `-- tests/                      # framework/auth/features/integrations
|-- frontend/
|   |-- package.json
|   |-- pnpm-lock.yaml
|   |-- src/
|   |   |-- app/                    # generic chat shell/bootstrap/Navgraph
|   |   |-- components/ui/          # generic shadcn/ui primitives
|   |   |-- lib/                    # shared UI helper
|   |   |-- routedeck/              # client and surface registry
|   |   |-- features/workspace/     # Lounge, auth-entry UI, feature styles
|   |   |-- features/sources/       # Sources workbench/client/styles
|   |   |-- main.tsx                # product composition
|   |   `-- styles.css
|   `-- src/tests/                  # framework, Workspace, Sources contracts
|-- scripts/
|   |-- docker-backend-entrypoint.py # persistent secrets, migration, process exec
|   |-- feature_behavior_notebook.py # notebook server + guarded container bind
|   |-- init-local.ps1              # reproducible environment setup
|   |-- run-backend.ps1
|   |-- run-frontend.ps1
|   `-- smoke_live.py               # real running guest/model smoke
|-- contracts/                      # future language-neutral contracts
|-- docs/                           # product, behavior, design notebook
|-- architecture/                   # subsystem ownership/contracts
|-- decisions/                      # durable ADRs
|-- plans/                          # active plans only
|-- test_index/                     # executable validation meaning
|-- tests/                          # repository-tooling tests
|-- logs/                           # dated session evidence
|-- context_checkpoints/            # restart handoffs
|-- context_history/                # archived prior live contexts
|-- knowledgebase/                  # verified reusable findings
|-- audits/                         # read-only audit reports
|-- errors/                         # reusable debugging evidence
|-- skills/                         # stable repeatable repo-local workflows
`-- benchmark/saastoagent-v0.1/     # ignored read-only legacy baseline
```

Generated local state lives only in ignored `.venv/`, `.env.local`,
`.runtime/`, `.codex-run/`, `frontend/node_modules/`, and `frontend/dist/`.
The primary development runtime is `docker compose up --build`; it uses the
filtered parent context to consume the local sibling RouteDeck source, keeps
ToolRouter embedded in the backend, and connects to host Ollama through an
explicit configured URL.
The new application does not import the ignored Corpus benchmark or the live
sibling ToolRouter checkout. The repository-contained ToolRouter snapshot is
private to its integration facade and is identified by exact hashes. See
`architecture/components/toolrouter-source-integration.md` for the
responsibility and separation rationale of every Sources/ToolRouter file.
