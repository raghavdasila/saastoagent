# API Connection Check Phase C Validation

Date: 2026-08-08 IST

## Delivered boundary

Corpus now performs an explicit safe API connection check from `sources.home`.
The owner selects an exact ready effective revision, a revision-bound encrypted
profile, and either `GetProductTypes` or `GetProductTags`. RouteDeck owns the
`sources.test_api_connection` `read_external`/no-review operation. Corpus
rechecks owner, Source, revision, profile and credential version immediately
before resolving the credential and making one validated request through the
Phase A adapter. There is no retry or fallback.

Only immutable redacted result identity is persisted: Source/revision/profile,
operation, exact effective contract hash, status, safe error code, HTTP status,
validation issue count, call count and allowlisted trace identity. Headers,
query values, request/response bodies, cookies and credential values are not
persisted or emitted in evidence.

This phase does not implement operation curation, route planning, generic read
or write execution, clarification, Designer, or later lifecycle work. The
Studio static SuggestedAction remains separately unmapped because it cannot
truthfully carry unresolved dynamic Source/revision/profile/operation inputs.

## Automated gates

- Phase C Sources/snapshot/recorder focus:
  `64 passed, 6 warnings`.
- Auth, conversation, Workspace and stable NavGraph focus:
  `27 passed, 1 warning`.
- Full backend: `208 passed, 6 warnings`.
- Full frontend: `15 files, 80 tests passed`.
- Frontend strict typecheck: passed.
- Frontend production build: passed with the existing large-chunk warning.
- Frontend contract export check, Studio parity, and architecture boundary
  checks: passed.
- Recorder-only sign-out diagnostic regression: `11 passed`.
- Independent implementation and recorder reviews: approved with no Critical,
  Important, or Minor findings.

The NavGraph hash incident observed in earlier evidence was traced to
`allowed_sources` frozenset serialization order. Corpus now canonicalizes only
that unordered array at RouteDeck's public compiled-contract document seam.
Two fresh processes with `PYTHONHASHSEED=1` and `2` both produce
`66593d52cfcba07c61b1b686966ea31344a2fe5bdc943112cfe09c73250d3df2`.
Real contract changes still change the hash; semantic arrays retain order.
Adopted auth rows and matching SQL RouteDeck sessions pass close/reopen tests.
No alternate-hash recovery was added, so a pre-fix session carrying the other
nondeterministic hash remains truthfully upgrade-incompatible.

## Local runtime

- Command: `docker compose build backend source-worker`
- Command: `docker compose up -d --force-recreate backend source-worker`
- Backend: `http://127.0.0.1:8099/readyz` -> 200 ready
- Frontend: `http://127.0.0.1:5199` -> 200
- Medusa: `http://127.0.0.1:9100/health` -> 200 OK
- Source worker: running
- Alembic: `0006_restrict_agent_attachment_delete (head)`

## Final browser evidence

Command:

```powershell
.\.venv\Scripts\python.exe scripts\run_api_connection_check_journey.py --url http://127.0.0.1:5199
```

Run `20260807T201347Z-311a9da2f3` retained all eight passing behavioral
assertions:

1. fresh Source processing reached ready with zero inventory 500s;
2. the exact repaired/approved `6fca793b...` revision was created;
3. the protected valid profile made one validated `GetProductTypes` call,
   HTTP 200, zero validation issues;
4. the invalid credential made one call and remained a visible persisted
   `api_error_response` failure;
5. mobile reload retained both redacted records with strict 390x844 bounds;
6. both check identities survived backend restart;
7. a second owner saw zero Sources and no check history;
8. only the six bounded Source/Workspace operations were observed and check
   call counts were exactly `[1, 1]`.

Exact identities:

- Source: `9-EUJW8MjTbRM2VB`
- parent revision: `ShRWEiacVuGUDtci`
- durable job: `5e0683eb-02b6-4c59-8389-fc383c10ce7c`
- proposal: `Wnk7MO92ZYiLg4r9`
- RouteDeck review: `review_vwd6KlBqL5OR_7Fchw5qkXhY`
- approved revision: `dwqe_gT8RVmwH63x`
- valid profile/check: `ysYWlHUBiC6MfHnH` / `CP2bozfUF7n4uYa9`
- invalid profile/check: `0E8TER2iWBgFjQuZ` / `zeDR9otUZa1aoHUd`

The immutable `result.json` status remains `failed`, not rewritten. Its sole
unexpected diagnostic is Playwright `net::ERR_ABORTED` for
`POST /api/auth/sign-out`. The backend access log proves that exact request
completed with 204 before public Lounge and second-owner registration; the
second-owner isolation assertion also passed. This is therefore a recorder
diagnostic false-negative, not a failed product behavior. The offline recorder
fix now classifies that abort only when the same page first observed the exact
204 response; it was independently approved and was not browser-rerun.

Evidence directory:
`artifacts/api-connection-check/20260807T201347Z-311a9da2f3/`

- `result.json` SHA-256
  `1ec83e20e7ca5b92166988ac31a76b8b70c9d062729e805d2fc04b76a1a92254`
- `corpus-trace.json` SHA-256
  `fa1a849d5a022f65537b9ab1ebdbb485853753abcf1801ef90b5887267ac636c`
- continuous WebM SHA-256
  `3c39f27f8486cced231636a1add36ad6684db71968c203a6122ea42a52993ed6`
- six screenshots: desktop success/failure, mobile controls/failure, restart
  history, and second-owner empty inventory.

All six screenshots were visually inspected. The two mobile capture files are
byte-identical because the same strict viewport truthfully contains both the
controls and visible failed-result heading; they are not claimed as distinct
visual states. The 208-event Corpus trace contains only `sequence`, `event`,
`method`, `path`, `status`, `disposition`, `operationId`, `outcome`,
`failureCode`, and `reviewId`. No forbidden header/body/query/cookie/credential
keys and no raw Playwright trace archive are present. The recorder's credential
canaries also passed before evidence publication.
