# Step 3 Shared Infrastructure Dependency Provenance

Validated locally on Windows with Python 3.11. The reference environment and
downloaded wheels are retained under
`.runtime/reference-workflows/step3-dependencies/`.

| Dependency | Pin | Source | License | Wheel | SHA256 | Result |
| --- | --- | --- | --- | --- | --- | --- |
| Huey | 3.2.1 | https://pypi.org/project/huey/ and https://github.com/coleifer/huey | MIT | `huey-3.2.1-py3-none-any.whl` | `da9e004b80941a718f33f9714697a67e6d5cf12e0707fc4f3dbb5d9c796e7224` | Immediate task result and SQLite storage queue round-trips passed |
| PyNaCl | 1.6.2 | https://pypi.org/project/PyNaCl/ and https://github.com/pyca/pynacl | Apache-2.0 | `pynacl-1.6.2-cp38-abi3-win_amd64.whl` | `62985f233210dee6548c223301b6c25440852e13d59a8b81490203c3227c5ba0` | SecretBox round-trip and tamper rejection passed |

## Reference workflows

Huey was exercised through its documented `SqliteHuey` API in two focused
probes: an immediate decorated task returned its expected result, and a
non-immediate SQLite storage enqueue/dequeue round-trip persisted the expected
payload. The retained storage database is
`.runtime/reference-workflows/step3-dependencies/huey-reference.db`.

PyNaCl was exercised through its documented `SecretBox` API using a random
32-byte key: encrypt a byte payload with an automatically generated nonce,
decrypt it, mutate the authenticated ciphertext, and confirm `CryptoError`.

Exact installed-version check:

```powershell
.\.runtime\reference-workflows\step3-dependencies\.venv\Scripts\python.exe -c "import huey,nacl; print(huey.__version__); print(nacl.__version__)"
```

Expected and observed versions were `3.2.1` and `1.6.2`. The machine-readable
manifest is `contracts/dependency-provenance/step3-shared-infrastructure.json`.

## Integration boundary

- Huey is used only behind `DurableJobPort`; the Corpus SQLAlchemy rows remain
  authoritative for status, retry, and lifecycle evidence.
- PyNaCl `SecretBox` is used only inside the Corpus credential adapter. Feature
  services retain opaque references and never receive key material.
- No provider fallback, plaintext store, inline job fallback, sibling host,
  queue, UI, or authentication implementation was imported.
- At Step 3 completion, `openapi-core` remained at 0.22.0 and was not changed
  by that slice. It was later superseded by the approved API Execution Phase A
  baseline documented in
  `docs/dependency-provenance/2026-08-07-api-execution-phase-a.md`.
