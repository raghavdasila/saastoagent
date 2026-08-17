# Corpus Current Context

Updated: 2026-08-17

## Local follow-up pending publication

The Docker build requires sibling `agent-execution-runtime==0.1.0` and
`agent-delivery-runtime==0.1.0` source directories. Both are now canonical
private repositories under the `saastoagent` GitHub organization. The
repository-owned dependency manifest and bootstrap clone RouteDeck plus both
runtimes at immutable commits; a fresh checkout requires authenticated
organization access rather than undocumented local source.

Local, not-yet-published follow-up now makes development Compose honor the
existing explicit OpenAI ToolRouter provider contract, documents separate
Ollama and OpenAI setup lanes, preserves the pinned local CPU MiniLM embedding
boundary, adds the pinned source bootstrap, and corrects
`scripts/init-local.ps1` to migration
`0019_builder_assembly_lifecycle`. Focused provider/runtime tests and both
default and OpenAI Compose configuration checks pass. Production remains on
the previously recorded digests and was not changed or redeployed by this
follow-up.

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
- Test meaning and commands: `test_index/README.md`
- Architecture ownership: `architecture/code-map.md`
