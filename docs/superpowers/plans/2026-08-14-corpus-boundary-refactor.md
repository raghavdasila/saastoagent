# Corpus Boundary Refactor Implementation Plan

Status: completed and validated on 2026-08-14. Exact completion evidence is in
`docs/superpowers/validation/2026-08-14-corpus-boundary-refactor.md`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Implement ADR-005 so every Corpus feature obeys one enforceable modular-monolith boundary, application composition lives under `corpus.app`, and generic API Source execution validates its selected reviewed revision without embedding Medusa acceptance policy.

**Architecture:** Features retain their domain logic and expose only stable contracts. A consuming feature defines the narrow port it needs; `corpus.app` implements that port with provider services and concrete integrations. Shared infrastructure is imported only through deliberate public roots. The Huey process is composed under `corpus.app`. Medusa 2.13.6 correction remains an explicitly selected acceptance adapter, while generic route/check/execute services use the exact persisted reviewed revision as truth.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, Huey, pytest, React 19, TypeScript, Vitest, Vite, Docker Compose, RouteDeck public packages.

## Global Constraints

- Work only in the authoritative Corpus checkout at `D:\Dev\AI Projects\saastoagent-v0.1`.
- Keep `D:\Dev\AI Projects\routedeck` read-only. A missing RouteDeck contract is a stop condition.
- Never modify `docs/corpus-agent-design/feature-behavior-notes.md`.
- Do not access `D:\Dev\AI Projects\AutomationBench`.
- Preserve accepted product operations, prompts, policies, routes, review semantics, state transitions, persisted data, and public behavior.
- Do not add dependencies, migrations, compatibility wrappers, hidden fallbacks, violation baselines, broad checker ignores, service locators, or dynamic import registries.
- Do not commit, stage, push, pull, branch, reset, or otherwise perform Git operations during implementation unless the owner separately authorizes that operation. The earlier documentation commit does not authorize implementation commits.
- Run locally. Do not deploy.
- Use the full three-mode horizontal E2E only after focused architecture, backend, frontend, and runtime gates pass.

---

### Task 1: Make the architecture contract universal before refactoring consumers

**Files:**

- Modify: `scripts/check_architecture_boundaries.py`
- Modify: `tests/test_architecture_boundaries.py`

- [x] Add failing fixture tests proving backend and frontend feature discovery is directory-driven rather than a hard-coded feature list.
- [x] Add one allowed-import test for each backend category: self, `corpus.shared`, `corpus.persistence`, public `corpus.jobs`, public `corpus.credentials`, `corpus.auth.contracts`, and another feature's exact `contracts` module.
- [x] Add forbidden-import tests for another feature's service/repository/model/schema/http/ports modules, `corpus.app`, `corpus.runtime`, concrete `corpus.integrations`, and concrete `corpus.jobs.repository`.
- [x] Add frontend tests for self/shared/component/RouteDeck imports, exact feature `contracts` imports, forbidden cross-feature internals, and forbidden `app` composition imports.
- [x] Implement sorted discovery of immediate feature directories, excluding non-feature cache/private directories, and retain exact file/line diagnostics.
- [x] Represent public infrastructure roots as a narrow explicit allowlist; do not use a checked-in violation baseline.
- [x] Run `\.venv\Scripts\python.exe -m pytest tests\test_architecture_boundaries.py -q` and confirm fixture tests pass while the current-repository assertion reports the real refactor inventory.

### Task 2: Establish stable public infrastructure and execution types

**Files:**

- Modify: `backend/src/corpus/jobs/ports.py`
- Modify: `backend/src/corpus/jobs/__init__.py`
- Modify: `backend/src/corpus/features/builder/execution.py`
- Modify: `backend/src/corpus/features/evaluation/execution.py`
- Modify: `backend/src/corpus/features/evaluation/generation.py`
- Modify: `backend/src/corpus/features/deployment/execution.py`
- Create: `backend/src/corpus/shared/agent_execution.py`
- Create: `backend/src/corpus/shared/agent_delivery.py`
- Create: `backend/src/corpus/shared/clarification.py`
- Modify: `backend/src/corpus/integrations/agent_execution/**`
- Modify: `backend/src/corpus/integrations/agent_delivery.py`
- Modify: affected feature and app imports
- Test: `backend/tests/jobs/**`
- Test: `backend/tests/integrations/agent_execution/**`
- Test: affected Builder/Evaluation/Deployment/Operations tests

- [x] Write focused protocol tests or type-level construction tests for a `DurableJobLifecyclePort` exposing only the job record transitions processors consume.
- [x] Export job protocols and job-domain failures through `corpus.jobs`; stop feature processors importing `corpus.jobs.repository` or its SQLAlchemy implementation.
- [x] Move neutral execution/delivery projection dataclasses and protocols out of concrete integrations into `corpus.shared.agent_execution` and `corpus.shared.agent_delivery`; update integrations to implement/consume the shared types.
- [x] Move the cross-feature clarification value/error contract to `corpus.shared.clarification` and update consumers without changing messages.
- [x] Keep SQLAlchemy repositories and concrete neutral adapters selected only by `corpus.app`.
- [x] Run focused jobs, integrations, and processor tests.

### Task 3: Replace Agent-centered cross-feature coupling with consumer ports and public identities

**Files:**

- Modify: `backend/src/corpus/features/agents/contracts.py`
- Modify: `backend/src/corpus/features/agents/declarations.py`
- Modify: `backend/src/corpus/features/{builder,designer,evaluation,sandbox,operations,channels,sources}/ports.py`
- Modify: `backend/src/corpus/features/{builder,designer,evaluation,sandbox,operations}/bindings.py`
- Modify: `backend/src/corpus/features/{builder,designer,evaluation,sandbox,operations,channels}/http.py`
- Modify: `backend/src/corpus/features/{builder,designer,evaluation,sandbox,operations,channels,sources}/feature.py`
- Modify: `backend/src/corpus/features/{builder,designer,evaluation,sandbox,operations}/operations.py`
- Modify: `backend/src/corpus/features/{builder,designer,evaluation,sandbox,operations}/service.py`
- Create: `backend/src/corpus/app/feature_adapters.py`
- Modify: application route/composition modules that construct these features
- Test: focused tests under `backend/tests/{agents,builder,designer,evaluation,sandbox,operations,delivery,sources}`

- [x] Move deliberately shared Agent Node/Operation/Entity identities into `agents.contracts`; declaration modules consume those constants rather than owning cross-feature identities.
- [x] Put deployment identities consumed by Channels into `deployment.contracts` and Source identities consumed by Builder into `sources.contracts`.
- [x] Define feature-local owner-scope/Agent-view/navigation ports with feature-owned unavailable errors. Do not import `agents.ports`, `agents.service`, `agents.operations`, or `agents.http` from consumers.
- [x] Implement adapters in `corpus.app.feature_adapters` using `AgentService` and provider repositories; keep public contract values stable.
- [x] Replace imports of `AgentsHttpProblem` with each feature's own HTTP translation of its own boundary error.
- [x] Inject consumer ports through service/handler/feature construction and update app wiring.
- [x] Run each affected feature suite after its adapter seam is green.

### Task 4: Remove Designer, Builder, Sandbox, Evaluation, Delivery, and ToolRouter implementation leaks

**Files:**

- Modify: `backend/src/corpus/features/designer/contracts.py`
- Modify: `backend/src/corpus/features/designer/repository.py`
- Modify: `backend/src/corpus/features/builder/contracts.py`
- Modify: `backend/src/corpus/features/builder/{navgraph.py,repository.py,service.py,ports.py}`
- Modify: `backend/src/corpus/features/sandbox/{ports.py,service.py,operations.py}`
- Modify: `backend/src/corpus/features/evaluation/{ports.py,service.py,generation.py}`
- Modify: `backend/src/corpus/features/operations/service.py`
- Modify: `backend/src/corpus/features/channels/service.py`
- Modify: `backend/src/corpus/features/deployment/service.py`
- Modify: `backend/src/corpus/features/sources/connectors/api/toolrouter.py`
- Modify: `backend/src/corpus/app/{builder_adapters.py,agent_product_runtime.py,source_composition.py}`
- Create or modify: narrow app adapters required by the consumer ports
- Test: focused Designer/Builder/Sandbox/Evaluation/Delivery/Source suites

- [x] Define immutable public Designer revision/build-request views in `designer.contracts`; Builder persistence and NavGraph compilation consume those views rather than Designer ORM models/schemas/topology internals.
- [x] Make Designer repository validation depend on an injected Agent-existence/lifecycle port instead of querying Agent ORM models.
- [x] Make Builder, Sandbox, Evaluation, Operations, Channels, and Deployment services depend on feature-local capability ports rather than provider services or concrete delivery integrations.
- [x] Implement those ports under `corpus.app`, preserving exact failures, lineage, eligibility, delivery, and review behavior.
- [x] Define Source-owned ToolRouter and API execution ports; concrete ToolRouter/API adapters remain in app composition.
- [x] Replace Evaluation generation imports of ToolRouter internals (`stable_hash`, normalized bundle loading) with injected Source/runtime capabilities or product-neutral shared helpers whose ownership is explicit.
- [x] Run focused suites and confirm no repository queries another feature's ORM model.

### Task 5: Move the complete Huey process composition under `corpus.app`

**Files:**

- Create: `backend/src/corpus/app/worker.py`
- Delete: `backend/src/corpus/features/sources/worker.py`
- Modify: `compose.yaml`
- Modify: `compose.production.yaml`
- Modify: `backend/tests/sources/test_worker.py`
- Modify or create: `backend/tests/runtime/test_worker_composition.py`
- Modify: runtime documentation references found by `rg 'corpus\.features\.sources\.worker'`

- [x] Add a failing runtime test that imports `corpus.app.worker.huey` with controlled settings and asserts Source, Builder assembly, Evaluation generation/run, and Deployment tasks are registered exactly once.
- [x] Move the current construction sequence unchanged into `corpus.app.worker`: settings, database, Source runtime, Agent runtime, Builder/Sandbox runtime, Evaluation, delivery, Channels, Deployment, then task registration.
- [x] Point local and production Compose consumers at `corpus.app.worker.huey`.
- [x] Remove the Sources worker module entirely; do not leave a forwarding import.
- [x] Run worker task tests, import smoke, and `docker compose config` plus `docker compose -f compose.production.yaml config`.

### Task 6: Make reviewed API revision identity generic

**Files:**

- Modify: `backend/src/corpus/features/sources/connectors/api/connection_checks.py`
- Modify: `backend/src/corpus/features/sources/connectors/api/route_plans.py`
- Modify: `backend/src/corpus/features/sources/connectors/api/routed_executions.py`
- Modify: `backend/src/corpus/features/sources/connectors/api/contracts.py` or Source-owned API port/value module
- Modify: `backend/tests/sources/test_api_connection_checks.py`
- Modify: `backend/tests/sources/test_api_route_plans.py`
- Modify: `backend/tests/sources/test_routed_api_execution_routedeck.py`

- [x] Add a non-Medusa reviewed API fixture whose canonical document hash differs from the accepted Medusa hash.
- [x] Add red tests proving connection check, route planning, and read/write execution accept only that fixture's exact selected `source_revision_id`, recorded `final_canonical_sha256`, owner, profile, curation, conversation, and RouteDeck session.
- [x] Add stale/tampered document tests proving byte hash and canonical hash drift fail before transport.
- [x] Replace every generic `MEDUSA_EFFECTIVE_CONTRACT_HASH` comparison/persistence with a helper that derives the selected reviewed revision's recorded canonical identity and verifies the persisted document against it.
- [x] Preserve exact one-call/no-retry, write-review, redaction, external-outcome-unknown, and safe operation semantics.
- [x] Run the focused Source route/check/execute suites and their RouteDeck recorder contract tests.

### Task 7: Extract Medusa 2.13.6 correction into an explicit acceptance adapter

**Files:**

- Create: `backend/src/corpus/integrations/medusa_acceptance/__init__.py`
- Create: `backend/src/corpus/integrations/medusa_acceptance/contract_revision.py`
- Modify: `backend/src/corpus/features/sources/connectors/api/contract_revisions.py`
- Modify: `backend/src/corpus/app/source_composition.py`
- Modify: `backend/src/corpus/features/sources/declarations.py`
- Modify: `backend/tests/sources/test_api_contract_revisions.py`
- Create: `backend/tests/integrations/medusa_acceptance/test_contract_revision.py`

- [x] Define a Source-owned `EffectiveContractPolicy`/plan protocol that returns a candidate only when the selected parent and evidence match.
- [x] Move `MEDUSA_EFFECTIVE_CONTRACT_PLAN`, its patch records, parent/local/evidence hashes, and Medusa-specific observed/declared text to the explicit integration package.
- [x] Make `ApiContractRevisionService` require an injected policy; it must have no Medusa default.
- [x] Select the Medusa acceptance policy explicitly in `create_source_runtime` for the accepted ecommerce pathway.
- [x] Add tests proving exact Medusa parent/evidence success, every mismatch fails closed, and an unknown API receives no automatic correction or synthetic candidate.
- [x] Replace generic owner-facing Source wording with `API definition`, `API version`, and `reviewed compatibility update`; retain Medusa naming only in integration evidence and focused acceptance tests.
- [x] Run generic and Medusa-specific contract-revision tests together.

### Task 8: Put frontend cross-feature state behind neutral contracts and shared presentation

**Files:**

- Create: `frontend/src/shared/agent/` modules for Agent selection store contract, operation-result helpers, shared build/runtime projections, and shared NavGraph presentation
- Create: `frontend/src/shared/conversation/Composer.tsx`
- Create: `frontend/src/shared/conversation/Conversation.tsx`
- Create: `frontend/src/shared/transport/contracts.ts`
- Modify: `frontend/src/app/{Composer.tsx,Conversation.tsx,transports.ts}` or move/remove obsolete owners
- Modify: `frontend/src/features/{builder,designer,evaluation,operations,delivery,sources}/**`
- Modify: frontend composition modules that instantiate stores and clients
- Test: affected frontend component tests

- [x] Add/update frontend checker fixtures before moving code so contracts and app-import failures are explicit.
- [x] Move generic Agent selection/store types and operation outcomes to neutral shared contracts; app still constructs the real Agent store.
- [x] Move build/runtime projection types and the reusable immutable NavGraph renderer to neutral shared ownership; do not re-export a feature implementation as a fake contract.
- [x] Move Composer/Conversation presentation out of app composition so the public delivery feature and owner shell consume the same shared components.
- [x] Move `AuthorizedTransport` interface to `shared/transport/contracts`; keep concrete transport creation in app.
- [x] Update Builder, Designer, Evaluation, Operations, Delivery, and Sources imports and component prop types without changing rendered behavior.
- [x] Run targeted Vitest files, then `pnpm --dir frontend test`, `pnpm --dir frontend typecheck`, and `pnpm --dir frontend build`.

### Task 9: Close the checker with zero violations

**Files:**

- Modify: any remaining files reported by `scripts/check_architecture_boundaries.py`
- Modify: `tests/test_architecture_boundaries.py` only for explicit architectural categories, never current-file exemptions

- [x] Run `\.venv\Scripts\python.exe scripts\check_architecture_boundaries.py` and classify every remaining line as misplaced contract, missing consumer port, app composition leak, or shared-infrastructure ownership issue.
- [x] Fix each owning boundary; do not add path ignores or a known-violation baseline.
- [x] Run `\.venv\Scripts\python.exe -m pytest tests\test_architecture_boundaries.py -q` and require the real-repository assertion plus all negative fixtures to pass.
- [x] Use `rg` to confirm no feature imports `corpus.app`, `corpus.runtime`, concrete `corpus.integrations`, `corpus.jobs.repository`, or another feature outside exact `contracts`.

### Task 10: Update durable instructions, skill, code map, and runtime references

**Files:**

- Modify: `architecture/components/corpus-feature-architecture.md`
- Modify: `architecture/components/corpus-routedeck-boundary.md`
- Modify: `architecture/components/api-execution-integration.md`
- Modify: `architecture/code-map.md`
- Modify: `test_index/README.md`
- Modify: runtime/deployment runbooks that name the old worker
- Modify: `skills/README.md`
- Create: `skills/audit-corpus-boundaries/SKILL.md`
- Modify: `context.md` and latest checkpoint only at completion if required by the repository closeout process

- [x] Use the repository skill-authoring instructions before creating the new skill.
- [x] Document the allowed/forbidden dependency matrix, public-contract criteria, consumer-port/app-adapter pattern, no-exemption rule, exact checker commands, interpretation, RouteDeck stop condition, and final verification order.
- [x] Update worker ownership and command everywhere from `corpus.features.sources.worker.huey` to `corpus.app.worker.huey`.
- [x] Document generic reviewed API identity separately from the explicitly selected Medusa acceptance adapter.
- [x] Keep audit/ADR/design/spec as historical decision evidence; do not duplicate their full prose into `context.md` or the skill.
- [x] Run reference searches for stale worker paths, global generic Medusa hash claims, and obsolete boundary rules.

### Task 11: Focused and broad local verification

**Files:**

- Test only; correct failures in their owning implementation or focused test fixture.

- [x] Run the architecture checker and its unit suite.
- [x] Run affected backend feature suites in coherent groups, then `\.venv\Scripts\python.exe -m pytest backend\tests -q`.
- [x] Run the full frontend test, typecheck, and production build gates.
- [x] Run worker import/task registration smoke and both Compose config validations.
- [x] Start the local backend/frontend/worker using the documented Compose path; report the exact command and smoke URLs `http://127.0.0.1:8099/health`, `http://127.0.0.1:8099/ready`, and `http://127.0.0.1:5199`.
- [x] Exercise bounded real paths for reviewed API revision, safe connection check, route planning/execution, and worker-driven Builder/Evaluation/Deployment transitions as required by changed seams.
- [x] Stop and fix the focused owner of any failure before proceeding; never weaken an assertion or introduce a fallback.

### Task 12: Final existing three-mode E2E acceptance and closeout

**Files:**

- Modify/create validation log and checkpoint artifacts only if fresh successful runs produce new evidence.

- [x] Confirm all focused gates are green before invoking the horizontal recorder.
- [x] Run surface, hybrid, and ordinary-chat modes sequentially with the exact current command documented in `test_index/README.md`; retain each run ID, assertion count, artifact path, diagnostics, and runtime location.
- [x] Verify accepted Medusa correction identity remains exact while generic Source tests continue to prove non-Medusa selected-revision behavior.
- [x] Review changed-file ownership through the repository documentation advisory and final architecture checker. Git diff/status were intentionally omitted because the implementation had no new Git-operation authorization.
- [x] Update only affected documentation owners and a concise restart checkpoint. Do not commit without separate owner authorization.
