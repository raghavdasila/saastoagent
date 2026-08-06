# Feature Architecture, Evaluator, Workspace, And Agents Closeout

Date: 2026-08-06

## Outcome

Implemented and verified the locked Lounge -> architecture foundation ->
generic evaluator -> Workspace -> core Agents order. The user-visible product
path and deterministic state evidence are both green.

## Architecture Audit

- Backend host/app composition owns concrete adapters and cross-feature
  injection.
- Auth owns global identity; persistence owns database lifecycle.
- Lounge, Workspace, and Agents own their vertical feature contracts and
  controller/domain layers.
- Frontend feature stores own only feature domain reads and local request state.
- RouteDeck owns topology, legality, transitions, projections, review, and
  recovery.
- `scripts/check_architecture_boundaries.py` enforces the import boundaries.
- `contracts/corpus-agent-design-routedeck-manifest.json` owns Studio mapping;
  technical identifiers remain out of Studio state.

## Evaluation Audit

Action plans now declare setup, surface/operation actions, expected outcomes,
and node/domain/projection checkpoints. The HTTP runtime performs real setup
through product Operations, the runner records durable evidence, and action-only
evaluations do not pretend that a chat semantic judge proves state mutation.

Passing evaluation artifacts:

- Workspace quick action: `20260806T060822Z-81f55dd99d`;
- Agent create: `20260806T060253Z-3925a7c131`;
- Agent edit: `20260806T060610Z-97d5395b7c`;
- Lounge aggregate: `20260806T062952Z-fac606911c` (8/8).

Earlier Mail.tm timeout artifacts and evaluator-diagnostic failures remain
immutable. Each was superseded by a passing run after the external mailbox or
the evaluator binding/readiness defect was corrected.

## Product Audit

Browser artifact `20260806T061531Z-bf0bc49c7c` proves the rendered flow and
database state. It also caught and then verified the fix for inherited surface
scroll position on node transitions. The mobile New Conversation control and
contract-derived Agents navigation were checked in the rerun.

Persistent Docker artifact `20260806T085604Z-persistent-6fe8de9bcd` proves the
same owner path against the long-lived development databases and the real
`5199`/`8099` stack: registration, Workspace, owner-scoped Agents empty state,
Agent v1 creation, immutable v2 save, resume-handle URL resynchronization,
session-bound reload, and persisted Workspace count. It recorded no HTTP
responses at or above 400, console warnings/errors, or page errors.

The earlier persistent artifact `20260806T070452Z-live-7c20c2be04` is a failed
run, not passing evidence. It exposed a RouteDeck projection invariant defect:
a session-bound self-transition rotated the projected resume handle without
advancing `projection_version`. The authorized RouteDeck correction includes
the current projected handle in the aggregate public signature and protects
the behavior at aggregate and operation-runner levels.

## Source-To-Owner Reconciliation

- Backend host/app/auth/persistence: Backend host, Corpus owner identity,
  shared persistence, and RouteDeck integration code-map rows.
- Lounge/Workspace/Agents backend and frontend: their feature rows plus Surface
  rendering.
- Evaluation runner/scripts: Corpus agent runtime and self-evaluation.
- Studio state/editor and manifest: RouteDeck Agent Design Studio and Shared
  contracts.
- Shell/header/navigation: Frontend app shell.
- Tests follow the same feature/runtime owners and are indexed in
  `test_index/README.md`.

## Validation

- `pytest backend/tests -q`: 100 passed, one upstream TestClient warning.
- `pytest tests -q`: 49 passed.
- `pnpm --dir frontend test`: 58 passed; typecheck/build passed with a
  non-failing Vite chunk advisory.
- Studio: 34 passed; typecheck/build passed.
- Architecture boundaries, Studio parity, and frontend contract check passed.
- RouteDeck core: 89 passed; typecheck/build passed.
- RouteDeck state/supervision/projection/navigation regression suites after the
  resume-handle correction: 270 passed; focused Ruff and MyPy passed.
- The wider RouteDeck checkout run finished 583 passed / 3 failed. Two failures
  require the separately running real Medusa integration state; the scripted
  chat replay assertion reproduces with the correction removed and is not
  caused by this change.

All application and evidence runtimes were local. Normal smoke URLs remain
`http://127.0.0.1:5199/` and `http://127.0.0.1:8099/readyz`; isolated evidence
ports are recorded in each result artifact.
