# API Execution Neutral Snapshot Provenance

## Source and authorization

- Source checkout: `D:\Dev\AI Projects\api-execution-runtime`
- Source package: `api-execution-runtime==0.1.0`
- Capture date: 2026-08-07
- Target: `corpus.integrations.api_execution._snapshot`

Internal source snapshot. Owner-authorized for use within Corpus. Source: local
sibling api-execution-runtime 0.1.0. No public redistribution license has been
established for this snapshot; do not publish or redistribute it until
licensing is resolved or it is replaced by an independently licensed
implementation. `httpx==0.28.1` and `openapi-core==0.23.1` remain BSD-3-Clause
dependencies under their own licenses.

The source checkout has no public redistribution license recorded for this
snapshot. This transfer is an internal, same-owner integration only. The exact
source and vendored SHA-256 values are recorded in `source_manifest.json`.

## Included neutral closure

The snapshot contains only `contracts`, `errors`, `ports`, `compiler`,
`plugins`, `security`, `validation`, `runtime`, and `contract_revision` from
the sibling package. The copied files are byte-for-byte unchanged.

`_snapshot/__init__.py` is a new minimal Corpus-owned restricted initializer.
It is not copied from the sibling and exposes no sibling host, adapter, job,
worker, persistence, demo, authentication, or UI implementation.

## Explicit exclusions

The sibling initializer, adapters, codec, SQLite contract store, jobs, worker,
demo, proof scripts, host state, and UI are not copied. Corpus will own any
future adapter, persistence, job, redaction, and product-orchestration layer.
Phase A does not wire this snapshot into Sources or any product behavior.

## Dependency baseline

- Python `>=3.11,<3.12`
- `openapi-core==0.23.1` (BSD-3-Clause)
- `httpx==0.28.1` (BSD-3-Clause)
- `openapi-spec-validator==0.8.5` (Apache-2.0)
- `prance==25.4.8.0` (MIT)

The `osv` extra is deliberately not requested from Prance because its
dependency range conflicts with the approved `openapi-spec-validator==0.8.5`
baseline. Corpus pins the validator directly and validates the Prance parser
against that exact installation.

