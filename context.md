# Corpus Current Context

Updated: 2026-08-19

## Local behavior evidence baseline

The first exhaustive local as-is Design Studio behavior campaign is committed
and pushed at `94ab630`. Canonical run
`RUN-20260818T192408Z-3bd810db` records 77 behaviors: 53 passed, 10 failed,
13 blocked, and 1 pending, with 231 tracked screenshots and 24 linked tasks.
The evidence dashboard and machine ledger live under
`audits/2026-08-v0.2-behavior-audit/`.

Use `docs/corpus-behavior-evidence-ledger.md` as the audit-process and
data-contract owner and `skills/audit-corpus-behaviors/SKILL.md` as the
repeatable operator workflow. Future retests build on the committed baseline;
the current recorder supports full in-place reruns but not selective behavior
or feature filters.

Use `docs/corpus-behavior-first-delivery-process.md` as the separate product
delivery process: owner behavior -> accepted Studio design -> RouteDeck mapping
-> Corpus vertical implementation -> isolated validation -> canonical ledger
retest -> release-level horizontal acceptance.

## v0.2 Sandbox publication

The Docker build requires sibling `agent-execution-runtime==0.1.0` and
`agent-delivery-runtime==0.2.0` source directories. Both are now canonical
private repositories under the `saastoagent` GitHub organization. The
repository-owned dependency manifest and bootstrap clone RouteDeck plus both
runtimes at immutable commits; a fresh checkout requires authenticated
organization access rather than undocumented local source.

Published `agent-delivery-runtime` v0.2 work at
`a20fce7dfa831bca4e6e10a4ea00b0badb01b47f` generalizes the shared runtime into
`sandbox` and `delivery` deployment modes. Corpus now owns one explicit
owner-private Sandbox target per Agent, deployment history, pinned persistent
Playground sessions, private diagnostics, and Evaluation-owned isolated case
sessions. Existing public Delivery admission and APIs remain unchanged. The
local OpenAI lane uses `gpt-5.6-luna` with low reasoning for the primary Agent,
ToolRouter generation/review, and Evaluation. Compose reads `.env.local`
through each service's `env_file`; no provider fallback is enabled. Production
remains on the previously recorded digests and was not changed or redeployed.
The canonical local Medusa-backed acceptance run is recorded at
`artifacts/sandbox-deployment-v02/20260819T160037Z-b692dfdff1/result.json`;
its exact-build evaluation succeeded with a session isolated from Playground
and no HTTP, page, or request failures. Build-scoped Agent RouteDeck access is
serialized across backend and worker processes so the existing single-instance
RouteDeck database lease remains authoritative under concurrent inspection.

The pre-v0.2 horizontal recorder is now explicitly bounded to new Designer or
Builder milestone runs. Its historical artifacts remain verifiable, while the
canonical v0.2 Sandbox journey owns current Sandbox and Evaluation proof. The
next approved work is, in order: configurable complete Evaluation coverage,
owner-scoped Agent discovery/selection, and cross-feature Studio journeys plus
a stable selected-Agent shell.

## Current state

Corpus is the authoritative checkout and is live at
`https://corpus.saastoagent.com`. ADR-005 is implemented, pushed, deployed, and
validated. All five HIGH findings in
`audits/2026-08-14-present-system-boundary-audit.md` are closed; four MEDIUM
findings remain explicit follow-up work.

Corpus remains a modular monolith. Every immediate backend and frontend feature
is governed by one directory-discovered checker with zero baseline exemptions.
Cross-feature behavior uses exact public contracts, consumer-owned ports,
neutral shared types, and adapters composed under `corpus.app`. The Huey
entrypoint is `corpus.app.worker.huey` and the live worker registers exactly
five application-owned tasks.

Generic API check/plan/execute paths validate the selected persisted reviewed
revision. Medusa 2.13.6 acceptance behavior is isolated in the explicitly
selected `corpus.integrations.medusa_acceptance` adapter. RouteDeck owns legal
topology, reviews, projection, and session mechanics; Corpus owns product
meaning, persistence, routes, surfaces, adapters, and identities.

## Production truth

- Corpus VM: `corpus-vm-1`, `n2-standard-2`, `asia-south1-a`.
- Private acceptance dependency: Medusa 2.13.6 at `10.138.0.2:9100` on
  `medusa-test-vm-1`.
- Backend/worker digest:
  `sha256:6b9c677b54bea60ea85ce9816a0e176d6e97b1f5185aea9b62fa0b2f59fd18ee`.
- Web digest:
  `sha256:1a9acb0a572b7708e87bd9b7d0407af9ae1cb38154d5f717f38a4e6aa41a6b41`.
- `corpus.service` and `corpus-backup.timer` are active.
- Backend, worker, and web are running with zero restarts and zero OOM kills;
  backend is healthy.
- Public `/healthz` and `/readyz` returned HTTP 200 after acceptance.

Readiness intentionally checks the configured OpenAI dependency with a
five-second timeout and fails closed. No provider, fixture, cached-output, or
heuristic fallback is selected.

## Accepted deployed evidence

- Surface `20260815T113953Z-89bb70e514`: 39/39.
- Hybrid `20260815T102407Z-828e3735c3`: 40/40.
- Chat `20260815T115153Z-5847710253`: 39/39.

The three journeys used independent lineages, the same real Medusa Source hash,
continuous normal-speed raw recordings, real restart recovery, reviewed public
writes, and zero unexpected HTTP, console, page, or request failures. Exact
video paths, durations, hashes, retained IDs, failed-run boundaries, and
commands are in
`docs/superpowers/validation/2026-08-15-deployed-boundary-refactor.md`.

Fresh closeout gates: backend 536/536; root 100/100; architecture zero
violations; doc coverage exit zero; repo-local boundary skill valid. The
deployed product sources also passed frontend 188/188, strict typecheck,
production build, package/import checks, and `pip check` before publication.

## Boundaries and remaining work

- The sibling RouteDeck checkout remains separate and was not changed.
- `docs/corpus-agent-design/feature-behavior-notes.md` remains user-owned and
  untouched.
- Runtime videos/screenshots are local artifacts; committed validation docs
  record their paths and hashes.
- The accepted Medusa ecommerce path does not prove every external API,
  exhaustive Behavior Note breadth, hostile-code/process isolation,
  multi-host scaling, or an SLA.
- Next work should address retained MEDIUM findings or normal feature QA, not
  rerun the horizontal campaign as a debugger.

## Restart owners

- Current audit: `audits/2026-08-14-present-system-boundary-audit.md`
- Decision: `decisions/ADR-005-enforced-feature-and-acceptance-boundaries.md`
- Validation: `docs/superpowers/validation/2026-08-15-deployed-boundary-refactor.md`
- Checkpoint: `context_checkpoints/2026-08-15-deployed-boundary-refactor.md`
- Log: `logs/20260815_deployed_boundary_refactor.md`
- Deployment: `docs/deployment/gcp-single-vm.md`
- Boundary checker workflow: `skills/audit-corpus-boundaries/SKILL.md`
- Behavior ledger workflow: `skills/audit-corpus-behaviors/SKILL.md`
- Behavior ledger contract: `docs/corpus-behavior-evidence-ledger.md`
- Behavior-first delivery process: `docs/corpus-behavior-first-delivery-process.md`
- Test meaning and commands: `test_index/README.md`
- Architecture ownership: `architecture/code-map.md`
