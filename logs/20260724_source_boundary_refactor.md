# Source Boundary Refactor Evidence

Date: 2026-07-24

## Outcome

Generic Sources no longer contains API upload transport or ToolRouter runtime
values. API owns its settings, multipart route, intake, connector, and engine
port. ToolRouter owns every embedding/Ollama/evalset value. One explicit bridge
translates between the API engine port and the public ToolRouter facade, and
`app/source_composition.py` is the concrete registration boundary.

## Changed Ownership

- Backend host: `app/source_composition.py`, `main.py`.
- Sources feature: generic config/HTTP/common transport; API config, HTTP,
  engine port, connector, and ToolRouter bridge; focused tests.
- ToolRouter integration: settings environment ownership and tests.
- Shared primitives: allowlisted environment reader.
- Context architecture: code map, component docs, ADR, flow/test indexes,
  structure explorer, plan, checkpoint, and live context.

## Fresh Validation

```powershell
.\scripts\init-local.ps1
.\.venv\Scripts\python.exe -m pytest backend\tests -q
.\.venv\Scripts\python.exe -m pip check
pnpm --dir frontend test
pnpm --dir frontend typecheck
pnpm --dir frontend build
python -m unittest tests.test_feature_behavior_notebook -v
python scripts\validate_design_notebook.py
```

Results:

- local setup completed; pinned MiniLM cached;
- 56 backend tests passed with one upstream Starlette/httpx deprecation
  warning;
- no broken Python requirements;
- 19 frontend tests passed; typecheck/build passed with the existing Vite
  chunk-size advisory;
- 10 behavior-notebook tests passed;
- proposed notebook remains 15 features, 53 nodes, 146 edges, and zero missing
  targets.

## Real Product Pipeline

The backend was restarted locally with:

```powershell
.\scripts\run-backend.ps1
```

Smoke URL: `http://127.0.0.1:8099/readyz` returned
`{"status":"ready"}`. Frontend remained at `http://127.0.0.1:5199/`.

An evidence owner was issued through the real local auth service and the
production Source HTTP routers received the sibling ToolRouter project's real
Ory Kratos `api.yaml`:

```text
source ex1IDkDESNq_5EWy
  -> ready
  -> 56 endpoints
  -> 477 graph nodes / 876 edges / 477 cards
  -> create a new identity
  -> ASK_DISAMBIGUATE / low_score_margin
  -> api:createRecoveryLinkForIdentity at 0.4279818403720856
  -> evalset boundary-proof-65553b771add
  -> ready, 1 accepted, 0 quarantined, 2,936 offline tokens
```

Model evidence:

- generator `gemma4:latest`, digest
  `c6eb396dbd5992bbe3f5cdb947e8bbc0ee413d7c17e2beaae69f5d569cf982eb`;
- reviewer `qwen2.5-coder:7b`, digest
  `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.

The reviewer model was initially absent. Setup failed explicitly, the exact
required model was pulled, setup was rerun successfully, and the same required
model completed the real evalset path. No alternate model or fallback was
used.

## Browser Boundary

The in-app browser rejected the localhost reload under its URL policy, so no
new rendered-browser claim is made for this refactor. The unchanged frontend
behavior passed all 19 component tests. The running Structure notebook returned
HTTP 200 at `http://127.0.0.1:8771/#structure` and its served document contains
`source_composition.py`, `http_common.py`, `ApiSourceEngine`, and API-owned
`http.py` entries.

