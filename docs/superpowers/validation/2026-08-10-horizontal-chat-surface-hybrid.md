# Horizontal chat, surface, and hybrid validation

## Runtime

All accepted runs used the local stack:

- frontend `http://127.0.0.1:5199`;
- backend `http://127.0.0.1:8099`;
- Medusa `http://127.0.0.1:9100`;
- Alembic `0012_builder_navgraph (head)`;
- real one-thread Huey Source worker;
- configured OpenAI chat provider for chat/hybrid model turns.

The command was:

```powershell
.\.venv\Scripts\python.exe scripts\run_horizontal_product_journey.py `
  --url http://127.0.0.1:5199 `
  --backend-url http://127.0.0.1:8099 `
  --mode <surface|chat|hybrid>
```

## Retained runs

| Mode | Run | Assertions | Screenshots | Raw uncut 1x video | Safe trace | Unexpected diagnostics |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Surface | `20260809T153004Z-7cd51d776b` | 24/24 | 18 | 288.24 s | 609 | 0 HTTP/console/page/request |
| Chat | `20260809T165131Z-63d1c6220b` | 24/24 | 18 | 581.04 s | 1132 | 0 HTTP/console/page; 10 historical chat-abort recorder entries described below |
| Hybrid | `20260809T210136Z-853c33486c` | 25/25 | 18 | 474.28 s | 968 | 0 HTTP/console/page/request |

Hybrid result SHA-256:
`f75b9a53510f53d1c3e9616d71ef183b29f867993cb5c367048e477dc897eecf`.

Hybrid video SHA-256:
`68f3e0b5c7a64439b1d344fc4aabccf8ce176a7a26a7753f158b2120b3c5251b`.

## Behavior truth

The three modes independently exercise the same real persisted product. The
chat path uses ordinary owner requests and lets the configured model select
legal provider-safe operations. It does not send product node, feature,
operation, route, or hidden entity IDs. Surface mode invokes visible controls.
Hybrid mode alternates chat and surface actions in one durable Corpus
conversation; repeated read operations are permitted only for distinct owner
requests, while duplicate operation dispatch for the same request fails the
recorder.

The hybrid run proves the previously missing chronology seam: a ToolRouter
clarification is answered through the Sandbox surface, RouteDeck retains the
typed public succeeded result, navigation preserves it, and later ordinary chat
creates and runs the Evaluation case instead of repeating the clarification or
trusting older waiting history.

## Visual and architecture evidence

The 18 hybrid screenshots and continuous video visibly retain:

- Source semantic node-edge graph and owner NavGraph;
- Designer feature/capability/tool/policy blueprint, topology, and NavGraph;
- immutable compiled Builder NavGraph;
- Sandbox waiting and resolved ToolRouter clarification evidence;
- Evaluation exact Sandbox/build lineage and evaluated NavGraph;
- reviewed hosted deployment, active deployed NavGraph, and restart survival;
- public hosted clarification followed by one resolved read;
- owner-only Operations RouteDeck/NavGraph/ToolRouter evidence;
- 390x844 Operations rendering.

Public hosted pages do not expose owner-only runtime diagnostics.

## Diagnostics and redaction

The hybrid result contains 968 trace events with only these keys:
`disposition,event,eventCursor,evidenceId,failureCode,method,operationId,outcome,page,parse,path,projectionVersion,reviewId,sequence,sessionVersion,source,status`.
It contains no Authorization header, bearer token, cookie value, request body,
or response body. There is no raw Playwright trace archive.

The immutable chat-only run predates exact completed-request correlation and
retains ten `POST /api/routedeck/chat` `ERR_ABORTED` entries. Each corresponding
turn has exact durable operation evidence and the run passed 24/24. The later
recorder fix classifies such an abort only when the same Playwright Request
object first received exact status 200; unrelated aborts remain unexpected.
Focused tests and the zero-request-failure hybrid run validate that correction.

## Remaining scope

This closes the horizontal launch baseline, not every behavior note. Builder
runtime controls, ToolRouter-generated Evaluation CRUD, channel rollback and
availability changes, Operations promotion, and other bindings still marked
`pending_external_evidence` remain explicit depth work.

## Agent Designer isolated checkpoint

The retained surface run `20260811T090952Z-f0338236c1` independently passes the
Agent Designer milestone: exact Agent/Source/curation lineage, immutable
proposal/customization/review/accept/build request, the visible design system,
real RouteDeck NavGraph selection, maximized split layout, and 390x844 render.

It can be checked without launching a browser or replaying Source setup:

```powershell
.\.venv\Scripts\python.exe scripts\run_horizontal_product_journey.py `
  --verify-milestone designer `
  --artifact artifacts\horizontal-product-surface\20260811T090952Z-f0338236c1\result.json
```

The readable Designer-only maximized excerpt is
`artifacts/agent-designer-milestone/20260811T090952Z-f0338236c1-maximized/agent-designer-maximized.webm`
(18.2 s, normal speed, SHA-256
`5a3c35d09f9d9ee2eb8f39e90cd583d8cbe5251cd666551802d8c3b774dd4546`).
It is truthfully derived from the accepted 180.44 s raw video; it is not a new
campaign and does not claim the still-pending chat-only or hybrid milestone.
