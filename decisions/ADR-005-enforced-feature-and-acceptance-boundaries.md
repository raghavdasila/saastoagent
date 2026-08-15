# ADR-005: Enforced feature and acceptance boundaries

Status: accepted and implemented; local and deployed validation complete

Date: 2026-08-14

## Context

Corpus is a modular monolith whose product lifecycle crosses Lounge,
Workspace, Agents, Sources, Designer, Builder, Sandbox, Evaluation, Channels,
Deployment, and Operations. RouteDeck supplies the legal interaction topology
across that lifecycle.

The current ecommerce path works end to end and has accepted surface, ordinary
chat, and hybrid evidence. Functional success did not prevent the later
feature packages from accumulating direct imports of upstream services,
repositories, ORM models, HTTP errors, declarations, and concrete integration
adapters. The architecture checker covers only Lounge, Workspace, and Agents,
so it cannot prevent the same coupling from recurring elsewhere.

The production Huey entrypoint also lives in the Sources feature while
composing most of the product. Separately, the generic API Source path contains
one built-in Medusa correction plan and exact Medusa effective-contract hash.
That accepted vertical is valid product evidence, but it is not the generic API
Source contract.

Corpus needs codebase and team scalability now, and an affordable path to
runtime scaling later, without replacing a working v0.1 with premature
microservices.

## Decision

### Keep a modular monolith

Corpus remains one product repository and may continue to run as a backend,
worker, and frontend on one host. This ADR changes dependency direction and
ownership, not deployment topology.

### Enforce feature dependency inversion

A feature package may import:

- its own modules;
- stable product-neutral primitives under `corpus.shared` or
  `frontend/src/shared`;
- the declared public interfaces of shared infrastructure such as jobs,
  credentials, and persistence;
- `corpus.auth.contracts` where owner context is part of a RouteDeck
  declaration; and
- another feature's deliberately public `contracts` module.

A feature package must not import another feature's service, repository, ORM
model, schema, HTTP problem, handler, declaration internals, or private port.
It must not import `corpus.app`, `corpus.runtime`, or a concrete
`corpus.integrations` implementation.

When feature A needs behavior owned by feature B, feature A owns a narrow port
that describes only the capability it consumes. `corpus.app` owns the adapter
that implements that port with feature B's public service or contract.

Cross-feature navigation identities that are deliberately shared are public
contracts. RouteDeck continues to own whether an operation is currently legal
and whether its transition may commit.

The target feature also owns the exact operation IDs for which a cross-feature
selected-entity binding is authorized. Those IDs are exported from that
feature's public `contracts` module and must equal the target RouteDeck Node's
declared operations that consume the entity kind. A transition handler must not
copy external operation IDs into a second allowlist. Compiled-contract tests
prove equality, while the architecture checker rejects hard-coded external
RouteDeck IDs in the selected-Agent transition handler.

RouteDeck identity types remain specific to their crossing. Context providers
consume persisted `PrivateEntityBinding` values, whose `private_id` is a
string. Guards and operation handlers consume resolved execution inputs, whose
`private_id` is a `SecretStr`. Corpus provider code must not reuse guard-side
secret-unwrapping logic, and provider tests must use the persisted binding
contract rather than a shape-compatible mock.

### Put process composition in the application layer

The Huey consumer entrypoint and complete task registration move under
`corpus.app`. Each feature retains ownership of its task factory, processor,
business status, safe result, and failure semantics. The application worker
selects concrete repositories, adapters, and integrations and registers those
tasks exactly once.

No compatibility wrapper remains in `features.sources` after runtime commands
and documentation move to the application entrypoint; a wrapper would preserve
the forbidden dependency direction.

### Separate generic API truth from Medusa acceptance policy

Generic API connection checks, route plans, and routed execution validate the
exact selected, persisted, reviewed API revision. They do not compare it with
a global Medusa hash.

The existing Medusa 2.13.6 correction plan remains available only through an
explicitly named acceptance integration selected by application composition.
It may apply only when its known parent/source evidence matches. It must not
silently apply to an arbitrary API definition.

Owner-facing generic Source text uses API-definition and API-version language.
Medusa names remain valid in acceptance evidence, an explicitly selected
acceptance adapter, and Medusa-specific tests.

### Make enforcement universal and discoverable

The architecture checker discovers every backend and frontend feature
directory. It fails on disallowed concrete cross-feature imports and forbidden
feature-to-app/runtime/integration dependencies. Its own tests cover each
allowed and forbidden dependency category.

The checker, its exact invocation, interpretation, exemptions, and extension
rules are owned by:

- `scripts/check_architecture_boundaries.py`;
- `tests/test_architecture_boundaries.py`;
- `architecture/components/corpus-feature-architecture.md`;
- `test_index/README.md`; and
- a repo-local boundary-audit skill under `skills/`.

No permanent baseline, ignore list, or allow-any-current-violation mode is
accepted. Any narrow exemption must identify a public contract owner and be
represented as an explicit checker rule with a negative test.

## Alternatives considered

### Permit a documented downstream dependency graph

Later lifecycle features could be allowed to import upstream services directly
if every permitted edge were recorded. This would require less immediate
refactoring, but it would preserve persistence and transport coupling, make
cycles increasingly likely, and make future worker or service extraction
expensive. Rejected.

### Split features into microservices now

Independent services would provide deployment and failure isolation, but would
also introduce network contracts, distributed transactions, independent
deployments, service discovery, and operational overhead before the current
internal workload requires them. Rejected for this refactor.

### Keep the three-feature checker and rely on E2E

The accepted E2E proves product behavior, not dependency direction. It cannot
detect an ORM model, HTTP error, or composition import crossing the wrong
owner. Rejected.

### Treat Medusa as the launch API contract

This matches the current acceptance vertical but conflicts with Corpus's
generic API Source product meaning and future database, knowledge, and MCP
source families. Rejected. Medusa remains an explicit acceptance integration.

## Consequences

### Positive

- Feature code becomes independently understandable and testable.
- RouteDeck remains the legal cross-feature interaction layer instead of being
  shadowed by an implicit service graph.
- New source families and integrations can enter through narrow adapters.
- Background work can later move to a different process or service without
  moving feature domains.
- The checker prevents architecture regression before expensive E2E runs.

### Costs

- Some small public contract modules and consumer-owned ports will be added.
- Application composition will contain more explicit adapters and wiring.
- Shared frontend components currently owned by `app` or another feature must
  move to a neutral owner.
- Focused tests and imports will change even though product behavior does not.

### Risks

- Broad mechanical moves could alter dependency injection or task
  registration. The implementation must proceed in coherent slices and prove
  worker registration explicitly.
- Public `contracts` modules could become dumping grounds. They must contain
  stable boundary types and identities only, not provider implementation.
- A generic API revision check could accidentally weaken Medusa validation.
  Medusa parent/evidence matching remains strict inside its explicit adapter.

## Validation

The decision is implemented only when:

1. the universal architecture checker passes with no baseline exemptions;
2. its negative tests prove every forbidden dependency category;
3. backend and frontend focused suites, typechecks, and builds pass;
4. local backend and Huey worker start from the new application entrypoint and
   register every required task exactly once;
5. generic API tests use non-Medusa reviewed revisions successfully while the
   Medusa acceptance adapter retains exact parent/hash failure semantics; and
6. the existing final horizontal surface, ordinary-chat, and hybrid E2E checks
   pass after focused verification is green.

The universal checker also rejects `private_id.get_secret_value()` in feature
provider modules, with a negative test that proves the persisted-versus-
execution identity boundary.

The horizontal E2E is the final acceptance gate, not the refactor debugger.

Implementation completed on 2026-08-14. The universal checker reports zero
violations without exemptions; the complete root, backend, and frontend suites
pass; both Compose configurations parse; the application-owned worker starts
and registers the required tasks; and fresh Surface, Hybrid, and Chat journeys
passed 39/39, 40/40, and 39/39 respectively. Exact commands, run IDs, runtime
locations, and claim boundaries are recorded in
`docs/superpowers/validation/2026-08-14-corpus-boundary-refactor.md`.

## Follow-up

Medium-severity source-provenance, hard runtime isolation, and code-map primary
ownership questions remain separate follow-up decisions. They are not silently
included in this refactor.
