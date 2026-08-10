# Phase D API Operation Curation Validation

Date: 2026-08-08 IST  
Status: bounded Phase D behavior validated locally  
Scope: operation curation only; no route plan, credential resolution, or API execution

## Delivered behavior

An authenticated owner can select an exact READY API Source revision and see
the API-operation inventory derived from that revision's existing ToolRouter
semantic graph. Every operation must be explicitly included or excluded.
Filtering is non-mutating. A save dispatches
`sources.save_api_operation_curation` as a RouteDeck `DRAFT`/no-review
Operation from agent or surface, appends an immutable record, and advances its
pointer only after exact expected-current CAS under the Source lock.

Unknown, duplicate, overlapping, incomplete, foreign, changed-inventory,
stale-current, concurrent, corrupt-history, or persistence input fails without
replacing the prior current selection. The UI rejects old Source/revision
responses, serializes refresh/save, shows stale failure, and refetches the
authoritative decision set.

The accepted Studio static SuggestedAction remains design-only: empty static
arguments cannot truthfully identify the runtime Source, revision, inventory,
expected current record, and exhaustive decisions. The compiled runtime
operation and `sources.home` affordance are the completed contract.

## Automated gates

- Focused backend service/HTTP/RouteDeck contract: 11 passed.
- Backend Sources plus Workspace: 60 passed.
- Full backend: 228 passed with six existing dependency deprecation warnings.
- Focused frontend curation: 10 passed.
- Full frontend: 16 files / 84 tests passed.
- Recorder helper/diagnostic/geometry suite: 9 passed.
- Frontend typecheck and production build passed; build retained the existing
  large-chunk warning.
- Generated frontend contract check, Studio parity, architecture boundary,
  manifest JSON, configuration, and documentation ownership gates passed.

## Local runtime and command

Docker Compose ran locally:

- frontend: `http://127.0.0.1:5199`
- backend: `http://127.0.0.1:8099` (`/readyz` returned 200)
- source worker: Huey consumer with `process_source_revision`
- database revision: `0006_restrict_agent_attachment_delete (head)`

Campaign command:

```powershell
.\.venv\Scripts\python.exe scripts\run_api_operation_curation_journey.py --url http://127.0.0.1:5199 --backend-url http://127.0.0.1:8099
```

A preceding Compose command used the nonexistent service name `worker` and
failed before rebuilding or starting any browser. The corrected service was
`source-worker`; this command typo is not an evidence campaign.

## Passing real journey

Run `20260807T212855Z-f8596ef591` passed 9/9:

1. Fresh Source Hub upload reached READY through the real Huey worker and
   ToolRouter path with zero inventory 500s.
2. Exact operations were `createOrder`, `listOrders`, and `trackShipment`;
   filtering left all three decisions unclassified and unchanged.
3. First exhaustive save appended immutable curation
   `Pr1WCMSTzi3GnpvN`.
4. A distinct authenticated conversation advanced the exact CAS to
   `tXA_fE0aKcozfdty`.
5. The stale first conversation received
   `api_operation_curation_selection_stale`, then visibly refetched the two
   persisted records and authoritative include/exclude radios.
6. Reload preserved both immutable records and the current selection.
7. Two strict 390x844 viewport captures proved revision/history identity and
   persisted action controls.
8. Backend restart preserved the exact history/current pointer.
9. A second owner saw zero Sources, while the bounded campaign dispatched only
   `workspace.open_sources`, `sources.open_api_creation`, and
   `sources.save_api_operation_curation`; external API call count was zero.

Exact identities:

- Source: `s_8I_YJ_fWo7oIPf`
- revision/artifact: `qu_YaxESgQofe2wp`
- durable job: `ce2e806d-c535-476b-93bd-27c7efa4912d`
- inventory fingerprint:
  `6002cc6e8ed3823285b037b9ffc669425d22d98899d4ce06c8ef85631669a963`
- primary conversation: `A27jjS0X5wpAG7U5d6ZeDoXISK4Dl175`
- concurrent conversation: `3jufmpTDMGkWIpGOnMDqRxGtM9hmE8va`

## Retained evidence and inspection

Artifact root:
`artifacts/api-operation-curation/20260807T212855Z-f8596ef591/`

- `result.json` — status passed; SHA-256
  `e5f6afa3eab10c7466dc7301cb9cade5fdfb0415a04c780770041d40594a56bb`
- eight inspected PNGs: desktop identity/controls split, stale failure and
  authoritative decisions, mobile identity/controls split, post-restart
  Source, and empty second-owner inventory
- `api-operation-curation-continuous.webm` — 62.16 seconds; SHA-256
  `b1e7515d3cff045027de03d896386d8c1e5e72cbb077e63a5f16648e8dd88ab2`
- `api-operation-curation-primary.webm` and
  `concurrent-conversation.webm` retain the two raw page clips
- `video-assembly.json` retains exact offsets and ffmpeg command
- `corpus-trace.json` — 171 events; SHA-256
  `55eb040f12fdc1d380ea44c7332e25a8c8528cca9fc8fce3a159fb0dd59c854e`

Visual inspection confirmed every named control is inside its claimed desktop
or 390x844 viewport. A 4-second-sampled contact sheet of the original video was
inspected from `.runtime/audits/20260808-phase-d-video-audit/`; it is an audit
aid, not primary product evidence.

Diagnostics contain zero unexpected HTTP errors, console errors, page errors,
request failures, or operation IDs. The one retained business failure is the
exact expected `sources.save_api_operation_curation` 409 stale-CAS result.
Navigation/poll/private-form cancellations and the exact successful sign-out
cancellation remain separately retained as expected abort diagnostics.

The safe trace contains only `sequence`, `event`, `page`, `method`, `path`,
`status`, `operationId`, `disposition`, `outcome`, and `failureCode`. It contains
no headers, query values, cookies, request/response bodies, credential values,
or bearer material. No raw Playwright trace archive exists.

## Failed attempts retained candidly

- `20260807T212045Z-07470388c7` stopped at 2/9 because one recorder assertion
  required an impossible single desktop frame for a tall panel. Product READY
  inventory/filtering passed with zero product diagnostics.
- `20260807T212331Z-f6d772a4cd` stopped at 4/9 because the recorder opened its
  concurrent page at `/`, which navigated the shared Source session away from
  the primary surface. Both curation saves had succeeded. The corrected helper
  enters through the exact current same-origin canonical URL and retains normal
  RouteDeck resume validation.

Both diagnoses were reproduced, fixed offline with deterministic tests, and
independently reviewed before the single passing post-fix campaign.

## Limits

- The uploaded OpenAPI document is explicitly labeled a development probe. It
  uses the real product upload, durable job, Huey worker and ToolRouter path; it
  is not production-data evidence.
- The browser stale case proves exact current-curation CAS across two real
  conversations. Changed-inventory fingerprint failure is covered by the real
  SQL RouteDeck guard test rather than this browser run.
- The recorder's zero-execution assertion is structurally backed by the
  curation service having no credential, transport, route-plan, or API-execution
  dependency. Browser observation alone cannot inspect backend outbound traffic.
- Route planning, clarification, credential resolution, read/write execution,
  write review/unknown-outcome recovery, and ordered graph replay remain open.
