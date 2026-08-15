---
name: audit-corpus-boundaries
description: Audit, explain, or enforce Corpus backend and frontend module boundaries. Use for dependency-boundary reviews, architecture-checker failures, new feature/module placement, cross-feature imports, composition ownership, worker ownership, public contract design, or API acceptance-policy separation in the authoritative Corpus repository.
---

# Audit Corpus Boundaries

Use the repository's executable boundary contract as evidence. Keep an audit
read-only unless the user authorizes fixes.

## Establish authority

1. Work only in the authoritative Corpus checkout.
2. Read `AGENTS.md`, `critical_prompt.md`, `context.md`, the latest checkpoint,
   `instructions.md`, `context_pipeline.md`, `architecture/code-map.md`,
   `architecture/components/corpus-feature-architecture.md`, and active plans
   relevant to the requested scope.
3. Treat the sibling RouteDeck repository as read-only. If an existing public
   RouteDeck contract cannot support the Corpus change, stop and report the
   exact missing contract.
4. Never modify `docs/corpus-agent-design/feature-behavior-notes.md`.

## Run the gate

From the repository root, run:

```powershell
.\.venv\Scripts\python.exe scripts\check_architecture_boundaries.py
.\.venv\Scripts\python.exe -m pytest tests\test_architecture_boundaries.py -q
```

The checker discovers every immediate backend and frontend feature directory.
Require zero repository violations. Do not add a baseline, current-file ignore,
or broad exemption.

## Apply the dependency rules

A backend feature may import its own modules, `corpus.shared`, public
`corpus.persistence`, public `corpus.jobs`, public `corpus.credentials`,
`corpus.auth.contracts`, and another feature's exact `contracts` module.

A backend feature must not import another feature's service, repository, ORM
model, schema, HTTP module, declaration, handler, or private port. It must not
import `corpus.app`, `corpus.runtime`, concrete `corpus.integrations`, or a
concrete shared-infrastructure repository.

A frontend feature may import itself, neutral shared/components/lib/RouteDeck
modules, and another feature's exact `contracts` module. It must not import
another feature's internals or application composition.

Keep public `contracts` modules narrow: stable identities, immutable boundary
views, and provider-owned public protocols only. Do not use them to re-export
implementation modules or ORM models.

When feature A consumes behavior owned by feature B, define the smallest
consumer capability in A and implement the adapter under `corpus.app`. Keep
process/task composition under `corpus.app`; each feature retains its task
factory, processor, business state, and failure semantics.

Generic API Source check, route, and execution paths must verify the exact
selected persisted reviewed revision. Medusa correction hashes and patches
belong only to the explicitly selected `corpus.integrations.medusa_acceptance`
adapter and its focused tests.

RouteDeck context-provider values supervise operation execution and are not
automatically model-visible. When the model must reason about current public
feature state, project the freshly loaded safe fields through the owning
feature's declared active Surface or entity contract using an existing Corpus
operation. Keep the exact provider/guard for execution-time truth. Add one
focused assertion against `routedeck_langgraph.build_model_context`; do not
infer model visibility from a passing provider test or from frontend API data.
If no existing RouteDeck public projection can carry the required state, stop
and report the missing framework contract instead of adding a Corpus-side
parallel context system.

Keep RouteDeck identity representations at their owning crossing. A
`ProviderInvocationContext` reads persisted `PrivateEntityBinding` values from
session state, where `private_id` is already a string. A guard or operation
receives `ResolvedEntityInput`, where `private_id` is a `SecretStr`. Never copy
`get_secret_value()` handling from a guard into a context provider. Provider
tests must construct a real `PrivateEntityBinding`, and the architecture
checker must reject execution-time secret unwrapping in `providers.py`.

For a selected entity crossing into another feature Node, compare that Node's
declared operations with the binding's `allowed_operation_ids`. The target
feature owns and exports its exact entity-bound operation tuple through
`contracts`; the transition handler imports it and must not repeat external
RouteDeck ID strings. Require a compiled-app regression that proves equality,
including review, retry, and navigation operations. RouteDeck should reject a
missing authorization; do not weaken its entity-resolution guard.

## Classify findings

For each finding, record:

- severity: HIGH when dependency direction, ownership, secret/failure truth,
  or future extraction is compromised;
- importing and imported owner;
- violated rule and exact file/line;
- smallest correct owner or consumer port;
- behavior that must remain unchanged;
- focused gate that proves the refactor.

Prefer moving composition to `corpus.app`, moving neutral types to `shared`,
or adding a narrow public contract/consumer port. Do not duplicate provider
behavior inside the consumer.

## Verify fixes

After each coherent slice, run its focused backend/frontend tests and rerun the
checker. Before completion, require:

1. checker and checker tests;
2. full backend suite;
3. frontend tests, typecheck, and build;
4. worker registration/import and both Compose config checks;
5. local runtime smoke at the documented URLs;
6. existing surface, hybrid, and ordinary-chat E2E only after focused gates
   are green.

Update only the owning architecture, code-map, test-index, decision/audit, and
runtime references. Report the exact runtime, commands, pass counts, remaining
limitations, and whether any E2E was rerun.
