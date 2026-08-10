# API Contract Revision Phase B Validation

Date: 2026-08-07

Status: behavior E2E passed in the retained 8/8 run; post-inventory-coherence-fix E2E remains open.

## Delivered Boundary

Corpus now owns a transport-free immutable API contract-revision proposal and
required-review path for the accepted local Medusa evidence chain. The path:

- retains raw `fd172730...`, repaired parent `bc1b4b24...`, repair-manifest
  `dc712d7c...`, final `6fca793b...`, local target hashes, evidence hash, and all
  ten exact patch records;
- shows `BaseRegionCountry.id` impact count 2 before review;
- uses an opaque owner-scoped proposal entity and RouteDeck required review;
- creates a new READY Source revision only after acceptance;
- retains the prior revision and exact historical Agent attachment identity;
- serializes proposal/approval read-check-write with one Source-scoped thread
  and OS file lock; and
- has no HTTP transport dependency and makes no target API call.

Connection checks, operation curation, route planning, read/write execution,
and Phase C behavior were not implemented.

## Automated Evidence

- Full backend: `180 passed, 6 warnings` using
  `.\.venv\Scripts\python.exe -m pytest backend/tests -q`.
- Full frontend: `15 files / 79 tests passed` using
  `pnpm --dir frontend test`.
- Focused RouteDeck/contract: 2/2 backend and 16/16 frontend.
- Recorder/static safety: 10/10.
- Frontend typecheck and production build passed; build retained the existing
  >500 kB chunk warning.
- Generated contract check, Studio parity, and architecture boundary check
  passed.
- Independent scoped review approved the final proposal-detail/review-slot fix
  with no Critical or Important findings.

Risk coverage includes full proposal metadata drift, owner isolation, immutable
historical reads, durable review reload/reject/accept, accept-time current-plan
recheck, six concurrent proposals without loss, exactly one concurrent approval,
missing-Source no-artifact behavior, safe review failure copy, and shell rendering
of simultaneous active plus detail surfaces.

## Browser Evidence

Run `20260807T171438Z-91803b18a0` stopped before Source creation because the
recorder used a global `Add API source` locator. This was recorder-only; zero
product HTTP/console/page/unexpected request failures were recorded. The failed
run retained one safe trace and one continuous video, no screenshot, and no raw
Playwright trace.

Run `20260807T171948Z-08008762fa` reached the real local Docker path:

- Source `woWWmI4l0KFrMZEM`;
- parent revision `HrwNfQ55_eR296DD`;
- durable job `25201fec-6178-4cd7-810b-45c663048a4b`;
- exact raw hash `fd172730...`;
- proposal outcome `proposed` with HTTP 200.

It passed 1/8 journey assertions and captured the READY parent desktop state.
The proposal surface did not appear because Corpus had placed it in RouteDeck's
review slot, whose props are intentionally inactive before a review is staged.
The failed browser artifact does not retain a proposal ID or proposal body;
exact persisted hash/patch/impact provenance is attributed only to the
automated repository/service/review contracts. The product bug was reproduced
RED and corrected by placing the proposal in
`detail`, keeping approval alone in `review`, and rendering `active/detail/review`
through the single shell host. The fix has automated and independent-review
proof but was not browser-rerun in this slice.

The diagnosed slot fix was rebuilt into all three Docker services. Post-fix run
`20260807T173632Z-466c48dc53` then passed 8/8 assertions:

- Source `hzc5F6334IQQUDl3`;
- parent revision `mqwymGd8df_EzKy3`;
- durable job `6ef9aae3-5a43-4ee5-b543-801f990d0d23`;
- proposal `IKvOpJfxawavKE3X`;
- durable review `review_aGY39W1nk167t47ncrM5Unnx`;
- approved child revision `2tq8aAhGahui2wnr`;
- exact repaired parent `bc1b4b2456eefab4684a07ffa6e63f652118f5a705dd13eba5d77e74ab965c6e`;
- exact final `6fca793be700dfb8bf511c2217d72cf97abf2f6cba08fbc2cd26ef0369b8f3f6`;
- all ten patches and `BaseRegionCountry` impact count 2 visible before review;
- required review survived reload;
- rejection retained the parent revision;
- acceptance created a new immutable child and survived reload plus backend restart;
- 390x844 heading, impact, accept and reject controls were all fully in viewport;
- observed RouteDeck operation IDs were exactly `workspace.open_sources`,
  `sources.open_api_creation`, `sources.propose_contract_revision`, and
  `sources.approve_contract_revision`; and
- zero product HTTP, console, page, or unexpected request failures.

The mobile bounds were heading `(39.39,177.94,311.22,48)`, impact
`(57.78,453.33,261.55,21)`, accept `(39.39,663.81,250.27,32)`, and reject
`(39.39,705.81,260.95,32)` within the 390x844 viewport.

The bounded service has no HTTP transport dependency and the browser observed
no execution operation. This is not a connection-check or API-execution claim;
server outbound traffic is not inferred solely from browser diagnostics.

## Retained Artifacts

- `artifacts/api-contract-revision/20260807T171438Z-91803b18a0/result.json`
  SHA-256 `02158a1f16b0eb6364f69d0af13b22c730fc893332831f9f5d16dd18d45b70df`.
- `artifacts/api-contract-revision/20260807T171948Z-08008762fa/result.json`
  SHA-256 `2c51b9be28e6750dfd1281ee2572e57b0847a368b445847160c659beee1a3fa6`.
- READY screenshot `01-ready-parent-desktop.png` SHA-256
  `f1b549d354f72ae1d10c93133d8017be53d938315aaa29dfaf2f8e31c598ca56`.
- Partial continuous video SHA-256
  `64b30858fba1665f692589085d333473bc59c2302d70235418dafc8448653a92`.
- Header/body/credential-free Corpus trace SHA-256
  `c19a8e81ff3e0ae5be240015a4481f0156d39d6cd85e9291e8a9ea8cea28f951`.

Passing run:

- `artifacts/api-contract-revision/20260807T173632Z-466c48dc53/result.json`
  SHA-256 `ed6f6b987a0edec8f589ae2dd45a7b2f1c3e2991a764b3163a444df5f2e0ca95`.
- Six nominal screenshots: READY parent, proposal, reloaded review, 390x844
  review, approved reload, and approved post-restart. Visual inspection found
  the proposal/reloaded-review desktop files show the top of the scrollable
  dock (preparing/loading state), not the exact panels. They remain retained
  with that limitation. The mobile review and approved post-restart desktop
  stills are useful. Exact paths are listed in the result; the mobile screenshot SHA-256 is
  `f4c5d4c617360f341eacbb3c0f4e6b97d84e1ec81a0af0dfb77dfda791529acf`.
- A reviewed 1 fps, 720 px-wide audit of the original video retained three
  explicitly derived, downscaled `from-video` frames. Together they show the
  tall proposal heading/hash cards, its patch tail including shared impact 2
  plus the Review control, and the explicit owner review with final hash,
  impact 2, no-call copy and both decisions. No native-screenshot or
  single-frame-containment claim is made. Exact sample indices, nominal time
  windows, hashes, and limitations are in
  `derived-video-frame-provenance.json`.
- Derived frame SHA-256 values: proposal patch tail/review button
  `20d74ba17505fa4a57bd56858db8273d5c8f60cf49bbfce3950f685851a8cc6c`,
  proposal heading/hashes
  `604f9a39ceb5513646b7cb6975e2980a1638bd06b298b44c90be2751bb88b052`,
  and reloaded review
  `b62950d504261d2b1e4b807c3cb9ee9eac5a3da87a33cd6152b67c3520003d55`.
- Continuous video SHA-256
  `759dc3cd806452326c28e38c8935eeac3a3cf7b36ade34d9a6d71fcb10e92e75`.
- Header/body/credential-free Corpus trace SHA-256
  `0f232675f8043a15b649bbc1d28fec8d87c633f43d008c9159df677cbad86f8f`.

All results explicitly retain their limitations and failures. No raw
Playwright trace, Authorization header, cookie, credential, request body, or
response body was retained.

The recorder is hardened for any future authorized evidence refresh to capture
two truthful proposal viewport frames (heading/hashes/impact, then patch
tail/review button) plus one reloaded-review viewport frame. A single proposal
frame is intentionally not required because the rendered proposal is taller
than 1440x1000. The revised offline capture contract has deterministic and
source-backed coverage but was not browser-rerun.

## Final Visual Attempt And Inventory-Coherence Fix

The independently reviewed first capture hardening was exercised once in run
`20260807T175743Z-215fdca86b`. It stopped after 1/8 assertions:

- Source `sClfjm8AAUhNG-GA`, parent revision `5ZPjbp1vU1UKxnAT`, durable job
  `3ba9da2f-0591-4929-82ab-c43bc1492b2d`, and proposal
  `R7SsABNlLixzOtY7` were created through the real product path;
- the exact proposal heading and impact were in the desktop viewport, but the
  review button began at y=1191.17, so requiring all three in one 1440x1000
  frame was impossible and the recorder stopped before that still;
- the run recorded one real `GET /api/sources` 500 plus its console error. The
  READY screenshot visibly retained the truthful message that the current
  revision file was temporarily missing;
- timestamped logs place the 500 at `17:58:03.653Z`, 78 ms after the Huey worker
  began `mark_running` at `17:58:03.575Z`; adjacent inventory polls were 200.

The inventory race was reproduced deterministically. Corpus now publishes a
new revision before its discoverable Source pointer and uses the existing
Source-scoped thread/OS lock for inventory and exact-revision reads plus
lifecycle, proposal, and approval mutations. Focused tests and independent
review are green with no Critical or Important finding. No further browser run
was authorized, so this coherence fix has automated/review proof only; the
earlier 8/8 run remains the authoritative complete behavior journey.

Final-attempt retained evidence:

- `artifacts/api-contract-revision/20260807T175743Z-215fdca86b/result.json`
  SHA-256 `ace1f1b3509a9a55e1715da7ae1d3f01d143d44b20644258a672987f8c7b2b51`;
- READY/error screenshot SHA-256
  `fe0e7455f6a7564e7e11d243efb2ad482f43b161301c286f323020bbdda04b9d`;
- continuous video SHA-256
  `4456ca2402b6f210ba91919f56e896fce5817aece27cf4156b30cf7986dd33ca`;
- header/body/credential-free Corpus trace SHA-256
  `d85f2ea139fca1d472ce49e19f23a63ac5833ea65e38a89589c77b3e729378d5`.
