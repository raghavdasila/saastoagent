# Step 4 Source Hub First Slice Validation

Date: 2026-08-07

This validation covers only the first behavior-complete Source Hub/API Source
runtime slice: owner inventory, API YAML plus optional Markdown intake,
source/revision/job linkage, separate Huey processing, persisted lifecycle
state, graph groups and exact recorded-stage inspection, protected revision-bound
connection-profile saving, and explicit retry. It does not close all of
horizontal-delivery Step 4.

## Runtime

- Command: `docker compose up --build -d backend source-worker frontend`
- Backend: `http://127.0.0.1:8099`
- Frontend: `http://127.0.0.1:5199`
- Source worker: `corpus-development-source-worker-1`
- Worker task: `corpus.features.sources.tasks.process_source_revision`
- Backend `/healthz`: `200`
- Backend `/readyz`: `200`
- Frontend `/`: `200`

The worker is a separate Compose service using the same Huey SQLite queue and
Corpus database. The backend never processes Source work synchronously and has
no in-process fallback when queue submission fails.

## Real Runtime Results

Successful development probe:

- source `j1k8YdSvK8g8Od4_`
- revision `OBv-uaH1g4JDLSYK`
- durable job `2e131af6-9969-4747-b3ce-a38a9e659675`
- initial state `queued`
- terminal state `ready`
- persisted optional description `medusa-probe.md`
- ToolRouter summary: 1 endpoint, 6 graph nodes, 8 graph edges
- after backend and worker restart, authenticated inventory reload returned the
  same source, revision, job, description, and `ready` state

Final rendered graph and protected-profile probe:

- run `20260807T082751Z-47061af05e`
- source `Ip7Azs0NjuEl6kCX`
- revision `rmBgcsnjvrxxoWcj`
- durable job `c6f083f8-782e-4412-9c3f-15e705302254`
- persisted graph: 5 nodes, 6 edges, semantic group `products`
- selected recorded construction stage: `2. reconcile`
- one revision-bound profile persisted with encrypted credential reference v1
- the private-form request received the generated secret
- public `sources.save_api_connection` dispatch arguments were exactly `{}`
- the secret was absent from rendered and persisted public profile metadata

Failure and retry development probe:

- source `sQUjVmiokwpIC-Fs`
- durable job `1a4fe6db-fcac-470d-95eb-4371bbbb32e1`
- first real worker attempt: `failed` / `source_processing_failed`
- explicit retry: `queued`
- second real worker attempt: remained truthfully `failed`

These were temporary local development probes against the actual Corpus
backend, queue, worker, filesystem persistence, and ToolRouter adapter. The
probe OpenAPI documents are not production data and are not presented as real
Medusa execution evidence.

## Automated Gates

- `.\.venv\Scripts\python -m pytest backend/tests -q`: 118 passed, one
  pre-existing Starlette/httpx deprecation warning
- `pnpm --dir frontend test`: 60 passed
- `pnpm --dir frontend typecheck`: passed
- `pnpm --dir frontend build`: passed
- `.\.venv\Scripts\python scripts/check_agent_design_parity.py`: passed
- `.\.venv\Scripts\python scripts/check_architecture_boundaries.py`: passed
- `.\.venv\Scripts\python scripts/check_doc_coverage.py`: passed
- `docker compose config --quiet`: passed

The visual audit found and corrected a real layout defect: selected Source
details reused the old debug overview flex class and rendered off-canvas. The
final browser run shows the corrected queued, ready, failed, and retry states.

The restart audit also reproduced a stale saved-conversation contract. Corpus
now treats `session_upgrade_required` like a missing or expired backing session:
it releases only that unusable Corpus conversation mapping, does not expose the
RouteDeck error, and allows a fresh conversation to start. The focused HTTP
test and a live browser retry both passed.

## Evidence

Machine-readable run record:
`.runtime/evaluations/20260807T063143Z-source-hub-first-slice/manifest.json`.

Original inventory/intake/retry browser evidence:

- result: `.runtime/evaluations/20260807T070523Z-17b1d043db/result.json`
- desktop screenshots: `02-source-queued.png`, `03-source-ready.png`, and
  `04-source-failed.png`
- mobile screenshots: `05-source-hub-mobile-390x844.png` and
  `06-source-failure-mobile-390x844.png`
- video: `source-hub-first-slice.webm`
- trace security: the raw Playwright trace was removed after the repository
  audit confirmed it retained an Authorization header; its pre-removal path
  and SHA-256 remain in
  `docs/superpowers/validation/2026-08-07-playwright-trace-security-removal.json`

The final run passed 5/5 behavior assertions with no HTTP, console, page, or
non-navigation request failures. Normal aborted RouteDeck event streams during
surface transitions are retained in the diagnostic record and are not treated
as product failures.

Graph/stage-inspection and protected-profile browser evidence:

- result: `.runtime/evaluations/20260807T082751Z-47061af05e/result.json`
- desktop screenshots: `01-source-hub-empty.png` through
  `06-source-failed.png`, including `04-semantic-graph-stages.png` and
  `05-protected-api-connection.png`
- mobile screenshots: `07-source-hub-mobile-390x844.png` and
  `08-source-failure-mobile-390x844.png`
- continuous video: `source-hub-first-slice.webm`
- trace through recorded-stage inspection: the raw archive was removed after
  the credential-header audit; the safe result, screenshots, and video remain,
  and the pre-removal identity is in the security-removal manifest

This run passed 7/7 behavior assertions with no HTTP, console, page, or
non-navigation request failures. The trace intentionally ends before protected
credential entry because Playwright traces retain request payloads. The
sanitized result records only boundary booleans and the empty public dispatch
object; screenshots and video render no secret.

Earlier failed recorder runs are retained under `.runtime/evaluations/` and
show the selector ambiguity, premature retry assertion, selected-detail layout
defect, and stale-conversation startup failure that were corrected before the
passing run.

## Limitations

This slice does not implement a safe API connection check, operation curation,
API execution, source deletion or dependency constraints, Agent attachment, or
later lifecycle features. Because the connection check is absent, the accepted
Studio Configure the API connection behavior remains partial even though
encrypted profile saving is complete. Recorded stages can be selected for
inspection, but the Studio Replay graph construction behavior remains incomplete
because ordered pause, resume, and step-through session replay is absent.
The OpenAPI documents in the browser recording remain explicitly labeled
development probes. Real local Medusa execution belongs to the later
API-execution slice and is not claimed here. This bounded slice passes its
visual evidence gate but does not close horizontal-delivery Step 4.
