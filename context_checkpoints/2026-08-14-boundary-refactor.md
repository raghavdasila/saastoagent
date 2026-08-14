# Checkpoint: universal Corpus feature boundaries

Date: 2026-08-14

ADR-005 is implemented and locally validated. The authoritative Corpus remains
a modular monolith, but every immediate backend and frontend feature is now
covered by a universal directory-discovered import checker. Features may use
another feature only through its exact public `contracts` module; consumer
capabilities are expressed as consumer-owned ports and implemented in
`corpus.app`. Concrete repositories, integrations, runtime composition, and
the Huey entrypoint do not live in or leak into product features.

The worker entrypoint is `corpus.app.worker.huey`. Generic API Source
connection checks, route plans, and executions validate the selected persisted
reviewed revision rather than a global Medusa hash. The Medusa 2.13.6 correction
is isolated under `corpus.integrations.medusa_acceptance` and selected by app
composition. ToolRouter model-provider configuration is explicit and separate
from the product conversation-model provider. Docker-executed local Sources use
`host.docker.internal` to reach host Medusa.

Fresh gates: architecture zero violations; root 98/98; backend 532/532;
frontend 188/188; TypeScript/build; local and production Compose parsing;
boundary-skill validation; local health/readiness/frontend/Medusa HTTP 200.
Fresh horizontal evidence: Surface `20260814T093227Z-c2b50e9520` 39/39,
Hybrid `20260814T094346Z-c08c93dd9e` 40/40, and Chat
`20260814T104438Z-b8dd360dbc` 39/39.

Resume from:

- decision: `decisions/ADR-005-enforced-feature-and-acceptance-boundaries.md`
- audit: `audits/2026-08-14-present-system-boundary-audit.md`
- validation: `docs/superpowers/validation/2026-08-14-corpus-boundary-refactor.md`
- boundary architecture: `architecture/components/corpus-feature-architecture.md`
- checker workflow: `skills/audit-corpus-boundaries/SKILL.md`
- implementation plan: `docs/superpowers/plans/2026-08-14-corpus-boundary-refactor.md`

No RouteDeck file or user-owned behavior note was changed. No deployment was
performed. The implementation is intentionally left uncommitted because this
goal did not include a new authorization to commit it.
