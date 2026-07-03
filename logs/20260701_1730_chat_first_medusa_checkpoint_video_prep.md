# 2026-07-01 17:30 IST - Chat-First Medusa Checkpoint And Video Prep

## Summary

Prepared the Corpus/Medusa demo for a new recording using a checkpoint strategy instead of recording first and hoping the flow works. The final public-checkout rehearsal now passes end to end with natural chat: product discovery, size choice, cart add, shipping, payment, order placement, and order readback.

No final video was recorded in this pass. The latest proof run used `DEMO_RECORD_VIDEO=0` so the user can approve the transcript and screenshots before recording.

## Product Changes

- Fixed deployed-agent order continuity after checkout. A terminal workflow result such as `POST /store/carts/{id}/complete` now records the returned `order` as `/store/orders` instead of keeping the cart as the active resource.
- Fixed follow-up readback routing. After an order is active, a natural request like `Can you show my order?` stays in the execution frame and calls `GET /store/orders/{id}` with the remembered order id.
- Preserved generic behavior: the terminal-result collection path is derived from returned resource keys and sibling collection paths, not from Medusa-specific ids or product names.
- Earlier fixes in this video-prep lane kept public greetings in normal chat, restored true SSE model streaming for Corpus/deployed-agent responses, exposed approval-policy controls in the deployment surface, improved selected-variant memory, and improved checkout continuation for shipping/payment actions.
- The recorder script now supports checkpointed owner setup and public checkout passes, with video disabled for proof runs and pacing controls separated from browser slomo.

## Files Changed

- `backend/services/agent/rest_operator.py`
- `backend/services/agent/execution_frames.py`
- `backend/tests/test_rest_catalog.py`
- `backend/tests/test_execution_frames.py`
- `backend/tests/test_api_orchestration.py`
- `frontend/src/components/appGraph/AppGraphShell.tsx`
- `frontend/scripts/record-chat-first-final.mjs`
- `test_targets/CREDS.md`

## Verification

- `docker compose exec -T backend python -m pytest backend/tests/test_rest_catalog.py -k "not docker_runtime_uses_stable_dev_encryption_key" -q`
  - Result: `51 passed, 1 deselected`
- `docker compose exec -T backend python -m pytest backend/tests/test_execution_frames.py -q`
  - Result: `17 passed`
- `docker compose exec -T backend python -m pytest backend/tests/test_api_orchestration.py -k "public_generic_capability_greeting or public_product_catalog_question or approved_public_policy_executes_prepared_financial_target or exact_order_lookup_bypasses_active_cart_frame or active_order_read_uses_stored_order_id_without_user_repeating_id" -q`
  - Result: `5 passed, 25 deselected`

Known excluded test:

- `test_docker_runtime_uses_stable_dev_encryption_key` is still excluded from the broad REST catalog run because the backend container cannot see `/app/saastoagent-v0.1/docker-compose.yml` in its current compose layout.

## Browser Checkpoint Evidence

Owner setup checkpoint reused:

- `frontend/recordings/checkpoint-owner-setup-1782903485581/checkpoint.json`
- Agent: `Medusa Shopping Assistant 5581`
- Public URL: `http://localhost:3000/a/medusa-shopping-assistant-5581`

Passing public checkout checkpoint:

- Artifact root: `frontend/recordings/checkpoint-public-checkout-1782907082540`
- `RECORDER_EXIT=0`
- Policy seed phase: passed
- Public checkout phase: passed
- Order id: `order_01KWERRDY02G08SGPCP042XNV0`
- Screenshots:
  - `frontend/recordings/checkpoint-public-checkout-1782907082540/screenshots/19-public-final-fresh-session.png`
  - `frontend/recordings/checkpoint-public-checkout-1782907082540/screenshots/20-public-final-order-readback.png`

Final public transcript:

1. User: `Hi, what products do you have?`
   Assistant listed Medusa Sweatshirt, Shorts, Sweatpants, and T-Shirt with available sizes.
2. User: `The sweatshirt sounds good. What sizes are available?`
   Assistant listed S, M, L, XL.
3. User: `I'll take a medium.`
   Assistant selected Medusa Sweatshirt size M and offered next actions.
4. User: `Yes, please add it to my cart.`
   Assistant added it to cart.
5. User: `What shipping options do I have?`
   Assistant listed Standard Shipping and Express Shipping.
6. User: `Standard Shipping works.`
   Assistant applied Standard Shipping.
7. User: `How can I pay?`
   Assistant listed `pp_system_default`.
8. User: `Use the default payment option.`
   Assistant created/used the default payment option.
9. User: `Place the order.`
   Assistant placed order #21 for 1 x Medusa Sweatshirt, total 20 EUR.
10. User: `Can you show my order?`
    Assistant read back order #21 with the same order id, item, status, and total.

## Next Step

Wait for user confirmation on this proof, then run the final video recording with video enabled, no browser slomo, readable pacing through explicit waits and character typing, and a fresh logged-out Corpus start.

## Final Recording Update - 2026-07-01 20:26 IST

Final video recording completed after one product bug was found and fixed during the recording attempt.

Bug found:

- The context-panel deployment card showed a filled "Save deployment" form, but the save path was dispatching through the generic graph action flow and reopening `operation_review.deployment.save` instead of persisting `deployment.save`.
- Evidence: the public deployed page showed "Agent unavailable"; the database row for the new agent still had `enabled = false`, `visitor_auth_mode = inherit_from_connection`, and the default welcome message.

Fixes made:

- `frontend/src/components/appGraph/AppGraphShell.tsx`
  - The deployment card now saves through the existing `/saas-agents/{id}/deployment` REST endpoint that it already reads from.
  - The deployment query is refreshed on save success.
  - The stale "deployment save is not currently legal" warning was replaced with a real save-error state.
- `frontend/scripts/record-chat-first-final.mjs`
  - The recorder now scopes the deployment save click to the deployment settings card submit button.
  - It now asserts backend deployment proof before continuing: enabled, anonymous visitor access, sandbox execution, confirm write policy, and a live public deployed-agent profile.
  - The final recording mode runs owner setup, seeded checkout policies, active-policy visibility, and public checkout without browser slomo.

Verification:

- `docker compose exec -T frontend node --check scripts/record-chat-first-final.mjs`
  - Result: passed
- `docker compose exec -T frontend npm run build`
  - Result: passed
- Database proof for final agent:
  - Agent: `Medusa Shopping Assistant 4301`
  - Slug: `medusa-shopping-assistant-4301`
  - Deployment: `enabled = true`, `visitor_auth_mode = anonymous`, `execution_mode = sandbox`, `default_write_policy = confirm`
- Recorder proof:
  - Artifact root: `frontend/recordings/final-natural-video-1782917454301`
  - `RECORDER_EXIT=0`
  - Phases: `owner_setup:passed`, `seed_checkout_policies:passed`, `active_policies:passed`, `public_checkout:passed`
  - Order id: `order_01KWF2WC47MQYKGMGKQF41JYS0`
  - Video: `frontend/recordings/final-natural-video-1782917454301/videos/page@a72b0cd3369aae6b9892cb40f7ca0347.webm`
  - Video size: 20.99 MB

Final public transcript:

1. User: `Hi, what products do you have?`
   Assistant listed Medusa Sweatshirt, Shorts, Sweatpants, and T-Shirt with sizes.
2. User: `The sweatshirt sounds good. What sizes are available?`
   Assistant listed S, M, L, and XL.
3. User: `I'll take a medium.`
   Assistant selected Medusa Sweatshirt size M and offered to add it.
4. User: `Yes, please add it to my cart.`
   Assistant added it to cart.
5. User: `What shipping options do I have?`
   Assistant listed Standard Shipping and Express Shipping.
6. User: `Standard Shipping works.`
   Assistant applied Standard Shipping.
7. User: `How can I pay?`
   Assistant listed `pp_system_default`.
8. User: `Use the default payment option.`
   Assistant used the default payment option.
9. User: `Place the order.`
   Assistant placed order #23, `order_01KWF2WC47MQYKGMGKQF41JYS0`, for 1 x Medusa Sweatshirt, total 20 EUR.
10. User: `Can you show my order?`
    Assistant read back order #23 with the same order id, item, pending status, and total.

## Full-Screen CDP Recording Update - 2026-07-02 00:45 IST

The earlier Playwright `.webm` recording was rejected because it looked sluggish. A Windows desktop capture attempt was also rejected during verification: `gdigrab` only sampled about 3.5 fps on this desktop, and the Python `dxcam` path returned no frames. The final accepted recording path uses Chrome DevTools Protocol screencast frames from the live browser page, then assembles them into a 1920x1080 MP4 at 30 fps.

Capture helpers added/updated:

- `frontend/scripts/capture-visible-demo.py`
  - Added an `mss` fallback backend for desktop capture experiments.
- `frontend/scripts/capture-ffmpeg-desktop.py`
  - Added a stop-file controlled FFmpeg desktop capture helper.
  - Added encoder selection for hardware/MediaFoundation tests.
- `frontend/scripts/cdp-loopback-proxy.mjs`
  - Added a tiny host CDP proxy so Docker Playwright can attach to Chrome even when Chrome binds DevTools to loopback only.
- `frontend/scripts/record-cdp-screencast.mjs`
  - Added full-resolution CDP screencast frame capture with timestamped frame manifest and concat file.
- `frontend/scripts/record-chat-first-final.mjs`
  - Added configurable viewport width/height.
  - Added `DEMO_KEEP_BROWSER_OPEN=1` so an external recorder can stop before the isolated browser is cleaned up.

Final CDP recording verification:

- Artifact root: `frontend/recordings/cdp-full-screen-final-1782932622657`
- Video: `frontend/recordings/cdp-full-screen-final-1782932622657/screen.mp4`
- Video metadata: `1920x1080`, SAR `1:1`, DAR `16:9`, `29.99 fps`, duration `00:10:01.43`
- Frame source: `8,471` CDP screencast JPEG frames, zero zero-byte frames
- Phases: `owner_setup:passed`, `seed_checkout_policies:passed`, `active_policies:passed`, `public_checkout:passed`
- Agent: `Medusa Shopping Assistant 2657`
- Public URL: `http://127.0.0.1:3007/a/medusa-shopping-assistant-2657`
- Deployment proof: enabled, anonymous visitor access, sandbox execution, confirm-before-writes policy
- Order id: `order_01KWFHM1TTA6RM2BNS978AJVF9`
- Final screenshot proof: `frontend/recordings/cdp-full-screen-final-1782932622657/screenshots/20-public-final-order-readback.png`

Final public transcript:

1. User: `Hi, what products do you have?`
   Assistant listed Medusa Sweatshirt, Shorts, Sweatpants, and T-Shirt with sizes.
2. User: `The sweatshirt sounds good. What sizes are available?`
   Assistant listed S, M, L, and XL.
3. User: `I'll take a medium.`
   Assistant selected Medusa Sweatshirt size M.
4. User: `Yes, please add it to my cart.`
   Assistant added it to cart.
5. User: `What shipping options do I have?`
   Assistant listed Standard Shipping and Express Shipping.
6. User: `Standard Shipping works.`
   Assistant applied Standard Shipping.
7. User: `How can I pay?`
   Assistant listed `pp_system_default`.
8. User: `Use the default payment option.`
   Assistant used the default payment option.
9. User: `Place the order.`
   Assistant placed order #25, `order_01KWFHM1TTA6RM2BNS978AJVF9`, for 1 x Medusa Sweatshirt, total 20 EUR.
10. User: `Can you show my order?`
    Assistant read back order #25 with the same order id, pending status, item, and total.
