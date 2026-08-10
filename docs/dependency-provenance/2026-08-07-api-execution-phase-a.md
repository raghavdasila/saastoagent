# API Execution Phase A Dependency Provenance

## Approved baseline

| Dependency | Pin | License | Purpose |
| --- | --- | --- | --- |
| Python | `>=3.11,<3.12` | PSF | Corpus backend runtime |
| openapi-core | `0.23.1` | BSD-3-Clause | OpenAPI request and response validation |
| httpx | `0.28.1` | BSD-3-Clause | Injected asynchronous HTTP transport |
| openapi-spec-validator | `0.8.5` | Apache-2.0 | OpenAPI document validation |
| prance | `25.4.8.0` | MIT | OpenAPI parsing and reference resolution |

The Prance `osv` extra is deliberately absent because its dependency range
conflicts with the approved `openapi-spec-validator==0.8.5` pin. Corpus pins
and verifies the validator directly.

## Neutral snapshot

The source is the owner-authorized local
`D:\Dev\AI Projects\api-execution-runtime` package at version `0.1.0`.
`backend/src/corpus/integrations/api_execution/_snapshot/source_manifest.json`
is the machine-readable authority for the nine source and vendored hashes.
Every included module is byte-identical to its source.

Internal source snapshot. Owner-authorized for use within Corpus. Source: local
sibling api-execution-runtime 0.1.0. No public redistribution license has been
established for this snapshot; do not publish or redistribute it until
licensing is resolved or it is replaced by an independently licensed
implementation. `httpx==0.28.1` and `openapi-core==0.23.1` remain BSD-3-Clause
dependencies under their own licenses.

The sibling initializer, adapters, codec, SQLite store, jobs, worker, host,
demo, proof scripts, authentication, and UI are excluded. Phase A adds no
product invocation.

## Reference verification

- `pip check` verifies the installed dependency closure.
- Prance parses its official minimal form through the pinned validator.
- The unchanged snapshot validates request and response objects through
  openapi-core 0.23.1 and executes a read through an injected transport.
- The real Medusa probe and its repaired-contract chain are recorded in the
  matching Phase A validation log. Secrets, headers, and response bodies are
  not retained.

The completed chain audit retained raw canonical hash `a3dbb864...`, one
explicit ToolRouter repair with manifest hash `dc712d7c...`, validated repaired
parent `bc1b4b24...`, and final ten-patch executable contract
`6fca793b...`. Only after both pinned validators passed did the unchanged
runtime make one successful redacted GetProductTypes read. The exact values
and allowlisted trace keys are in
`.runtime/audits/20260807-api-execution-contract-chain/contract-chain-audit.json`.
