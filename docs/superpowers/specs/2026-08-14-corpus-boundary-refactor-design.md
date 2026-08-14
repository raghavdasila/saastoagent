# Corpus boundary refactor design

Status: approved, implemented, and validated

Date: 2026-08-14

## Purpose

Refactor the three high-severity findings from
`audits/2026-08-14-present-system-boundary-audit.md` without changing accepted
Corpus product behavior:

1. enforce feature boundaries across every feature;
2. move complete worker composition out of Sources; and
3. separate Medusa acceptance policy from generic API Source execution.

The product already has accepted end-to-end evidence. This work preserves
those contracts at code level, proves each refactor through focused gates, and
runs the existing horizontal E2E only after the architecture and focused
runtime checks are green.

## Scope and authority

All implementation lives in `D:\Dev\AI Projects\saastoagent-v0.1`.

- No RouteDeck source change is required or authorized.
- The owner-authored Behavior Notes remain untouched.
- No new third-party dependency is required.
- No database migration or persisted-data rewrite is planned.
- No product operation, RouteDeck transition, review policy, public route,
  accepted prompt/policy text, or interaction-mode behavior is intentionally
  changed.
- Medium-severity build provenance, hard process/container isolation, and
  code-map overlap are documented but excluded.

## Selected architecture

Corpus remains a modular monolith with explicit feature contracts and
application-owned composition.

```text
feature domain
  -> consumer-owned port
    -> corpus.app adapter
      -> provider feature or concrete integration
```

RouteDeck remains the product-neutral legal interaction layer. The refactor
does not create a second workflow engine or application service bus.

## Dependency policy

### Backend feature imports

Allowed:

- the current feature's own modules;
- `corpus.shared` public primitives;
- `corpus.persistence` public database/base primitives;
- the root public interfaces of `corpus.jobs` and `corpus.credentials`;
- `corpus.auth.contracts` for declared owner context; and
- `corpus.features.<other>.contracts`.

Forbidden:

- another feature's services, repositories, models, schemas, HTTP problems,
  handlers, declarations, internal ports, or task processors;
- `corpus.app` and `corpus.runtime`; and
- concrete `corpus.integrations` packages.

If a stable shared-infrastructure interface currently exists only in a
concrete submodule, expose the minimal interface through its package's public
root or an explicit `contracts` module. Do not allow the concrete submodule in
the checker merely to avoid an export.

### Frontend feature imports

Allowed:

- the current feature;
- another feature's explicit `contracts` module;
- `shared`, generic UI primitives, and deliberately public integration view
  models; and
- RouteDeck public packages.

Forbidden:

- another feature's store, client implementation, Surface, or internal model;
- `app` composition modules; and
- application singletons.

Generic `Composer` and `Conversation` presentation needed by both the Corpus
owner shell and the public Agent move to a neutral shared owner. Transport
interfaces consumed by a feature move out of app composition; concrete
transport creation remains in `app`.

## Refactor slices

### Slice 1: Universal enforcement contract

Expand `scripts/check_architecture_boundaries.py` to discover all feature
directories rather than maintaining a hard-coded feature set.

The checker will:

- apply backend dependency rules to every backend feature;
- apply frontend rules to every frontend feature, including `delivery`;
- reject feature imports from `corpus.app`, `corpus.runtime`, and concrete
  integration modules;
- distinguish public infrastructure roots from concrete repositories;
- retain file and line diagnostics;
- have explicit tests for every allowed and forbidden category; and
- fail with no checked-in violation baseline or broad ignore list.

The checker changes and dependency refactors land together so the main branch
never treats a known failing architecture gate as acceptable.

### Slice 2: Public feature seams and application adapters

Classify every current cross-feature import as one of:

1. shared identity/navigation contract;
2. consumer-required capability;
3. orchestration/composition; or
4. misplaced shared presentation primitive.

Apply these conversions:

- shared RouteDeck Node/Operation identities needed for legal navigation move
  to the provider feature's `contracts` module;
- each consumer feature defines a narrow port for owner scope, Agent lookup,
  build lookup, evaluation promotion, Source lookup, or other required
  behavior;
- `corpus.app` adapters implement those ports with provider services;
- repositories query only their own feature models; cross-feature validation
  uses an injected gateway rather than another feature's ORM model;
- HTTP layers translate feature-owned errors rather than importing another
  feature's HTTP problem; and
- integration implementations are selected and injected by composition.

Public contracts contain stable IDs, commands, views, and protocol-level
types. They do not expose repositories, SQLAlchemy models, or concrete service
classes.

### Slice 3: Application-owned worker composition

Create an application worker entrypoint under `backend/src/corpus/app/`.

The entrypoint will:

- load the existing runtime settings once;
- create shared persistence and infrastructure once;
- compose the Source, Agent, Builder, Evaluation, Channel, Deployment, and
  delivery adapters explicitly;
- register each feature-owned task exactly once; and
- expose the Huey object required by `huey_consumer`.

Move local/production runtime commands and tests to the new module. Remove the
feature-owned entrypoint after all references move. Do not retain a forwarding
module in Sources.

Task business logic, result/error payloads, retry limits, and state transitions
remain in their owning features. Only concrete process composition moves.

### Slice 4: Generic API revision truth and Medusa acceptance adapter

Replace the global Medusa hash dependency in generic services with exact
selected-revision truth:

- route planning, connection checks, and routed execution load the selected
  persisted reviewed API revision;
- the document hash must equal that revision's own recorded canonical hash;
- Source, revision, connection profile, curation, owner, conversation, and
  RouteDeck session checks remain exact;
- no service resolves `latest` when an exact identity is unavailable; and
- read/write one-call, review, redaction, and no-retry semantics remain
  unchanged.

Move the predefined Medusa 2.13.6 correction plan and its known parent/evidence
matching behind an explicitly named acceptance integration. Application
composition supplies it only for the current accepted Medusa pathway. An
unknown API receives no automatic correction plan and no synthetic success.

Generic compiled product text uses `API definition`, `API version`, and
`reviewed compatibility update`. Medusa-specific names remain only in the
acceptance adapter, acceptance evidence, and focused tests.

Add at least one non-Medusa reviewed API test proving that generic planning and
execution depend on the selected revision rather than the Medusa hash. Existing
Medusa tests continue proving its exact plan, parent, patch, and hash boundary.

### Slice 5: Durable prevention and usage guidance

Update the owners that tell future work how to preserve the boundary:

- `architecture/components/corpus-feature-architecture.md`;
- `architecture/components/corpus-routedeck-boundary.md` when composition
  locations change;
- `architecture/components/api-execution-integration.md`;
- `architecture/code-map.md` for moved source ownership;
- `test_index/README.md` with exact checker commands and interpretation;
- runtime runbooks and Compose commands for the worker entrypoint;
- `skills/README.md`; and
- a repo-local `skills/audit-corpus-boundaries/SKILL.md` with triggers,
  authority read order, checker commands, classification rules, stop
  conditions, and verification checklist.

The skill must direct an agent to fix the owning boundary rather than add a
checker exemption. A missing RouteDeck contract remains a cross-repository stop
condition, not permission to duplicate framework behavior in Corpus.

## Error and failure semantics

- Dependency injection failures stop application or worker startup visibly.
- A missing consumer port or task registration is a construction error.
- Generic API services fail when the selected reviewed revision, document,
  profile, curation, owner, conversation, or session identity is inconsistent.
- The Medusa acceptance adapter fails when its exact parent/evidence contract
  does not match; it never applies a best-effort patch.
- Existing queue failures, explicit retries, RouteDeck reviews, external-
  outcome-unknown handling, and credential redaction are unchanged.

No compatibility fallback, service locator, dynamic import, or global registry
is introduced to conceal an unresolved dependency.

## Testing and acceptance

Verification proceeds from the smallest boundary to the complete product:

1. checker unit tests and the universal checker;
2. focused tests for every moved contract, adapter, repository, and task;
3. focused API Source generic and Medusa acceptance tests;
4. backend type/lint/test gates affected by the moves;
5. frontend tests, typecheck, and production build;
6. Docker/production Compose configuration and worker import/startup proof;
7. bounded real feature checks for any refactored runtime seam; and
8. the existing final horizontal surface-only, ordinary-chat-only, and hybrid
   E2E acceptance after every focused gate is green.

The horizontal journey is not used to locate import, composition, or fixture
defects. A failure returns to the owning focused gate before another complete
journey is attempted.

Because deployment topology is unchanged, this design does not authorize a
production deployment. A local successful E2E plus production-image/Compose
proof is the implementation completion boundary unless deployment is
separately requested.

## Completion criteria

The refactor is complete when:

- every current feature is governed by the same explicit checker;
- no forbidden backend or frontend feature import remains;
- no product feature composes the application or worker process;
- generic API execution has no global Medusa hash requirement;
- Medusa acceptance behavior remains exact and explicitly selected;
- all moved owners and repo-local instructions are current;
- focused gates are green; and
- the existing final three-mode E2E remains green with no requirement or
  assertion weakened.

## Excluded follow-up

- publishing or changing RouteDeck;
- extracting microservices;
- per-Agent containers, quotas, or hostile-code sandboxing;
- changing the deployed GCP topology;
- changing product behavior or widening feature completeness;
- resolving every medium-severity audit finding; and
- replacing the accepted E2E or its claim boundaries.
