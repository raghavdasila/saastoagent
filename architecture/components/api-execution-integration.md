# API Execution Integration

## Current boundary

Phase A established a neutral, hash-pinned execution foundation. Corpus owns
`corpus.integrations.api_execution`; the unchanged sibling `0.1.0` modules
live under its private `_snapshot` package. Phase C adds one narrow
Corpus-owned adapter consumed only by the Source safe connection-check service.
It is not a generic execution host, queue, session, route planner, or second
Source owner.

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
The adapter validates the request and response against the exact effective
`6fca793b...` contract and permits one transport call with no retry or fallback.
It returns only redacted execution identity and call/validation counts.

Corpus persists the immutable safe result through the existing Source owner.
Headers, query values, request/response bodies, cookies, credentials, and
exception text do not cross into RouteDeck arguments, DTOs, traces, DOM, logs,
or evidence. Connection checks do not authorize operation curation, route
planning, or generic read/write execution. See
`docs/superpowers/validation/2026-08-08-api-connection-check-phase-c.md`.
