# Horizontal ecommerce acceptance: chat, surface, and hybrid

Date: 2026-08-13

## Claim

Three independent local Corpus journeys accept the same Medusa ecommerce Agent
from fresh Source intake through owner-only Operations evidence:

1. direct surfaces;
2. ordinary owner-language chat, with credentials kept surface-only; and
3. a hybrid conversation that deliberately alternates chat and surfaces.

This is local development acceptance, not production deployment or an SLA. The
runs exercise the real Corpus product path, local Medusa 2.13.6, the configured
model provider, durable Corpus persistence, RouteDeck supervision, the Source
worker, and browser-rendered desktop/mobile UI. They do not use product mocks,
canned responses, fallback models, direct database mutation, or test-only
runtime branches.

## Runtime command

```powershell
.\.venv\Scripts\python.exe scripts\run_horizontal_product_journey.py `
  --url http://127.0.0.1:5199 `
  --backend-url http://127.0.0.1:8099 `
  --mode <surface|chat|hybrid>
```

Runtime endpoints were Corpus `http://127.0.0.1:5199`, backend
`http://127.0.0.1:8099`, and local Medusa `http://127.0.0.1:9100`.

## Accepted runs

| Mode | Run | Assertions | Screenshots | Raw 1x video | Safe trace | Unexpected diagnostics |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Surface | `20260812T183856Z-02c48c5a50` | 39/39 | 28 | 478.44 s | 734 | 0 |
| Hybrid | `20260812T221223Z-0e9ec6eb55` | 40/40 | 27 | 790.64 s | 1,863 | 0 |
| Chat | `20260812T222652Z-403a886798` | 39/39 | 27 | 921.60 s | 2,214 | 0 |

Unexpected diagnostics means each run retained empty `httpErrors`,
`consoleErrors`, `pageErrors`, and `requestFailures` lists. The surface run
retained 51 expected navigation/poll aborts; hybrid retained 112; chat retained
140. Each run separately classified four WebGL readback performance warnings
from semantic-graph capture as expected. These allowlists do not suppress an
operation, review, API, or product failure.

## Immutable artifact identity

### Surface

- Result:
  `artifacts/horizontal-product-surface/20260812T183856Z-02c48c5a50/result.json`
- Result SHA-256:
  `c863a1ec59231c93a97a7c01da566e3605a29f24d1c36a4eb3e3a56568198837`
- Video:
  `artifacts/horizontal-product-surface/20260812T183856Z-02c48c5a50/raw-video/page@ed4413d661b2685664c02640613aa798.webm`
- Video SHA-256:
  `73f74460f7e4e6f3473580805574f7f084073ff28e89a6865d0b823b307f50be`
- Video bytes: `35,021,345`
- Conversation `arZEzin2MQQ9MRcDnC1sgSUBw5unVU6P`; Source
  `006H-StsVllmMVNe`; approved revision `XqBzWfxXRMd088c4`; profile
  `HfoihRes1f9P8OgB`; curation `nOd2ROZ5mLmpp2MW`; Agent
  `4a4ab407-79e6-4869-a723-4fd5982033e2`; build
  `12fd482b-9c87-4217-a1b6-e28103ecbafe`; Sandbox run
  `a49a596e-e5d1-451d-a657-5e427d4d106a`.
- Post-run Medusa audit: cart `cart_01KZVMPSBEES62PRC3RRRS2M2Q`, one
  `Medusa T-Shirt`, quantity 1.

### Hybrid

- Result:
  `artifacts/horizontal-product-hybrid/20260812T221223Z-0e9ec6eb55/result.json`
- Result SHA-256:
  `6863f8fbca65bf1ec96c73c819629a3a59cb4bfb35286e40adc9c9e27f7d2848`
- Video:
  `artifacts/horizontal-product-hybrid/20260812T221223Z-0e9ec6eb55/raw-video/page@97389ef66e272628897a068a2be58e4f.webm`
- Video SHA-256:
  `ac829b7080f1f93bc588e318acc012b9011b3dc71f928fc13dd7cd78f2cbd9e3`
- Video bytes: `69,092,689`
- Conversation `a4TFHARpBocG8Avc6u95KO8HzKyGOFY0`; Source
  `4-G4PM5zhemSB3m2`; approved revision `y4mgwBHPaVEY98IE`; profile
  `3m3KxmlzPOeUUR_W`; curation `fXyipIkzM0UfQEVi`; Agent
  `b3e205e9-bf0a-4835-bc1e-b10f2bba6b36`; build
  `f8f63e7e-2d80-49ec-957c-3ba98607f72b`; Sandbox run
  `082ef5bf-46d3-47da-9bd0-7d7b0b286128`.
- Post-run Medusa audit: cart `cart_01KZW16R4F7GPNG0E5Q77YK1KP`, one
  `Medusa T-Shirt`, quantity 1.
- The result retains 26 chat-operation events plus direct surface actions in
  the same conversation.

### Chat

- Result:
  `artifacts/horizontal-product-chat/20260812T222652Z-403a886798/result.json`
- Result SHA-256:
  `6adc5d3037b7922eabf9b5d5089c5695594e92c204b9f75003ebe8f7db5f7ce3`
- Video:
  `artifacts/horizontal-product-chat/20260812T222652Z-403a886798/raw-video/page@6cc69de6b14bb2772eb72df0a414c06c.webm`
- Video SHA-256:
  `c28dae47b16abeb9328d3ddb71133d699d362972be01a5b2ba68cbc16ce9072e`
- Video bytes: `79,736,347`
- Conversation `siQhJHAzn-iLNEk0ghiji6AOtxrrEr0w`; Source
  `xv71B-dsq1kAEHyQ`; approved revision `_EmBHrkFWjDBTbf3`; profile
  `qGi4Qvhq0-dQJmI0`; curation `_FS2wiPGdvCLAwAZ`; Agent
  `7d9f4b12-cd80-408d-85d2-877a146d9efd`; build
  `de6d235e-b654-4408-a22d-0dfaf5938d43`; Sandbox run
  `d6602509-636a-47b5-b5ce-7db508378cdf`.
- Post-run Medusa audit: cart `cart_01KZW251N87CWHBM5959PS16G7`, one
  `Medusa T-Shirt`, quantity 1.
- The result retains 44 operation events across ordinary owner messages.

## Behavior accepted in every mode

- The owner supplies an API definition as a file. Saving the attachment does
  not start processing; a separate explicit action queues analysis.
- Source processing persists the complete semantic node-edge graph and its
  construction evidence. Source Hub shows that graph and supports maximized
  split mode with chat retained to the left.
- The owner reviews a new immutable effective API revision. Connection
  credentials remain in the protected surface path and are never placed in
  chat, public RouteDeck arguments, retained result bodies, or the safe trace.
- Operation curation retains exactly `GetProducts`, `PostCarts`, and
  `PostCartsIdLineItems` for the shopping Agent.
- The Agent pins the exact approved Source revision. Designer produces one
  grounded immutable feature revision, renders the proposed design system and
  NavGraph, separates approval from build request, and renders at 390x844.
- Builder queues durable assembly, the worker materializes the exact accepted
  design and Source bindings, the immutable compiled RouteDeck NavGraph is
  visible, and initial ToolRouter evaluation coverage is scheduled for that
  exact build.
- Sandbox routes `Medusa T-Shirt` through ToolRouter, performs one validated
  `GetProducts` call, returns the real Medusa product, and exposes the isolated
  owner runtime plumbing.
- Evaluation retains generated exact-build truth, runs the required case,
  derives deployment eligibility, and shows the NavGraph that it evaluated.
- Deployment is review-gated. The Agent receives two immutable releases,
  rollback selects the earlier release, pause removes public access, resume
  restores the same address, and backend/worker restart restores the exact
  active binding.
- The hosted Agent completes a real product search. `PostCarts` is staged with
  zero external calls before approval and completes once after approval.
  `PostCartsIdLineItems` is separately staged and adds exactly one selected
  product in the same public session after approval.
- The public session never receives owner-only RouteDeck, ToolRouter, Source,
  or credential diagnostics. Operations shows the redacted owner-only deployed
  interaction evidence and promotes the exact successful interaction into
  Evaluation once.
- The joined lifecycle renders at 390x844.

## Effective API correction boundary

The accepted effective API definition is a new immutable reviewed revision;
the earlier `6fca793b...` revision was not overwritten. Two local-response
identity corrections were added after observing the real local Medusa 2.13.6
responses:

- `GetProducts` requires the response envelope, product ID/title, and variant
  ID used by later same-session cart work. Evidence:
  `2026-08-12-medusa-product-response-correction.json`.
- `PostCartsIdLineItems` requires the returned cart ID and line-item ID,
  variant ID, and quantity. Evidence:
  `2026-08-13-medusa-line-item-response-correction.json`.

The resulting canonical SHA-256 is
`c0b9c6bf1b149a0e458de9fbda4f7bad3cf6f9f7eb4ff383bded3b09d23e50ef`.
Both evidence files omit headers, credential values, request bodies, and
response bodies. This is Corpus-reviewed local target evidence, not an
official Medusa contract claim.

## Safe trace and redaction

The safe trace is embedded in each `result.json`; no raw Playwright trace is
published. Surface keys are limited to
`disposition,event,failureCode,method,operationId,outcome,page,parse,path,reviewId,sequence,status`.
Hybrid adds
`eventCursor,evidenceId,projectionVersion,sessionVersion,source`; chat uses the
same provenance keys without `reviewId`. No trace entry contains headers,
query values, cookies, request bodies, response bodies, credential values, or
private-form content.

## QA follow-up, not acceptance blockers

- improve the visual hierarchy of later feature surfaces and their
  empty/loading/error/review states;
- correct wrong-direction overflow in docked non-maximized complex surfaces;
- replace repeated tester vocabulary such as `consequences` with varied
  ordinary product language while preserving review semantics;
- continue feature-by-feature Behavior Note depth beyond this accepted
  ecommerce path.

Earlier failed and partial runs remain failed in
`docs/corpus-agent-design/final-integration-tasks-and-process.md`. They are not
reclassified by these three accepted replacements.
