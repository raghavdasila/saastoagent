# Corpus v0.2 Sandbox Deployment Mode Implementation Plan

**Status:** Approved for implementation on 2026-08-19.

## Outcome

Sandbox is an explicit owner-private `sandbox` mode of the shared
`agent-delivery-runtime`, alongside channel-bound `delivery`. A ready immutable
build enters Sandbox only after an explicit owner deployment. Playground and
evaluation sessions execute through the same RouteDeck-powered Agent runtime
as Delivery without sharing admission, sessions, state, or evidence.

## Mutation Boundary

- Corpus: behavior/Studio/mapping owners, Deployment, Sandbox, Evaluation,
  application composition, migrations, Sandbox frontend, focused tests, and
  validation documentation.
- Shared runtime: sibling `agent-delivery-runtime` contracts, services, store,
  API compatibility surface, tests, and package version `0.2.0`.
- Read-only: RouteDeck, `agent-execution-runtime`, build compilation,
  credential ownership, public Delivery behavior, production, retained v0.1
  Sandbox evidence, and Git state.

## Delivery Order

1. Align Behavior Notes, accepted Studio design, RouteDeck mapping, and the
   approved architecture spec.
2. Generalize `agent-delivery-runtime` to mode-neutral deployment targets,
   activations, sessions, interactions, and host services while retaining the
   public channel compatibility wrapper.
3. Add Corpus deployment targets and migrate existing channel deployments to
   `delivery` targets without changing IDs or active public behavior.
4. Add explicit Sandbox deployment, owner-authenticated Playground session,
   message, review, and diagnostics APIs.
5. Execute Evaluation cases through fresh `evaluation_case` sessions on an
   exact Sandbox deployment and keep results Evaluation-owned.
6. Replace the current Sandbox operation form with the private Agent shell,
   deployment history, Playground, Evaluations, and Diagnostics.
7. Run focused and full contracts, local restart persistence, real Medusa
   execution, browser QA, isolated evidence, and only then the canonical audit.

## Locked Rules

- One Sandbox target exists per owner-scoped Agent and points to at most one
  active ready deployment.
- Sandbox deployment requires a ready immutable build but not Evaluation
  eligibility. Delivery continues to require eligibility.
- Failed replacement leaves the previous ready deployment active. Successful
  replacement supersedes it without mutating it or its sessions.
- Deployment mode and session purpose (`playground`, `evaluation_case`, or
  `delivered_conversation`) are immutable.
- Eval cases and retries always create new sessions. Eval traffic never enters
  Playground history or deployed Operations.
- Duplicate requests are idempotent by request key. Redeploying the active
  build without an explicit failed-attempt retry returns `already_active`.
- Existing `agent_sandbox_sessions` and `agent_sandbox_runs` remain read-only
  v0.1 evidence and receive no fabricated deployment lineage.
- Failures remain failures. There is no automatic retry, mock execution,
  alternate provider, cached result, or fallback response.

## Acceptance Evidence

- Shared-runtime mode/purpose, activation, replacement-failure, review, and
  cross-mode isolation tests.
- Corpus migration, owner isolation, explicit deployment, persistence,
  Delivery regression, eval isolation, and Operations exclusion tests.
- Local Docker product at `http://127.0.0.1:5199/` with readiness at
  `http://127.0.0.1:8099/readyz`.
- Real Medusa journey from ready build through explicit Sandbox deployment,
  multi-turn Playground, clarification/review, ToolRouter evalset, isolated
  case runs, and durable Evaluation results, with normal-speed video and exact
  identities.
