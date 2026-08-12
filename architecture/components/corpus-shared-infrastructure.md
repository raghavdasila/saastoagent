# Corpus Shared Infrastructure

## Purpose and boundary

Corpus owns one reusable infrastructure seam for durable asynchronous work and
write-only credentials. `corpus.jobs` defines the `DurableJobPort` contract and
persists job truth plus lifecycle events in the central Corpus database.
`corpus.credentials` owns opaque credential references and encrypted payloads.
`corpus.app.infrastructure` is the only concrete composition hook.

This layer does not own Source, Agent, build, Sandbox, evaluation, delivery, or
RouteDeck behavior. It does not start a worker or register a product task by
itself. A consuming feature supplies a task factory that registers its task on
the composed Huey instance and retains ownership of business processing and
safe result/error payloads.

## Durable job flow

```text
feature service requests enqueue
  -> Corpus durable_jobs row and enqueued lifecycle event commit
  -> Huey receives only opaque Corpus job UUID plus attempt number
  -> feature-owned worker loads job and marks running
  -> worker records succeeded result or explicit failed code/message
  -> owner-scoped status reads Corpus truth
  -> explicit retry is allowed only from failed while attempts remain
```

If Huey rejects enqueue, Corpus records `queue_unavailable` and raises
`DurableJobEnqueueError`. It never runs work inline or substitutes an in-memory
queue. Attempts increment only when work starts. Historical state transitions
remain in `durable_job_events`.

Builder consumes this seam through `builder.assemble`: the web process first
persists a queued immutable attempt, enqueues only its opaque job/build/request
identities, and returns. The source worker marks the exact attempt running,
rechecks the accepted design and Source bindings, materializes the immutable
build, and records ready/failed truth. Queue rejection is a visible failed
attempt; there is no inline fallback or automatic retry.

## Credential flow

```text
owner supplies secret values over a private product surface
  -> Corpus creates opaque UUID reference
  -> PyNaCl SecretBox encrypts a bound JSON envelope with a random nonce
  -> only ciphertext and non-secret metadata persist
  -> owner-scoped adapter resolves plaintext only at execution time
```

`CORPUS_CREDENTIAL_VAULT_KEY` must be URL-safe base64 that decodes to exactly
32 bytes. Missing or invalid key material fails configuration. The encrypted
envelope binds owner ID, reference ID, and version; wrong-key, tamper, or row
swapping fails as `CredentialAuthenticationError`. Public metadata never
contains the secret payload, and errors contain no credential values.

## Persistence and configuration

- Infrastructure introduction: Alembic revision `0003_shared_infrastructure`.
- Current Builder consumer schema: `0019_builder_assembly_lifecycle` adds the
  exact durable job binding and queued/running/ready/failed attempt lifecycle.
- Corpus tables: `durable_jobs`, `durable_job_events`,
  `credential_references`.
- Huey local queue: `CORPUS_JOB_QUEUE_PATH`; it is scheduling transport, not
  authoritative product state.
- Credential key: `CORPUS_CREDENTIAL_VAULT_KEY`; supplied through the
  environment and never persisted in a Corpus table.
- Local setup generates the key once and migration startup remains explicit.

## Dependency provenance

Huey 3.2.1 and PyNaCl 1.6.2 are exact runtime pins. Their source, license,
wheel hashes, reference commands, and local evidence are recorded in
`docs/dependency-provenance/2026-08-07-step3-shared-infrastructure.md` and
`contracts/dependency-provenance/step3-shared-infrastructure.json`.

No sibling runtime source was copied in this slice.

## Verification

- `backend/tests/jobs/**`: persistence-before-enqueue, owner isolation,
  explicit failure/retry, retry exhaustion, lifecycle records.
- `backend/tests/credentials/**`: encrypted-at-rest values, metadata boundary,
  owner isolation, rotation, wrong-key and tamper failure.
- `backend/tests/infrastructure/**`: required queue/key configuration and exact
  key decoding.
- `backend/tests/persistence/**`: Alembic head and exact schema.

Run `\.venv\Scripts\python.exe -m pytest backend\tests -q` from the repository
root. These tests protect infrastructure contracts; they do not claim a Source
or other feature is using the new seam yet.
