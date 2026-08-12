# Builder/Evaluation And Lounge History Validation

Date: 2026-08-11

## Product truth

- Builder completion schedules one durable `Generated coverage` ToolRouter set
  for the exact immutable build. Existing queued/running/ready/failed history is
  never overwritten; failed generation requires the explicit Evaluation retry.
- Sandbox uses the exact running build, retains the RouteDeck runtime and
  ToolRouter clarification, and made one validated real call to local Medusa.
- Evaluation ran the automatically generated case for the same build and made
  that build eligible for deployment.
- Authenticated RouteDeck Back preserves the exact owner/conversation and now
  restores the prior Lounge article before the declared Continue to Workspace
  operation. No conversation reset or direct URL mutation is used.

## Real integration evidence

- Local Medusa 2.13.6 taxonomy was created and normalized through official
  `medusa exec` workflows: product type `Apparel`; tags `Catalog` and
  `Essentials`. The schema-compatible response was then validated through the
  real Sandbox call.
- A duplicate local Ollama server produced a real visible generation failure
  (`memory layout cannot be allocated`). After consolidating to one server, the
  unchanged ToolRouter baseline produced one accepted case using
  `gemma4:latest` (`c6eb396d...`) and independent `qwen2.5-coder:7b`
  (`dae161e2...`). No model fallback or canned case was introduced.

## Retained isolated evidence

- Builder/Sandbox/Evaluation run: `20260811T153036Z-270ee701d6`.
- Exact lineage: build `b53256e4-8516-4232-97e9-dd83be66fbe9` and Sandbox run
  `69ced953-acfd-4eb0-bf78-4413dcd199a4`.
- Feature film:
  `artifacts/horizontal-product-surface/20260811T153036Z-270ee701d6/builder-sandbox-evaluation-maximized.webm`.
  It is 60.160 seconds, maximized, normal-speed (1.0x), SHA-256
  `71b889689a0884f907a02633134d1c3ff49bd20872d0b3f11ec8bd8b5f93cc1d`.
- All 21 retained assertions are true; the original result ledger says failed
  only because the recorder expected 20 assertions. The corrected isolated
  verifier accepts the immutable artifact as 21/21 without rewriting it.
- Lounge desktop film:
  `artifacts/authenticated-lounge-history/20260811T151635748Z/authenticated-lounge-history-desktop-normal-speed.webm`
  (10.066 seconds).
- Lounge mobile film:
  `artifacts/authenticated-lounge-history/20260811T151635748Z/authenticated-lounge-history-mobile-normal-speed.webm`
  (15.100 seconds). Mobile uses native browser Back because the responsive
  Corpus header still hides visible Back/Forward controls at 390px.

## Gates

- Horizontal recorder plus Builder/Sandbox focused backend: 75 passed.
- Lounge/Workspace backend: 21 passed.
- Lounge/frontend shell-focused: 36 passed.
- Frontend typecheck: passed.
- Builder milestone diagnostics: zero unexpected HTTP, console, page, or
  request failures.
- Lounge capture-window diagnostics: zero relevant non-2xx HTTP responses and
  zero console warnings/errors.
