# Video-Driven Fix Debt - 2026-07-03

## Purpose

This note marks the boundary between the initial RouteDeck/Corpus refactor checkpoint and the later fixes made to get the chat-first Medusa recording over the line.

The recording fixes are useful evidence, but they are not the final RouteDeck architecture. Treat them as a preservation lane: keep what is genuinely product behavior, replace what is hardcoded for the video, and move reusable runtime mechanics back into RouteDeck.

## Commit Boundary

Boundary commit:

- `d7ce5ff7 chore(video): mark demo-fix boundary`
- Commit body tag: `VIDEO_FIX_BOUNDARY`

Commits after that marker are recording/demo-driven and should be reviewed before being treated as final architecture:

- `63abd197 fix(video): harden public Medusa checkout flow`
- `d770f3d1 fix(video): stabilize deployed chat UI flow`
- `6c589663 chore(video): add recording harness and prep log`

The preceding checkpoint commit is:

- `c45ddd7f refactor(corpus): checkpoint RouteDeck adapter split`

That checkpoint intentionally preserves the current coupling so it can be refactored safely. It is not the intended final boundary.

## What Changed After The Boundary

### Backend deployed-agent checkout hardening

Files:

- `backend/services/agent/rest_operator.py`
- `backend/services/agent/execution_frames.py`
- `backend/services/agent/chat_service.py`
- `backend/scripts/seed_demo_checkout_policies.py`
- `backend/tests/test_api_orchestration.py`
- `backend/tests/test_execution_frames.py`
- `backend/tests/test_rest_catalog.py`

Why it happened:

- The public Medusa checkout recording needed conversational continuity across product selection, variant choice, cart creation, shipping option selection, payment provider/session setup, cart completion, and order readback.
- The deterministic REST executor had to stop treating generic public help prompts as API tasks.
- The public chat needed model-written wording over deterministic operation results instead of raw JSON-looking tool output.

Debt:

- Some ranking and intent rules are Medusa/video-shaped, especially payment and shipping phrase handling.
- Public write policy execution is now optimized for the recorded checkout path.
- The seeding script is demo support, not general platform behavior.

Keep:

- Exact ID extraction for explicit resource reads.
- Deterministic operation result as source of truth before model wording.
- Regression tests that describe real product behavior.

Revisit:

- Payment/shipping special cases should become policy/configuration or generated route metadata, not hardcoded phrase weights.
- Demo policy seeding should stay outside normal runtime paths.

### Frontend recording flow fixes

Files:

- `frontend/src/pages/DeployedAgentChatPage.tsx`
- `frontend/src/components/appGraph/AppGraphShell.tsx`
- `frontend/src/components/agent/LearningPanel.tsx`
- `frontend/src/components/appGraph/corpusActiveSurfaces.tsx`
- `frontend/src/components/appGraph/corpusFrameSurfaces.tsx`
- `frontend/src/components/appGraph/corpusSurfaces.tsx`

Why it happened:

- The final recording needed the deployed chat input/composer to remain visible. The public chat page now uses fixed-height flex layout with a scrollable transcript.
- Owner deployment settings had to persist directly because the graph operation path reopened review state instead of saving the deployment in time for the public page.
- Learning approve/reject had to persist directly during the recording flow.

Debt:

- Direct REST calls from deployment settings and learning review bypass the RouteDeck typed operation path.
- The frontend surface split is useful, but it still consumes app-owned Corpus surface shape rather than a fully library-owned RouteDeck surface runtime.

Keep:

- The fixed-height deployed chat layout.
- The idea of separating frame and active surface renderers.

Revisit:

- Decide which owner settings are ordinary product REST forms and which must flow through RouteDeck operations.
- RouteDeck should own generic active/frame surface selection mechanics; Corpus should define product surfaces like sign-in, API connection, learning policy review, and deployment settings.

### Recording harness and local fixture config

Files:

- `frontend/scripts/record-chat-first-final.mjs`
- `frontend/scripts/record-cdp-screencast.mjs`
- `frontend/scripts/cdp-loopback-proxy.mjs`
- `frontend/scripts/capture-ffmpeg-desktop.py`
- `frontend/scripts/capture-visible-demo.py`
- `frontend/vite.config.ts`
- `logs/20260701_1730_chat_first_medusa_checkpoint_video_prep.md`
- `logs/README.md`
- `test_targets/CREDS.md`

Why it happened:

- The recording campaign needed checkpointed owner setup, policy seeding, public checkout playback, external/CDP recording support, desktop capture fallbacks, and durable evidence logs.

Debt:

- The recorder contains hardcoded demo copy, pacing, selectors, seeded policy shapes, and Medusa fixture assumptions.
- `test_targets/CREDS.md` changed a publishable demo key; treat it as a fixture, not platform logic.

Keep:

- The harness as a reproducible recording/evidence tool.
- The logs as context for why the video fixes exist.

Revisit:

- Move demo constants into explicit scenario config.
- Keep generated recordings, screenshots, proof blobs, and local captures out of git history.

## RouteDeck Boundary Resume Target

The current runtime still does too much in Corpus. The next refactor should move generic technical mechanics into RouteDeck and leave Corpus with product-specific definitions and business handlers.

Move toward RouteDeck:

- Active surface selection and default surface mechanics.
- Route open/switch/back/forward/cancel validation.
- Operation review state construction.
- Pending operation storage conventions.
- Dirty surface tracking mechanics.
- Projection update and operation completion event shaping.
- Generic action dispatch plumbing.
- Generic graph state request/response contract helpers.

Keep in Corpus:

- Product node IDs and action IDs.
- Product surfaces such as sign-in, register, API connection, learning review, deployment settings, catalog, execution, memory, and QA.
- Product/business handlers that touch SaaS agents, connections, generated tools, learning candidates, deployment records, and execution traces.
- Product copy and planning descriptions.

The target library experience should be:

1. Corpus defines product manifest, product surfaces, and product handlers.
2. RouteDeck owns navigation, active surface mechanics, operation review mechanics, projection/runtime state, and dispatch lifecycle.
3. Corpus wires business handlers into RouteDeck without redefining RouteDeck technical behavior under Corpus class names.

## Current Risk Summary

- The current Corpus adapter split is a checkpoint, not the final architecture.
- Video-driven commits after `d7ce5ff7` should not be casually generalized.
- Direct REST UI paths should be either documented as product form behavior or routed back through typed RouteDeck operations.
- Medusa checkout phrase/ranking rules should become metadata/configuration before this runtime is treated as reusable.
