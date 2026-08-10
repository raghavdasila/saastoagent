# Step 5 bounded Agent archive/delete validation

Status: implementation and automated contract gates pass; the complete browser
evidence gate remains open. No browser rerun occurred after the authenticated
new-conversation frontend handoff defect was corrected.

## Delivered behavior

- owner-scoped archive preserves the Agent record, immutable versions, and
  Source attachments while removing the Agent from the active inventory;
- dependency-free delete requires durable RouteDeck review, supports rejection
  without mutation, and deletes only the selected exact owner Agent;
- dependency-aware delete uses one owner-scoped inspector for preview, guard,
  accept-time recheck, and mutation-time validation;
- attached Source revisions block delete without cascade or silent detach;
- the database `RESTRICT` foreign key remains the final no-cascade backstop;
- separate archive/delete review surface identities reconstruct exact product
  copy after reload without rendering technical operation IDs;
- stale accepted review failures remain visible and refresh authoritative
  dependency state; empty-to-pending review projections preserve React hook
  order.

RouteDeck owns operation legality, durable review staging/accept/reject,
projection, and transitions. Corpus owns lifecycle persistence, dependency
inspection, product copy, and failure presentation. No RouteDeck source changed.

## Real campaign truth

The single reviewed campaign command was:

`.\.venv\Scripts\python.exe scripts\run_agents_archive_delete_journey.py --url http://127.0.0.1:5199`

Run `20260807T143014Z-4533d14d8c` completed 20 of 22 checks before stopping.
It proved durable archive review across reload, accepted archive, delete review
rejection with no mutation, a fresh accepted dependency-free delete, real
Source Hub processing, visible dependency blocking, a distinct second
conversation, and desktop/mobile lifecycle controls. It did not reach the
accept-time race or mandatory backend-restart assertions because that second
authenticated conversation was incorrectly provisioned at `lounge.home`.

The defect was traced to the Corpus session factory treating every provisioned
conversation as a guest. The factory is now principal-aware: exact persisted
anonymous mappings enter `lounge.home`; exact persisted owner mappings enter
`workspace.home` with node-scoped public surfaces and an exact resume
capability. Missing or mixed principal state fails closed. Focused tests prove
anonymous entry, two isolated owner conversations, correct owner projection,
and owner/anonymous/missing classification. The corrected path has not yet been
re-exercised successfully through the complete browser path.

The next independently reviewed campaign, run
`20260807T152202Z-c966d9f041`, recorded 20 of 21 checks as passing before it
stopped at the distinct-conversation handoff. It again proved archive review
reload and acceptance, delete rejection and fresh acceptance, real Source Hub
processing, dependency blocking, and desktop/mobile controls, with zero
unexpected HTTP, console, page, or request failures. Corpus created the exact
new owner conversation and RouteDeck persisted it at `workspace.home` with its
resume capability, but the frontend tried to encode that session-bound route
before its new store had a projection. Strict capability validation correctly
rejected the unbound handle, so the handoff never committed tab storage.

The frontend now validates the fetched new-conversation projection through a
temporary RouteDeck codec bound to that exact projection before committing the
canonical URL and opaque conversation ID. It reuses the live codec's exact
public-key and resume-capability predicates; mismatched handles still fail.
Focused regression coverage starts on the previous Lounge URL, proves the
authenticated `/home` handoff and subsequent bootstrap, and preserves the
anonymous shareable Lounge path. A failure regression also proves that chat
history must load before the URL or selected/history conversation storage is
committed, so the old mounted conversation remains internally consistent on a
failed handoff. This correction has automated proof only and has not been
browser-rerun.

Retained non-sensitive evidence is under
`artifacts/agents-archive-delete/20260807T143014Z-4533d14d8c/`, including the
result, screenshots, and raw page videos. The raw Playwright trace was removed
after an audit confirmed a non-empty Authorization header. The exact path,
pre-removal SHA-256, byte size, and removal timestamp are recorded without
credential values in
`docs/superpowers/validation/2026-08-07-playwright-trace-security-removal.json`.
The later failed campaign is retained under
`artifacts/agents-archive-delete/20260807T152202Z-c966d9f041/` with its result,
responsive screenshots through dependency blocking, two raw page videos, and
header/body-free `corpus-trace.json`. It did not create a raw Playwright trace
or an assembled continuous video.

## Current automated gates

- backend: 150 passed, with one existing Starlette/httpx deprecation warning;
- frontend: 73 passed sequentially; strict typecheck and production
  build passed with only existing chunk/plugin timing warnings;
- focused conversation handoff/history/bootstrap: 13 passed, including five
  lifecycle tests for exact Workspace handoff, strict mismatch rejection,
  post-commit bootstrap, unchanged anonymous Lounge replacement, and
  no-commit cleanup when chat history fails;
- focused recorder/security diagnostics: 18 passed;
- generated frontend contract: current;
- Studio-to-compiled parity: passed;
- architecture boundaries: passed;
- architecture/documentation validators: 7 passed;
- Docker Compose configuration: valid;
- live Docker migration: `0006_restrict_agent_attachment_delete (head)`.

The authenticated handoff regression was first run red and failed with the
same `capability_mismatch` stack as the campaign. The focused suite then passed
after the projection-bound correction, followed by the sequential full suite.

## Evidence security

The repository-wide evidence audit inspected 100 Playwright archives under
`artifacts` and `.runtime/evaluations`. Ninety-six archives (945,644,637 bytes)
contained a non-empty Authorization header and were removed only after exact
path-boundary and SHA-256 validation. Four archives without credential markers
were retained with matching hashes. The deletion is unrecoverable from the
workspace. Future archive/delete runs disable raw Playwright traces and emit
only chronological `corpus-trace.json` events from an explicit header/body-free
field allowlist.

## Remaining proof gate

One independently reviewed browser campaign must still prove the accept-time
dependency race as visible `review_stale`, preservation of the Agent and its
attachment, mandatory backend restart, zero unexpected HTTP/console/page
failures, responsive screenshots, the assembled continuous video, and the safe
Corpus trace. The retained failed runs are partial evidence only. No automatic
retry is authorized by this validation state.
