# Deployed Corpus boundary-refactor validation

Date: 2026-08-15

Status: passed in production

## Result

The universal Corpus boundary refactor is committed, pushed, deployed, and
verified at `https://corpus.saastoagent.com`. All five HIGH audit findings are
closed. The production backend/worker and web run immutable digest-qualified
images, the product lifecycle passes independently through Surface, Hybrid,
and ordinary Chat modes, and the repository boundary/checker gates remain
green.

RouteDeck was used through its existing read-only contracts and was not
modified. The user-owned
`docs/corpus-agent-design/feature-behavior-notes.md` was not modified.

## Published implementation

The deployed product lineage is:

- `4529a7e` — universal feature boundaries, app-owned worker composition,
  generic Source truth, isolated Medusa acceptance adapter, checker/skill/docs;
- `947805f`, `4350b6b`, and `98abe57` — current Source and Evaluation truth in
  model-visible context;
- `1e16231` — persisted RouteDeck provider identity contract;
- `783e2f3` — target-feature-owned cross-feature Agent binding contracts;
- `b396cad` — unique most-specific deployed operation choice.

Production manifest and running-container identities agree:

| Runtime | Digest |
| --- | --- |
| Backend and worker | `sha256:6b9c677b54bea60ea85ce9816a0e176d6e97b1f5185aea9b62fa0b2f59fd18ee` |
| Web | `sha256:1a9acb0a572b7708e87bd9b7d0407af9ae1cb38154d5f717f38a4e6aa41a6b41` |

The rollback manifest for the immediately preceding production image is at
`/srv/corpus/deploy/rollback/20260815-b396cad/image-manifest.env`.

## Accepted deployed E2E

All three journeys ran against production Corpus and private Medusa
`http://10.138.0.2:9100`. They used Medusa Source SHA-256
`fd17273078c222a5632459f67204cbc9cf03cb925641d47669209baa9cc97fb6`,
created independent owner/conversation/Source/Agent/build lineages, and
recorded zero unexpected HTTP, console, page, or request failures.

| Mode | Result | Run ID | Continuous raw recording |
| --- | --- | --- | --- |
| Surface | 39/39 | `20260815T113953Z-89bb70e514` | `artifacts/horizontal-product-surface/20260815T113953Z-89bb70e514/raw-video/page@e87bdc395367bf8186da89f3f23c5420.webm`; 561.68 s; 39,784,849 bytes; SHA-256 `e09d297f5084d398f8b8437085fd47e1a47d707c2ad8ffbad93fa02416f127be` |
| Hybrid | 40/40 | `20260815T102407Z-828e3735c3` | `artifacts/horizontal-product-hybrid/20260815T102407Z-828e3735c3/raw-video/page@cd84f0eba388c81ba5774bdbf7040a12.webm`; 820.44 s; 68,436,010 bytes; SHA-256 `7527c6d734d316439fb0a426b6ca5942233b5352aeb3a0e4b64be4ef6fc9b3eb` |
| Chat | 39/39 | `20260815T115153Z-5847710253` | `artifacts/horizontal-product-chat/20260815T115153Z-5847710253/raw-video/page@83a5459d29e3d2570ca84aa49ec3c49a.webm`; 1,002.12 s; 84,579,761 bytes; SHA-256 `7ad5c433b63a999b03b229bab9623f80be283d0ee7008a05b573446be8ce299e` |

These videos are the same evidence class as the earlier accepted recordings:
uncut, normal-speed Playwright page videos with synchronized result JSON,
screenshots, retained IDs, safe trace, and diagnostics. They are new
independent journeys, not copies of the earlier films.

## Checker corrections found during deployed verification

The strict assertions were not reduced and failed campaigns were not relabeled.
Deployed verification identified checker-language and DOM assumptions:

- generated Evaluation copy now requests the generated draft case rather than
  incorrectly calling it the required case;
- Builder runtime copy names the already assembled exact build and forbids
  creating another build;
- public assistant-response parsing excludes the visual `Assistant` header
  before classifying an operation-choice question;
- the initial attached-file request explicitly requires adding the API and
  starting analysis in the same turn, while still containing no Corpus or
  RouteDeck operation IDs.

Focused checker tests passed 3/3 after the final prompt/DOM corrections. The
complete backend suite later passed 536/536 and the root suite passed 100/100.

Retained non-accepted runs include Hybrid
`20260815T091109Z-d8276df5e0` (the ambiguity that led to the product-level
most-specific-operation correction), Surface
`20260815T112146Z-da382ef8c9` (the DOM-header checker defect), Chat
`20260815T114932Z-88d37c3572` (underspecified same-turn file request), plus
earlier DNS, provider-identity, binding, builder-prompt, and exact-slug
failures. Their artifacts and recordings remain local historical evidence and
are not acceptance proof.

## Fresh repository gates

All commands ran from `D:\Dev\AI Projects\saastoagent-v0.1`:

| Gate | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest backend\tests -q` | 536 passed, 6 dependency deprecation warnings, in 102.65 s |
| `.\.venv\Scripts\python.exe -m pytest tests -q` | 100 passed in 6.08 s |
| `.\.venv\Scripts\python.exe scripts\check_architecture_boundaries.py` | Passed with zero real-repository violations |
| `.\.venv\Scripts\python.exe scripts\check_doc_coverage.py` | Exit zero; both changed checker files mapped to documented owners |
| `skill-creator/scripts/quick_validate.py skills/audit-corpus-boundaries` | `Skill is valid!` |
| `git diff --check` | Passed; only Git's Windows line-ending advisory was emitted |

The deployed product sources had already passed frontend 188/188, strict
TypeScript typecheck, production build, production image package/import checks,
and `pip check` before publication. The final closeout delta changes only the
E2E checker, its tests, and documentation; it does not change the runtime
image.

## Live operational proof

- `corpus.service` is active.
- `corpus-backup.timer` is active; the next nightly backup is scheduled.
- backend, worker, and web are running with zero restarts and
  `OOMKilled=false`; backend health is `healthy`.
- `corpus.app.worker` registers exactly five tasks: Source processing, build
  assembly, evaluation-set generation, evaluation-case execution, and build
  publication.
- public `/healthz` returned `200 {"status":"ok"}`.
- public `/readyz` returned `200 {"status":"ready"}`.
- recent logs contain successful E2E traffic. Canceled SSE proxy responses
  coincide with expected page navigation/teardown.

Readiness deliberately performs a real configured OpenAI dependency check with
a five-second timeout. A provider stall can therefore make `/readyz` fail; the
system does not mask that failure with an alternate provider or canned result.

## Current claim boundary

This proves the deployed Medusa ecommerce vertical and the HIGH architecture
remediation at the code, checker, runtime, and three-mode product-path levels.
It does not prove every external API, exhaustive Behavior Note breadth,
hostile-code/process isolation between built Agents, multi-host scaling, or a
production SLA. The four MEDIUM audit findings remain explicit follow-up work.
