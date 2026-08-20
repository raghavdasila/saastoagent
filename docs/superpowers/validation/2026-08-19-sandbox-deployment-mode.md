# Sandbox deployment mode validation

Date: 2026-08-19

## Boundary

Validated the local v0.2 implementation in `saastoagent-v0.1` and the sibling
`agent-delivery-runtime`. RouteDeck, `agent-execution-runtime`, public Delivery
behavior, Studio build compilation, credentials, and production were not
changed. Repository publication does not deploy production; no production
deployment was performed.

## Runtime and provider

- Start command: `docker compose up --build -d backend source-worker frontend`
- Product: `http://127.0.0.1:5199/` (HTTP 200)
- Readiness: `http://127.0.0.1:8099/readyz` (`{"status":"ready"}`)
- Services: backend and frontend healthy; source-worker running locally
- Primary Agent, ToolRouter generator/reviewer, and Evaluation provider:
  OpenAI `gpt-5.6-luna`, reasoning effort `low`
- Provider fallback: none

## Automated verification

- `agent-delivery-runtime`: 21 passed
- Corpus deployment, migration, evaluation, provider, RouteDeck concurrency,
  and Delivery-compatibility focus: 23 passed
- Journey recorder contracts: 20 passed
- Frontend typecheck: passed
- Frontend: 35 files, 188 tests passed
- Corpus Agent Design Studio parity: passed
- RouteDeck application lease conflicts after the concurrency fix: 0

The concurrency regression test constructs two independent Corpus supervisors
against one build database and proves they serialize access through the shared
filesystem lock. This preserves RouteDeck's existing single-instance lease and
does not add a retry, fallback, provider, or dependency.

## Superseded legacy recorder boundary

The canonical v0.2 Sandbox journey above is the current execution authority for
Sandbox deployment, Playground, Diagnostics, and Evaluation-owned isolated
case sessions.

`scripts/run_horizontal_product_journey.py` now supports new bounded runs only
through Designer or Builder. A new unbounded run or `--stop-after evaluation`
fails loudly and directs the operator to
`scripts/run_v02_sandbox_deployment_journey.py`. Retained milestone artifacts
remain verifiable, but the pre-v0.2 owner-workspace `sandbox.start` segment and
its downstream Evaluation/Delivery path are historical evidence rather than a
current v0.2 product contract.

Redesigning one cross-feature journey across Agent selection, Sandbox,
Evaluation, Builds, and Diagnostics is deferred to the approved follow-on
cross-feature Studio and selected-Agent shell work. Historical artifacts and
their claims are not rewritten or fabricated.

Fresh closeout verification after adding that boundary:

- horizontal recorder contracts: 83 passed;
- root architecture/bootstrap/runtime-tooling suite: 102 passed;
- exact Windows-host focused Sandbox set: 17 passed, with the two known
  platform/dependency-sensitive cases separately passing 2/2 inside the Linux
  backend service;
- backend collection: 546 tests;
- Studio-to-compiled-RouteDeck parity: passed;
- documentation coverage advisory: exit 0;
- product: `http://127.0.0.1:5199/` returned HTTP 200;
- readiness: `http://127.0.0.1:8099/readyz` returned
  `{"status":"ready"}`.

The two host-only failures were not converted into product fallbacks: the
cross-process file-lock contract uses Linux runtime semantics, and the host
ToolRouter validator stack differs from the built service. Both exact tests
passed in the actual Linux Compose backend.

## Canonical real journey

Evidence: `artifacts/sandbox-deployment-v02/20260819T160037Z-b692dfdff1/result.json`

The normal-speed browser journey used the real local Medusa API and completed:

1. API Source definition, connection, operation curation, Agent design, and a
   ready immutable build.
2. Explicit owner-private Sandbox deployment without Evaluation eligibility.
3. Persistent multi-turn Playground interaction on the pinned deployment.
4. Clarification, write review, approval, and verified cart creation.
5. Private runtime diagnostics and page-reload recovery.
6. OpenAI/ToolRouter-generated evalset launch against the exact active Sandbox
   deployment.
7. A fresh `evaluation_case` session with a durable successful Evaluation-owned
   result, distinct from Playground history.

Canonical identities:

- Source: `6lCr0nGpXlBWhIr3`
- Source revision: `REu2kQrPC1ga8OIg`
- Agent: `7aa726f4-b6d0-4e3a-afa8-c9d1b2bc38f7`
- Build: `2e049b07-3bbf-4ddd-a5ef-48b68d9277bd`
- Sandbox target: `473ef70a-24d9-4db4-853e-83ea93995076`
- Corpus deployment: `e6231929-cae2-4881-b3a2-e055f6af2f3f`
- Runtime deployment: `dep_85c9b7cdf68e4627b742be6e2254001b`
- Playground session: `ses_cdc884cfd7b145808363b812e098683b`
- Evalset: `4abd1ab1-b8c3-43ac-b68b-b1e36763c5d7`
- Evaluation attempt: `de1971e1-79f7-4299-a0b7-a31f35149f33`
- Evaluation session: `ses_d06c384d44eb40b4b222f1661388f90f`

Diagnostics reported zero HTTP errors, zero page errors, and zero request
failures. Four Chromium WebGL performance warnings were retained in the ledger;
they are not application errors.

Video:
`artifacts/sandbox-deployment-v02/20260819T160037Z-b692dfdff1/sandbox-deployment-v02.webm`

- Playback rate: 1.0
- Bytes: 20,282,462
- SHA-256: `8691579bcb1e02dd0389e05baf661e2fdeb5ba7e0bfa3115f26ea7034fd372e5`
