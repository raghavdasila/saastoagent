# Corpus Backend

The backend contains the generic RouteDeck host, Corpus owner authentication,
Lounge, Workspace, generic Sources, and the replaceable ToolRouter integration used by
the API connector.

```text
backend/
|-- pyproject.toml
|-- src/corpus/
|   |-- app/                         # host + concrete composition roots
|   |-- auth/                        # owner identity/session/claims
|   |-- features/lounge/             # public Lounge + account journeys/policies
|   |-- features/workspace/          # owner Workspace nodes and surfaces
|   |-- features/sources/            # generic lifecycle + connectors/API
|   |-- integrations/toolrouter/     # facade + private proven engine snapshot
|   |-- runtime/                     # RouteDeck runtime and Corpus agent
|   |-- composition.py               # selects Lounge + Workspace + Sources
|   |-- bindings.py
|   |-- session.py
|   `-- main.py               # ASGI factory
`-- tests/                           # framework/auth/features/integrations
```

The generic Sources package exposes `SourceService`, neutral retrieval/evalset
contracts, and a connector protocol. The API package separately owns its
upload configuration/HTTP and an `ApiSourceEngine` port. Only
`features/sources/connectors/api/toolrouter.py` translates the public
ToolRouter facade; a boundary test enforces this rule. Concrete registration
lives in `app/source_composition.py`. ToolRouter owns all of its model,
embedding, Ollama, and timeout settings while its `engine/` modules remain
private and hash-manifested.

Run from the repository root after `.\scripts\init-local.ps1`:

```powershell
.\scripts\run-backend.ps1
.\.venv\Scripts\python.exe -m pytest backend\tests -q
```

The host fails startup on invalid or missing configuration. Readiness fails
closed when persistence or the configured primary Ollama model is unavailable.
Source ingestion additionally requires the pinned local MiniLM revision;
evalset generation requires the configured Gemma generator and Qwen reviewer
with resolvable immutable Ollama digests. No parser/model/provider fallback is
selected on failure.

Source API paths are:

```text
GET  /api/sources
GET  /api/sources/{source_id}
POST /api/sources/api
POST /api/sources/{source_id}/retrieve
POST /api/sources/{source_id}/evalsets
```

All require an active Corpus owner session; mutations enforce same-origin
policy and cross-owner lookups return the same 404 as missing sources.
