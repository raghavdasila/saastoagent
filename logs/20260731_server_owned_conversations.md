# 2026-07-31 Server-Owned Conversations And Recovery Closeout

## Scope And Outcome

Completed the approved bearer/conversation architecture correction across
Corpus and RouteDeck. Mobile-compatible bearer identity and public Corpus
conversation selection now replace browser-cookie session authority. Corpus
authorizes and maps conversations; RouteDeck centrally provisions and owns
runtime sessions and reconnectable runs.

The final recovery proof runs in a disposable local runtime that owns both
databases. It no longer leaves new RouteDeck sessions in the normal development
database.

## Changed Corpus Source By Code-Map Owner

### Frontend app shell

- Added `frontend/src/app/transports.ts` and
  `frontend/src/app/browserSessionAdapters.ts`.
- Updated `frontend/src/app/bootstrapConnection.ts`, `clientSession.ts`,
  `conversations.ts`, `createRouteDeck.ts`, `loadRouteDeck.ts`,
  `ApplicationShell.tsx`, and `frontend/src/main.tsx`.
- Updated Lounge authentication composition and Sources transport injection in
  `frontend/src/features/lounge/**` and
  `frontend/src/features/sources/sourceClient.ts`.
- Removed the obsolete `frontend/src/app/corpusConnection.ts` and
  `frontend/src/routedeck/client.ts` paths.
- Added/updated focused transport, bearer, conversation-selection, bootstrap,
  shell, auth-surface, and Sources tests under `frontend/src/tests/**`.

Owner row: **Frontend app shell**. Architecture anchor updated:
`architecture/components/corpus-routedeck-boundary.md`. Validation meaning
updated in `test_index/README.md`.

### Corpus owner identity and Backend host

- Updated `backend/src/corpus/auth/conversations.py`, `config.py`, `database.py`,
  `http.py`, `models.py`, `schemas.py`, `selector.py`, `service.py`, and
  `session_boundary.py` for bearer identity and public conversation ownership.
- Added `backend/src/corpus/auth/credential_transition.py`; reduced
  `backend/src/corpus/auth/operation_http.py` to the HTTP adapter.
- Updated composition through `backend/src/corpus/main.py`,
  `backend/src/corpus/runtime/application.py`, `backend/src/corpus/bindings.py`,
  and `backend/src/corpus/features/lounge/bindings.py`.
- Updated the initial auth migration directly; no compatibility migration or
  database reset was introduced.
- Updated focused auth, integration, runtime, and Workspace tests.

Owner rows: **Corpus owner identity**, **Backend host**, **Lounge feature**.
Architecture anchors updated: `architecture/components/corpus-routedeck-boundary.md`,
`architecture/code-map.md`, and the existing identity decision/flow owners.

### Validation tooling and Docker development runtime

- Added `scripts/smoke_restart_recovery_isolated.py`.
- Hardened `scripts/smoke_restart_recovery.py`; its unsafe direct CLI is now
  disabled.
- Added `tests/test_smoke_restart_recovery.py` coverage for owned database/path,
  state integrity, decoy preservation, and direct-execution rejection.
- Updated `compose.yaml` so Uvicorn's five-second graceful timeout is shorter
  than Compose's ten-second stop grace period.

Owner rows: **Validation tooling** and **Docker development runtime**.
Architecture and test anchors were updated. `SYSTEM_FLOW_INDEX.md` remains the
runtime-flow owner; no product Navgraph claim changed.

### Design Studio and Lounge implementation

Earlier in the same session, the RouteDeck Agent Design Studio was reshaped and
the Lounge design/implementation mapping was completed. Relevant files include
`docs/corpus-agent-design/workbench/**`,
`contracts/corpus-agent-design-routedeck-manifest.json`, and
`backend/src/corpus/features/lounge/**`. The user-owned
`docs/corpus-agent-design/feature-behavior-notes.md` was not modified.

Owner rows: **RouteDeck Agent Design Studio**, **Shared contracts**, and
**Lounge feature**. Their existing architecture/test anchors remain current.

## Explicitly Authorized RouteDeck Changes

The user granted RouteDeck write authority for the named server-owned
conversation plan only. That work changed the central runtime provisioner,
FastAPI session/run/history/SSE contracts, LangGraph model-start diagnostics,
generated TypeScript descriptors/decoders, and focused tests/docs in
`D:\Dev\AI Projects\routedeck`.

Notable owners include:

- `routedeck_core/runtime.py`
- `routedeck_fastapi/conversation_projection.py`
- `routedeck_fastapi/conversation_sse.py`
- `routedeck_fastapi/routes/sessions.py`
- `routedeck_fastapi/routes/conversation.py`
- `routedeck_langgraph/agent_driver.py`
- `packages/core/src/conversation/codec.ts`
- generated contract schema/type/descriptor artifacts and focused tests

The final cross-language review found no remaining actionable mismatch.
Request IDs share a 1..256 Unicode-code-point domain, versions are bounded to
JavaScript-safe integers, history identifier semantics align, and unknown
fields fail.

This plan-limited RouteDeck authority is exhausted; the sibling returns to
read-only-by-default status.

## Runtime Evidence

Normal local runtime: Docker Desktop on Windows host.

```powershell
docker compose up --build -d
```

- Product `http://127.0.0.1:5199/` -> HTTP 200
- Backend `http://127.0.0.1:8099/readyz` -> HTTP 200
- Studio/notebook `http://127.0.0.1:8771/` -> HTTP 200
- Backend, frontend, and notebook reported healthy.

Disposable restart proof:

```powershell
.\.venv\Scripts\python.exe -m scripts.smoke_restart_recovery_isolated
```

Observed request ID:
`restart-smoke-0a4e5b3c291340dea63ad5736bee94da`.
The real local Ollama turn became active, Uvicorn shut down gracefully, the
same isolated databases reopened immediately, and the run recovered as durable
`turn_interrupted`. Owner identity and the public conversation remained
authorized. Both temporary databases were removed; normal `.runtime` was not
selected.

## Automated Evidence

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
# 69 passed; one upstream Starlette/httpx deprecation warning

.\.venv\Scripts\python.exe -m pytest tests\test_smoke_restart_recovery.py -q
# 27 passed
```

From `D:\Dev\AI Projects\routedeck`:

```powershell
pnpm --filter @routedeck/core test
# 88 passed

pnpm --filter @routedeck/core typecheck
# passed

.\.venv\Scripts\python.exe -m pytest tests\fastapi\test_public_response_models.py tests\test_contract_generation.py -q
# 36 passed
```

Earlier in the same implementation slice, Corpus frontend completed 32 tests,
strict typecheck, and production build. Final focused Ruff checks passed.
RouteDeck's full-package mypy still has the pre-existing unrelated
`routedeck_core/contracts/surfaces.py:100` Pydantic overload issue; touched-file
mypy passed.

`python scripts/check_doc_coverage.py` mapped the changed Corpus owners and
exited zero. Its full-tree advisory continues to report unrelated checked-in
`mockruns/**/node_modules` files with no code-map owner.

## Unresolved Items

- `backend/src/corpus/features/lounge/prompt.py` contains Lounge-specific entry
  guidance but the current entry agent uses the generic Corpus prompt. The
  first message is model-generated, not hardcoded. Prompt/policy ownership is
  the next design/mapping question.
- Pre-isolation probes may have left internal sessions in the normal RouteDeck
  SQLite database. No safe public deletion contract exists, so they were not
  deleted directly.
- Failed isolated probe directories retained for diagnosis:
  `C:\Users\ragha\AppData\Local\Temp\corpus-restart-smoke-egaf2mrf` and
  `C:\Users\ragha\AppData\Local\Temp\corpus-restart-smoke-ihqvn53s`.
- A fresh rendered owner registration/sign-in adoption run was not repeated
  after the final credential-transition refactor. Focused integration tests and
  the existing prior rendered evidence passed; do not claim a fresh final
  browser proof for that exact path.

No Git operation was performed.
