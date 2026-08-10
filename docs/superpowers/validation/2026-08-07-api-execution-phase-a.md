# API Execution Phase A Validation

## Scope

This gate covers only the pinned dependencies and unchanged neutral
`api-execution-runtime==0.1.0` snapshot. No Corpus Source behavior, RouteDeck
operation, credential lookup, persistence, job, or UI invokes it. Phase B is
not started.

## Snapshot and compatibility proof

- Nine neutral sibling modules are byte-identical to their recorded source
  SHA-256 values.
- The Corpus-owned restricted initializer exposes only the snapshot version.
- No sibling import or sibling filesystem path is needed at runtime.
- The sibling host, adapters, store, jobs, worker, demo, proof scripts,
  authentication, and UI remain absent.
- Prance minimal parsing, openapi-core request/response validation, and a
  validated injected-transport read pass under the exact approved pins.

## Real local reference

The first read attempt used the official-current Medusa Store spec retained by
agent-core and the local Medusa service at `http://127.0.0.1:9100`. The
unchanged snapshot rejected the raw document before transport because a
boolean schema contained a string default. The retained redacted artifact is
`.runtime/audits/20260807-api-execution-phase-a/get-product-types.json`.
The reference runner itself now records `blocked_before_http`, exact HTTP call
count 0, `http_request_sent=false`, and the already-emitted
`execution_started` event with only the safe `attempt` key. Its SHA-256 is
`d4e198d7262323890585808e12c00c37af2b630675e67249bf2ad4d8650e9a2a`.
It contains no credential, exception message, header, response body, or secret
value. The command deliberately returns non-success because raw-contract
validation failed; the artifact is evidence of a stopped attempt, not success.

The follow-up read-only audit ran that same source through the existing
ToolRouter invalid-default repair. The engine produced exactly one native
repair record (it has no opaque repair-ID field): source `medusa_store`, action
`remove_invalid_default`, pointer
`/components/schemas/AdminProductVariantDeleteResponse/properties/deleted/default`.
The repair-manifest canonical SHA-256 is
`dc712d7c172a8e6c3ee2fef8aa11c4f337d0c1622330df521dcf89c6fda19af2`;
the validated repaired-parent canonical hash is
`bc1b4b2456eefab4684a07ffa6e63f652118f5a705dd13eba5d77e74ab965c6e`.

The unchanged snapshot contract-revision engine then applied exactly the ten
reviewed cart patch IDs. The validated final executable canonical hash is
`6fca793be700dfb8bf511c2217d72cf97abf2f6cba08fbc2cd26ef0369b8f3f6`.
The prior planned `7ad31513...` value was stale because it did not include this
exact repair parent and is no longer authoritative.

Only after both pinned validators accepted the final document, the audit made
exactly one real call: `GET /store/product-types` (`GetProductTypes`) against
local Medusa. It succeeded with HTTP 200, zero validation issues, product-type
count 0, and three allowlisted trace events. No headers, bodies, credential
values, validator details, or response values were retained. The redacted
artifact is
`.runtime/audits/20260807-api-execution-contract-chain/contract-chain-audit.json`
(SHA-256
`86d39cb5a40286e6ef1388886f837274b5c04aa83bca50c991c5691269376b03`).

## Verification

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest backend\tests\integrations\api_execution -q` | 9 passed, including exact pre-HTTP trace/call-count/redaction evidence |
| `.\.venv\Scripts\python.exe scripts\run_api_execution_phase_a_reference.py` | Expected blocked result persisted: 0 HTTP calls, 1 allowlisted trace event, no secret material |
| `.\.venv\Scripts\python.exe -m pytest backend\tests -q` | 159 passed; one existing Starlette/httpx deprecation warning |
| `.\.venv\Scripts\python.exe -m pip install -e backend` then fresh `.\.venv\Scripts\python.exe -m pip check` | Editable metadata refreshed; no broken requirements found |
| `.\.venv\Scripts\python.exe -m compileall -q backend\src\corpus\integrations\api_execution scripts\run_api_execution_phase_a_reference.py` | Passed |
| `.\.venv\Scripts\python.exe scripts\export_frontend_contract.py --check` | Generated contract current |
| `.\.venv\Scripts\python.exe scripts\check_agent_design_parity.py` | Passed after the proven hash correction |
| `.\.venv\Scripts\python.exe -m pytest tests\test_agent_design_parity.py -q` | 30 passed |
| `.\.venv\Scripts\python.exe scripts\check_architecture_boundaries.py` | Passed |
| `.\.venv\Scripts\python.exe -m pytest tests\test_architecture_boundaries.py tests\test_check_doc_coverage.py -q` | 7 passed |
| `.\.venv\Scripts\python.exe scripts\check_doc_coverage.py --files <Phase A file list>` | Every supplied file mapped; exit 0 |
| `docker compose config --quiet` | Passed |

The retained audit directory was scanned against the actual local Medusa
credential without printing it. No exact credential value, bearer-token
pattern, or API-key/Authorization/Cookie assignment was found in any retained
audit file.

The explicitly required native ToolRouter `repair-manifest.json` is retained
as contract evidence. It contains only the source, JSON pointer, invalid schema
default, explicit repair action, and validator reason; it contains no HTTP
observation or credential material. The unnecessary full effective OpenAPI
document generated during independent reproduction was removed and is not
retained.

## Limitations

- The raw official-current Medusa Store spec is not directly executable under
  the approved validator pins; it requires the already-owned explicit
  ToolRouter repair pipeline.
- No API Source connection check, operation curation, route plan, real product
  execution, write, review, UI, screenshot, or video is claimed.
- The internal snapshot must not be publicly redistributed until its licensing
  is resolved or it is replaced.
