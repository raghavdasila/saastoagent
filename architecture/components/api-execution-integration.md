# API Execution Integration

## Current boundary

Phase A established a neutral, hash-pinned execution foundation. Corpus owns
`corpus.integrations.api_execution`; the unchanged sibling `0.1.0` modules
live under its private `_snapshot` package. Corpus now has two narrow adapters:
the Phase C Source connection-check adapter and a separate routed adapter used
only after an exact current Source plan or immutable assembled-Agent operation
has been resolved. This integration is not a generic execution host, queue,
session, route planner, or second Source owner.

The restricted snapshot contains only contracts, errors, ports, compiler,
plugins, security, validation, runtime, and contract-revision logic. Corpus did
not copy the sibling initializer, adapters, codec, SQLite store, jobs, worker,
host, proof scripts, demo, authentication, or UI.

## Provenance and dependencies

`source_manifest.json` records the exact source and vendored SHA-256 for every
unchanged file. `PROVENANCE.md` records the internal owner authorization and
the absence of a public redistribution license. The approved runtime baseline
is Python `>=3.11,<3.12`, `openapi-core==0.23.1`, `httpx==0.28.1`,
`openapi-spec-validator==0.8.5`, and `prance==25.4.8.0`. Prance's `osv` extra is
not used because it conflicts with the approved validator pin.

## Validation boundary

Focused tests verify byte identity, import isolation, exact dependency pins,
official minimal Prance parsing, openapi-core request/response compatibility,
and one validated read through an injected transport. The real local Medusa
reference is separate evidence: the raw official-current document is expected
to pass through the existing ToolRouter invalid-default repair before any
execution attempt. A raw-contract failure before transport is not an execution
success and records zero API calls.

## Phase C safe-read boundary

The adapter receives an owner/revision/profile-bound target, a safe operation
identity (`GetProductTypes` or `GetProductTags`), and an opaque credential
reference/version. The credential vault resolves that secret just in time.
The adapter validates the request and response against the exact canonical
document hash recorded by the selected persisted reviewed Source revision and
permits one transport call with no retry or fallback.
It returns only redacted execution identity and call/validation counts.

Corpus persists the immutable safe result through the existing Source owner.
Headers, query values, request/response bodies, cookies, credentials, and
exception text do not cross into RouteDeck arguments, DTOs, traces, DOM, logs,
or evidence. Connection checks do not authorize operation curation, route
planning, or generic read/write execution. See
`docs/superpowers/validation/2026-08-08-api-connection-check-phase-c.md`.

## Routed read/write boundary

The routed adapter accepts one exact operation, reviewed effective API
definition, parameter binding, target, profile-managed credential identity,
and optional internal write-approval marker. It validates the request before
transport, resolves the credential just in time, makes at most one call, and
validates the response. There is no automatic retry, alternate operation,
cached success, or body-shaped fallback.

Source route-plan execution owns immutable single-use claim/result persistence.
Assembled Sandbox and hosted-Agent runtimes own their session/run records and
call the same narrow execution boundary through Corpus adapters. RouteDeck
still owns whether a write has an accepted current review. The adapter treats a
missing approval marker as a pre-transport failure.

The explicitly selected `corpus.integrations.medusa_acceptance` chain for the
accepted local Medusa 2.13.6 vertical ends at canonical hash
`c0b9c6bf1b149a0e458de9fbda4f7bad3cf6f9f7eb4ff383bded3b09d23e50ef`.
It adds reviewed response-identity schemas for `GetProducts` and
`PostCartsIdLineItems` without retaining response bodies. The product runtime
may retain only the validated product variant and cart IDs needed for the same
session's next explicitly requested operation.

Generic connection checks, route plans, routed execution, and Source UI do not
compare against that Medusa hash. They require the exact selected revision,
owner, profile/curation lineage, recorded canonical hash, and verified
persisted document. An unrelated reviewed API revision may therefore execute
without receiving or inheriting Medusa corrections.

Current surface, ordinary-chat, and hybrid journeys independently prove one
validated `GetProducts` call, zero calls before each write review, one approved
`PostCarts` call, and one separately approved `PostCartsIdLineItems` call. See
`docs/superpowers/validation/2026-08-13-horizontal-ecommerce-chat-surface-hybrid.md`.
