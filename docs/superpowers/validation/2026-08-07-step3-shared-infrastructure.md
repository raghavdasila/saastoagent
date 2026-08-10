# Step 3 Validation: Shared Infrastructure

## Scope

This validation covers the non-visual infrastructure introduced for the first
mapped Source slice: Corpus-owned durable jobs, lifecycle records, encrypted
credential references, migration `0003_shared_infrastructure`, runtime settings,
and dependency provenance. No Source product behavior is activated by this
slice, and no API-execution dependency was changed.

## Reference workflows

Reference environment:
`.runtime/reference-workflows/step3-dependencies/.venv`

- Huey 3.2.1: immediate decorated-task result passed; non-immediate
  `SqliteHuey` storage enqueue/dequeue round-trip passed against
  `.runtime/reference-workflows/step3-dependencies/huey-reference.db`.
- PyNaCl 1.6.2: `SecretBox` encrypt/decrypt round-trip passed and a mutated
  ciphertext raised authenticated-decryption failure.
- Downloaded wheel hashes match
  `contracts/dependency-provenance/step3-shared-infrastructure.json`.

## Verification

| Command | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest backend/tests/jobs backend/tests/credentials backend/tests/infrastructure backend/tests/persistence/test_shared_infrastructure_migration.py -q` | 11 passed |
| `.\.venv\Scripts\python.exe -m pytest backend/tests -q` | 113 passed; one existing Starlette/httpx deprecation warning |
| `.\.venv\Scripts\python.exe scripts/check_architecture_boundaries.py` | Passed |
| `.\.venv\Scripts\python.exe scripts/check_agent_design_parity.py` | Passed |
| `docker compose config --quiet` | Passed |
| `.\.venv\Scripts\python.exe -c "import huey,nacl,openapi_core; print(huey.__version__, nacl.__version__, openapi_core.__version__)"` | `3.2.1 1.6.2 0.22.0` |

The focused tests cover owner isolation, persistence-before-enqueue, explicit
queue failure, job lifecycle and retry exhaustion, encrypted-at-rest storage,
secret-safe representations, rotation, wrong-key and tamper failure,
configuration failure, feature-owned task registration, and the exact migrated
schema.

## Current limitations

- No feature task is registered in the live product yet. The first Source slice
  must compose its own task and use these ports explicitly.
- The running Docker database has not been migrated or restarted by this
  infrastructure-only validation. Product activation will run the local
  initialization/migration path and report the smoke URL.
- At Step 3 completion, `openapi-core` remained `0.22.0`; this historical gate
  was later superseded by the separately approved API Execution Phase A 0.23.1
  baseline in
  `docs/superpowers/validation/2026-08-07-api-execution-phase-a.md`.
- There is no screenshot or video for this slice because it has no user-visible
  product surface. Visual evidence begins when Source behavior consumes it.
