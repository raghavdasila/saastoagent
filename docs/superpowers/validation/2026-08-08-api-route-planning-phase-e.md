# Phase E API Route Planning Validation

Date: 2026-08-08 IST  
Status: bounded Phase E behavior validated locally  
Scope: non-executing route preparation and same-lineage clarification only

## Delivered behavior

An authenticated owner can prepare an immutable API route plan from an exact
READY effective revision, saved connection profile, and current operation
curation. The current curation becomes ToolRouter's retrieval corpus before
unchanged routing; excluded endpoint-bound material cannot rank or influence a
plan. Corpus persists exact owner, conversation, RouteDeck session, Source,
revision, artifact, profile, curation, inventory, route evidence, parameter
provenance, expiry, fingerprint, and zero-call identity.

Ambiguity exposes candidates without claiming a selected operation. An exact
typed choice must belong to both the current curation and the current
ambiguity candidates, then reruns unchanged ToolRouter over the one chosen
endpoint while retaining the original subset identity. Missing non-secret
input appends a record in the same lineage under exact current-record CAS.
Managed API-key identity comes only from the exact selected profile and is
recorded without a value, credential reference, or credential version. An
expired or RouteDeck-session-rolled plan can start an explicit new lineage;
the immutable prior lineage remains retained.

`sources.prepare_routed_api_test` is a RouteDeck `STATE_SELECTION`/no-review
Operation allowed from agent or surface. It opens the stable
`sources.api_operation_test` detail surface and makes no external call. The
accepted static Studio SuggestedAction maps truthfully to this empty-input
opener. Read/write dispatch, credential resolution, API execution, write
review, and unknown-outcome recovery remain outside this phase.

## Automated gates

- Focused route-plan service, HTTP, real ToolRouter, SQL RouteDeck, and recorder
  suites passed.
- Full backend: 268 passed with six existing dependency warnings.
- Full frontend: 17 files / 92 tests passed.
- Frontend typecheck and production build passed; build retained the existing
  large-chunk warning.
- Generated frontend contract check, Studio parity, architecture boundary,
  manifest JSON, and documentation ownership gates passed.

## Local runtime and command

Docker Compose ran locally:

- frontend: `http://127.0.0.1:5199`
- backend: `http://127.0.0.1:8099` (`/readyz` returned 200)
- local Medusa: `http://127.0.0.1:9100`
- source worker: Huey consumer with `process_source_revision`
- database revision: `0006_restrict_agent_attachment_delete (head)`

Campaign command:

```powershell
.\.venv\Scripts\python.exe scripts\run_api_route_planning_journey.py --url http://127.0.0.1:5199
```

## Passing real journey

Run `20260808T000249Z-c67d5b0004` passed 13/13:

1. A fresh Source Hub upload reached READY without an inventory coherence
   failure; the owner approved the exact effective `6fca793b...` revision.
2. Curation included exactly `GetProductTagsId` and `GetProductTypesId` and
   excluded the other 62 operations.
3. Agent-origin preparation opened the non-executing planner after the agent
   stream reached a terminal idle state.
4. Real ToolRouter routing exposed Tags/Types ambiguity with no preselection.
5. The typed `GetProductTypesId` choice retained the same lineage and asked
   only for `id`; `x-publishable-api-key` remained profile-managed.
6. Supplying `id` completed that immutable lineage with `api_call_count=0`.
7. A distinct surface-origin conversation produced a ready read route and
   retained explicit current-request provenance.
8. Reload and backend restart preserved the exact ready plan at 390x844.
9. A third conversation retained an unresolved two-step plan atomically with
   zero calls.
10. All seven retained records had `api_call_count=0`; excluded operations did
    not appear in rankings.
11. The three plans remained bound to their exact distinct conversations while
    retaining the same Source, revision, profile, and curation identities.
12. A second owner saw zero Sources and therefore none of the first owner's
    profiles, curations, or plans.
13. The bounded operation set contained only registration/setup, Source
    proposal/approval/configuration/curation, Workspace Sources navigation,
    and `sources.prepare_routed_api_test`; no read/write execution variant was
    dispatched.

Exact identities:

- setup conversation: `ORg1A_xFiH-i_LMztvVtmI7qKS8quyIi`
- Source / parent / approved revision:
  `hTLfKybYAo8noaF0` / `YZd_NkeByTTITxn_` / `_uc10WxT5NtxLWGW`
- job / proposal / review:
  `e074a23f-bb9e-4eb9-b4c5-1f66e8ba90df` /
  `E1cxD_MIBJRRuU32` / `review_AMaUTMfQGp3FWBlnRgORytlP`
- profile / curation: `7kaaG-0D-bFPU5rz` / `fWbuO3JVjIcgGosk`
- ambiguity plan and records:
  `rVJ6n7jwFDw2gAcs` / `YHU3uxHQmEgZQQAy` /
  `FN7j-K6Y2cAd5ZDO` / `xh2pwCxxFBeWnz6v`
- current-request conversation / plan / record:
  `sQ3uBQ_lgZJCXBJNf1XX4s-EZYUnJEQE` /
  `dAl6gIDRX5m_GWe6` / `ggjybPZznrQGmjUX`
- multi-step conversation / plan:
  `_TQOuIBZElhEqqE4xpS7qZVi6Vh4PgUC` / `7KZMSmdHyGs6FCjN`

## Retained evidence and inspection

Artifact root:
`artifacts/api-route-planning/20260808T000249Z-c67d5b0004/`

- `result.json` — passed; SHA-256
  `85a4ac120281daf27e1bedd749964599a86455b55ae6af2d7250fe31398b2325`
- six inspected viewport screenshots: five 1440x1000 desktop frames and one
  strict 390x844 post-restart mobile frame
  - `01-real-ambiguity-no-preselection-desktop.png` — SHA-256
    `5f1ad735addf6cc267b3c1be25e97bffd63907ecaf83ab27e0430fbb8c825780`
  - `02-choice-needs-only-id-desktop.png` — SHA-256
    `4acff7e356223c43b48c2df526f64b8559173233a8a13f160966ea7374424d60`
  - `03-current-request-ready-desktop.png` — SHA-256
    `11ffa371b25240b577a94068fdf761b4cdbc5ced2b2c0a89f79f03f37730b1da`
  - `04-ready-after-restart-mobile-390x844.png` — SHA-256
    `2b2c5f0ab7a8bb9426483818d56c190c01c0afaa0d4a6daca25c8b9a86f60a1d`
  - `05-unresolved-multi-step-desktop.png` — SHA-256
    `2eab261d464603b3f6e421b00082b07088ff69cfb8aa5972bb68aea85dfa79ff`
  - `06-second-owner-empty-inventory-desktop.png` — SHA-256
    `eae9182d9b7988f15d6d0bf924ab7e2249c7d9b80d2160862978a4049265258f`
- `api-route-planning-continuous.webm` — 143.760 seconds, VP8 1440x1000;
  SHA-256
  `c6286dde246aeb12882f8cb73bff520f06f9bb970eb68b10580d3ea76fc99194`
- `corpus-trace.json` — 293 events; SHA-256
  `46cca64cb5151f36763aea80f65b4001633f675932c0eb3e09f66a651d40c47f`

Visual inspection confirmed the ambiguity, typed choice, current-request ready
route, mobile restart, unresolved multi-step, and second-owner empty-inventory
states. Every assertion-named element used by the recorder is within its
claimed viewport.

Diagnostics contain zero unexpected HTTP errors, console errors, page errors,
or request failures. Forty navigation, event, conversation, or private-form
cancellations are retained separately as expected abort diagnostics.

The safe trace key union is limited to `sequence`, `page`, `event`, `method`,
`path`, `status`, `operationId`, `disposition`, `outcome`, `failureCode`,
`reviewId`, `planId`, `recordId`, `planState`, `apiCallCount`, and `parse`.
It contains no headers, query values, cookies, request/response bodies,
credential values, bearer material, or raw Playwright trace. Public plan DTOs
contain none of the forbidden internal router-decision/evidence or credential
reference/version fields. The pre-publication canary scan covers credentials
and per-run user inputs in structured JSON, trace, diagnostics, and raw file
bytes. Accordingly, `result.json`'s `inputValues:false` describes structured
result/trace/diagnostic retention; it is not an OCR claim about pixels.

The rendered screenshots and video intentionally retain synthetic non-secret
development probe values needed to demonstrate current-request provenance:
the per-run `ptyp-phase-e-current-...` value is visible in screenshot 03 and
`cus_123` is visible in screenshot 05. Visual inspection found no credential,
secret header value, password, bearer token, or real user input. These visual
artifacts are not described as input-value-free.

## Failed attempts retained candidly

Earlier runs stopped before completion on recorder selector, missing
conversation-header binding, implicit planner context, agent-stream timing, or
idle-barrier assertions. Each was diagnosed from retained evidence, fixed with
focused deterministic coverage, and independently reviewed before the next
campaign. They are not counted as passing evidence:

- `20260807T232108Z-e84e4967c4`
- `20260807T232808Z-82fd319585`
- `20260807T234223Z-2930db7eea`
- `20260807T235426Z-57cc1eda18`
- `20260807T235846Z-80fae6177f`

## Limits

- This phase prepares routes and clarifications only. It never resolves a
  credential and never executes a read or write API operation.
- Zero target calls are enforced structurally by the route-plan service and
  immutable records. Browser diagnostics cannot independently observe backend
  outbound traffic.
- Expired-plan replacement and stale-CAS behavior are covered by focused
  deterministic tests rather than this bounded browser journey.
- The development OpenAPI input travels through the real Source Hub, Huey,
  ToolRouter, proposal, approval, profile, and curation product path; it is not
  production-data evidence.
- The accepted “Route and test an API operation” behavior remains incomplete
  until the separately mapped read/write execution variants are implemented
  and validated.
