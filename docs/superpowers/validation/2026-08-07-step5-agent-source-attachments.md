# Step 5 bounded Agent Source attachment validation

Status: passed for the bounded attach-existing, create-and-attach, and
open-attached Source runtime, including identity-only persistence, fresh mobile
control evidence, reload persistence, and mandatory backend-restart recovery.
Later Step 5 behaviors remain out of scope.

## Runtime and evidence

- Frontend: `http://127.0.0.1:5199`
- Backend: `http://127.0.0.1:8099`
- Docker services: backend and frontend healthy; source-worker running.
- Migration history: `0003_shared_infrastructure -> 0004_agent_source_attachments -> 0005_remove_agent_attachment_display_name`.
- Live migration check: `docker compose exec -T -w /workspace/corpus/backend backend python -m alembic -c alembic.ini current` reported `0005_remove_agent_attachment_display_name (head)`.
- Run: `20260807T115259Z-ca04df5b57`
- Result: `artifacts/agents-lifecycle/20260807T115259Z-ca04df5b57/result.json`
- Agent: `37b8aa57-358d-45b7-95e8-2b8b205d3bb7`
- Source: `l4qdDbOCh5XvJ5QB`
- Revision: `2ycdNoJNNGdbNGby`
- Job: `17e24b67-4719-4f84-9f1c-ff788bcf546b` (`SUCCEEDED`, attempt 1 of 3).
- Screenshots: six captures in the run directory, including
  `05-mobile-agent-attachments.png` and `06-restart-persistence.png`.
- Video: `artifacts/agents-lifecycle/20260807T115259Z-ca04df5b57/videos/page@359ec8b18dd9a25ace784c8dc56393c3.webm`
- Trace security: the original raw Playwright archive was removed after an
  audit confirmed it retained an Authorization header. Screenshots, result,
  and video remain. The exact pre-removal path and SHA-256 are recorded in
  `docs/superpowers/validation/2026-08-07-playwright-trace-security-removal.json`.

The latest continuous journey registered a real owner, created and selected an Agent,
uploaded an OpenAPI Source through Source Hub, waited for the real Huey worker
and ToolRouter revision to become READY, attached the exact revision, returned
to the Agent, opened the attachment in Source Hub, and proved browser reload
plus backend-restart persistence. It recorded zero HTTP, console, or page
errors. Eighteen expected aborted event/conversation/private-form requests
during navigation and restart remain in the diagnostic record.

The original full-page `03-agent-attached-revision.png` does not bring the
nested attachment section into the visible viewport. The curated seventh
still is frame 30 extracted from the same authenticated continuous video; it
visibly shows `Attached Sources`, the immutable revision, and `Open Source`.
It is derived desktop evidence, not a fresh browser run. A later refresh attempt
(`20260807T094949Z-252a1d02fc`) stopped before the lifecycle at the real
registration IP rate limit and is retained as a failed precondition artifact,
not product failure or passing evidence. At the review checkpoint only about
45 minutes had elapsed, so the one-hour throttle window had not safely reset
and no early or blind registration retry was made.

The original recorder generated both email and password independently with
`uuid4()` and did not retain credentials in its result metadata, so the passing
account could not be logged into deterministically. An existing authenticated
Edge owner was inspected through the normal product UI, but it had no attached
Source. The extension-owned file chooser could not assign the development
OpenAPI probe because local file access was disabled. The browser bridge's
page evaluation contract is read-only, so injecting a synthetic in-memory
`File` would violate that tool boundary. The recorder now requires
`Attached Sources`, the exact
pinned revision, `Attach Source`, and `Open Source` to each have a complete
bounding box inside the 390x844 viewport before it records the mobile capture.

After the one-hour threshold, exactly one normal recorder attempt ran at
`2026-08-07T10:51:09Z`. Registration succeeded and the real path created Agent
`45286226-8865-4b3c-af26-c16f46531ac6`, Source `shPN2PHJMIcVBbJB`, and revision
`vOmQ2iXVFAwKaAaC`. Four assertions passed: attach-and-return, open Source,
immutable identity exposure, and reload persistence. Desktop screenshot
`03-agent-attached-revision.png` visibly includes the attached Source, exact
pinned revision, Attach Source, and Open Source controls. The worker completed job
`f3956fbc-d0b5-42a4-af68-427f067840d3` in 3.316 seconds, and no HTTP, console,
or page errors were recorded.

That single attempt then restarted the backend successfully, but the recorder
timed out waiting for the `Agents` heading while restoring navigation after
the restart. Backend logs show successful authentication refresh plus 200
responses for the Agent and its attachments; a read-only live database check
after restart retained the same agent/source/revision identity row. This is a
recorder navigation/recovery failure, not passing mobile evidence, and the
attempt was not rerun. Retained failure evidence:

- Result: `artifacts/agents-lifecycle/20260807T105109Z-179a2da66d/result.json`.
- Screenshots: `01-agent-empty-attachments.png` through
  `04-open-attached-source.png` in that run directory.
- Raw continuous failure-run video:
  `artifacts/agents-lifecycle/20260807T105109Z-179a2da66d/videos/page@3a257112c81b0b7c5164f4809bb65a07.webm`.

The mobile step was never reached in that failed attempt, so it did not close
the requested mobile visual review gate.

Post-run diagnosis used the retained result, backend logs and the final video
frame. The page was still rendering `Preparing Corpus` while the backend had
already returned successful refresh, session and event responses. The old
`restore_agents()` sampled Sign in / Continue to Workspace / Open Agents once
during that loading shell, found nothing, then waited only 30 seconds for an
Agents heading. It could not act on controls appearing after bootstrap. The
recorder now polls for up to 90 seconds, clicks only currently visible recovery
controls, and completes only when the Agents heading is visible. A focused
deterministic delayed-bootstrap regression test passes. At that checkpoint no
browser journey had been rerun, so the evidence gap remained.

The recorder evidence order is also corrected for the next authorized run.
Immediately after attach/open/reload persistence it now switches to 390x844,
scrolls the attachment region into view, captures
`05-mobile-agent-attachments.png`, and records the four in-viewport bounds.
It then restores the 1440x1000 viewport, restarts the backend, reloads, uses the
condition-based recovery above, and records `06-restart-persistence.png` plus
the restart assertion. A focused orchestration test proves the declared order
is mobile then restart and that neither phase was removed. This changes only
recorder evidence ordering; it does not replace real mobile or restart proof.

The subsequent single authorized journey `20260807T115259Z-ca04df5b57`
closed those evidence gaps with 6/6 assertions. Its 390x844 screenshot visibly
contains `Attached Sources`, revision `2ycdNoJNNGdbNGby`, `Attach Source`, and
`Open Source`. The exact in-viewport bounds were:

- heading: x 37, y 447.46875, width 316, height 24;
- revision: x 48, y 562.46875, width 294, height 19.1875;
- Attach Source: x 37, y 714.65625, width 316, height 32;
- Open Source: x 48, y 591.65625, width 294, height 32.

After that capture the same journey restored the desktop viewport, restarted
the backend, refreshed the authenticated owner session, reopened the exact
Agent, and found the same pinned revision. The restart assertion passed and
`06-restart-persistence.png` was saved. Uvicorn cancelled one open long-poll
request when its configured five-second graceful-shutdown timeout elapsed;
the backend restarted healthy and the product journey recorded no HTTP,
console, or page failures.

Focused backend tests protect same-owner scope, READY/current validation,
duplicate/newer-revision conflict, immutable stored revision, foreign-owner
rejection, dynamic Source display enrichment and truthful unavailable-source
failure. Migration tests assert the exact current columns, named uniqueness,
two cascade foreign keys, owner/agent/time index, forward removal of the stale
display column, and identity preservation from an applied `0004` database.
Frontend tests protect exact canonical `agent_ref` plus `source_id` dispatch
for attach-existing and attach-created.

## Current contract gates

- Backend: 122 passed.
- Frontend: 62 passed; strict typecheck and production build passed.
- Design Studio: 49 passed; strict typecheck and production build passed.
- Focused Agents plus evaluation binding/runtime registry: 9 passed.
- Studio-to-compiled parity: passed with the exact current evaluator IDs and
  no aggregate or fake lifecycle placeholder.
- Architecture boundary: passed after the Source handoff constant and client
  types were exposed only through the backend/frontend Sources contract seam.
- Generated frontend contract and Docker Compose configuration: current and
  valid.
- Final focused review checks: 16 passed for Agents, migration, persistence,
  runtime/config and integration risk coverage; 3 passed for recorder viewport
  containment, delayed-bootstrap navigation recovery, and mobile-before-restart
  evidence ordering with restart retained.
- Live `0005` schema: only `id`, `organization_id`, `agent_id`, `source_id`,
  `source_revision_id`, and `attached_at`; named attachment uniqueness,
  owner/agent/time index, and both cascade foreign keys remained intact.

The exact lifecycle evaluation definitions use the registered
`agents.one_agent` setup adapter. Attach-existing, create-and-attach and
open-attached definitions point to this recorder as their external evidence
owner. Later accepted definitions retain their exact IDs but do not claim
runtime completion.

Chat/mixed continuation, archive/delete, selected-agent operations hub, and
build lineage are not implemented or claimed by this bounded slice.
