# Present-system boundary audit

Date: 2026-08-14

Status: complete audit; all three high-severity findings remediated and validated

## Question

Which boundaries define the current Corpus system, which of them are presently
respected, and which implementation seams undermine the product's intended
modular-monolith architecture?

This audit treats a boundary as an ownership and crossing rule, not merely a
folder boundary. A concern has one authoritative owner. Other concerns cross
into it only through an explicit public contract while retaining identity,
state, security, failure, and evidence semantics.

## Authority and repository boundary

- `D:\Dev\AI Projects\saastoagent-v0.1` is the authoritative Corpus checkout.
- `D:\Dev\AI Projects\routedeck` was inspected read-only. It was not changed.
- `docs/corpus-agent-design/feature-behavior-notes.md` was read as owner
  authority and was not changed.
- No Git operation was performed during the audit.
- The ignored benchmark and stale Studio/runtime prototypes were not treated as
  current implementation truth.

## Boundary model

The present system must preserve these boundaries:

1. **Repository authority:** Corpus, RouteDeck, owner-authored notes, historical
   evidence, and external runtimes retain separate authority.
2. **Product and framework:** Corpus owns product meaning, persistence,
   adapters, routes, Surfaces, and owner-visible language. RouteDeck owns legal
   topology, navigation, reviews, projections, and session mechanics.
3. **Feature ownership:** Lounge, Workspace, Agents, Sources, Designer,
   Builder, Sandbox, Evaluation, Channels, Deployment, and Operations are
   vertical product slices rather than layers in one implicit service chain.
4. **Design and implementation:** Studio owns product semantics; the manifest
   owns technical mapping; compiled source owns runtime implementation.
5. **Identity and lineage:** owner, conversation, Source revision, Agent
   version, design revision, build, evaluation, deployment, and interaction
   identities remain exact and immutable.
6. **Runtime isolation:** Corpus, each built Agent, Sandbox sessions, and public
   deployed sessions retain separate state and results.
7. **Trust and visibility:** credentials remain in private Surfaces and the
   vault; public users do not receive owner diagnostics, raw framework state,
   internal identifiers, or credentials.
8. **Safety and failure:** writes require a current review; failures stay
   failures; retries are explicit; unavailable dependencies do not select a
   hidden fallback.
9. **Integration scope:** generic Source and Agent behavior depends on narrow
   integration ports. A particular acceptance target cannot silently become a
   generic product contract.
10. **Evidence and claims:** the accepted Medusa ecommerce path proves that
    exact vertical. It does not prove every generic API or every Behavior Note
    row, a production SLA, or hard process/container isolation.

## Evidence collected

### Passing gates

```powershell
.\.venv\Scripts\python.exe scripts\check_architecture_boundaries.py
.\.venv\Scripts\python.exe scripts\check_agent_design_parity.py
```

Both returned zero. The architecture result is limited by its hard-coded
governance set; the parity result covers the saved Studio state, implementation
manifest, and compiled Corpus application.

The current public deployment returned HTTP 200 for both:

- `https://corpus.saastoagent.com/healthz` -> `{"status":"ok"}`
- `https://corpus.saastoagent.com/readyz` -> `{"status":"ready"}`

A read-only search of `routedeck_core`, `routedeck_fastapi`,
`routedeck_langgraph`, `routedeck_sqlalchemy`, and the RouteDeck TypeScript
packages found no Corpus, Medusa, or ToolRouter product literals.

### Expanded import-boundary probe

The existing checker rule was applied in memory to all current backend and
frontend feature directories without changing repository files. It found:

- 64 direct backend internal cross-feature imports;
- 34 affected backend files;
- 19 backend feature-to-feature dependency edges; and
- 29 frontend boundary violations across 11 files.

These counts exclude imports through another feature's `contracts` module.
They are architectural dependencies, not a claim that the current product
journey is functionally broken.

### Focused invariant tests

Focused credential-vault, authentication, API-execution redaction, public
projection, owner/session scope, and delivery tests produced 17 passes and 3
failures.

The failures were:

1. a public-projection assertion that predates the public-safe
   `pending_action_review` field; and
2. two route-plan scope/redaction tests whose fixtures no longer reach their
   intended assertions because the implementation first rejects any effective
   contract hash other than the exact Medusa acceptance hash.

No credential disclosure or proven cross-owner data access was observed. The
failures show that the boundary evidence is stale and incomplete, not that the
affected privacy invariants failed.

## High-severity findings

### H1. Universal feature boundaries are declared but not enforced

`architecture/components/corpus-feature-architecture.md` permits direct
cross-feature imports only through the target feature's public contracts and
requires concrete adapters to be wired centrally. The checker governs only
`agents`, `lounge`, and `workspace`.

Later features directly import other features' services, repositories, ORM
models, HTTP problems, handlers, declarations, and internal ports. Examples
include:

- Designer importing Agents models, services, operations, and HTTP problems;
- Builder importing Agents services, Designer ORM models/topology internals,
  and Sources declarations;
- Evaluation importing Builder and Sandbox services plus the concrete API
  Source ToolRouter bridge;
- Operations importing EvaluationService;
- Channels importing Deployment schemas and declarations; and
- frontend feature components importing other feature stores/models and app
  composition modules.

This turns the accepted product lifecycle into an implicit dependency graph.
It increases change blast radius, lets persistence and transport details cross
domain ownership, and makes later worker/service extraction expensive.

### H2. The Source worker is an application composition root

`backend/src/corpus/features/sources/worker.py` composes Sources, Agents,
Builder, Evaluation, Channels, Deployment, the neutral delivery runtime,
shared jobs, persistence, and application adapters. Both local and production
runtime configuration start this module as the Huey consumer.

The Source feature therefore owns the startup and concrete wiring of unrelated
downstream features. This is a dependency-direction inversion. Worker process
composition belongs in `corpus.app`; features should contribute their own task
registration factories and public worker contracts.

### H3. Medusa acceptance behavior crosses the generic API Source boundary

The generic API connector's contract revision, connection check, route-plan,
and routed-execution paths depend on one global
`MEDUSA_EFFECTIVE_CONTRACT_HASH` and a built-in Medusa 2.13.6 correction plan.
Compiled owner-facing policy and operation text also names the local Medusa
compatibility update.

The current accepted behavior is valid evidence for the Medusa ecommerce
vertical, but the executable restriction sits inside the generic API Source
core. An arbitrary reviewed API definition cannot use the same route-planning
and execution path. This is both a product claim boundary and an integration
ownership violation.

## Medium findings retained for later work

1. RouteDeck remains repository- and governance-separated, but Docker builds
   copy the mutable sibling source and frontend packages use sibling `link:`
   dependencies. Deployed image digests pin artifacts, but the retained
   production evidence does not identify the exact RouteDeck source revision.
2. Built-Agent state is isolated by exact build-derived RouteDeck database,
   tenant, session, and build identities, but all Agents share the same
   backend/worker host. This is logical isolation, not a process, container,
   quota, or hostile-code sandbox claim.
3. The code map contains overlapping ownership, including Evaluation source in
   both the Builder/Sandbox row and the Evaluation row. Cross-cutting glob
   coverage is useful, but it is not a single primary owner.
4. The checker and focused boundary tests can report green while substantial
   later-feature coupling and stale invariant assertions remain outside their
   effective coverage.

## Boundaries presently holding

- RouteDeck runtime packages remain product-neutral in the inspected source.
- Studio-to-compiled-RouteDeck parity passes and technical IDs remain outside
  Studio state.
- The current credential-vault, JIT resolution, redaction, and public/owner
  projection implementation retains its intended trust boundary in the
  inspected code and passing focused tests.
- External writes retain separate RouteDeck review gates and no-call-before-
  review semantics.
- Built-Agent RouteDeck state is persisted per exact build-derived NavGraph;
  Sandbox/public sessions do not reuse the Corpus owner conversation store.
- The public deployment was healthy and ready at audit time.

## Accepted remediation direction

Retain a modular monolith. Do not introduce microservices as part of this
refactor.

Every feature may depend on itself, stable shared primitives, public shared
infrastructure interfaces, and deliberately public contracts from another
feature. A feature that needs behavior owned elsewhere declares a narrow
consumer-owned port. `corpus.app` implements and wires that port using the
provider feature or integration. Concrete services, repositories, ORM models,
HTTP errors, integration adapters, and application composition do not cross
feature boundaries.

The approved remediation is recorded in
`decisions/ADR-005-enforced-feature-and-acceptance-boundaries.md` and designed
in
`docs/superpowers/specs/2026-08-14-corpus-boundary-refactor-design.md`.

## Audit limitations

- This was not a full security review or database-content audit.
- GCP IAM, firewall, Secret Manager, backup contents, and private Medusa health
  were not re-read from the live control plane.
- The complete backend/frontend suites and the horizontal E2E were not rerun.
- No source was changed to test a proposed boundary repair.

## Remediation status

ADR-005 has now been implemented and validated. The universal checker
discovers every backend and frontend feature
and currently reports zero violations without a baseline. Worker composition
is owned by `corpus.app.worker`; cross-feature service/repository/model imports
were replaced by public contracts, consumer ports, shared neutral types, and
application adapters; frontend composition/presentation seams are neutral;
generic API check/route/execute paths use the selected persisted reviewed
revision; and the Medusa 2.13.6 plan is isolated in the explicitly selected
`corpus.integrations.medusa_acceptance` adapter.

Fresh completion evidence is green: root Python 98/98, backend 532/532,
frontend 188/188, TypeScript and production build, local and production
Compose parsing, the repo-local boundary skill validator, four live HTTP 200
smokes, and three independent local horizontal journeys (Surface 39/39,
Hybrid 40/40, Chat 39/39). See
`docs/superpowers/validation/2026-08-14-corpus-boundary-refactor.md` for exact
commands, run IDs, and artifact paths.

The original findings and limitations above remain the audit-time record; they
are not rewritten as if the initial scan had observed the remediated state.
