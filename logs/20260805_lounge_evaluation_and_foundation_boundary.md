# Lounge Evaluation And Foundation Boundary Log

Date: 2026-08-05

## Scope

This session aligned the authoritative Design Studio, current RouteDeck
contracts, Lounge implementation, and executable evaluation evidence. It also
audited whether RouteDeck feature names correspond to clean Corpus backend
module boundaries.

RouteDeck remained read-only except for earlier, separately authorized work
already committed outside this closeout. The user-owned
`docs/corpus-agent-design/feature-behavior-notes.md` remained unchanged.

## Delivered Work

- Added Studio-owned behavior evals, adaptive feature-conversation evals, and
  product-journey definitions without exact-response matching.
- Added operation source authoring and parity against RouteDeck
  `Operation.allowed_sources`.
- Added Studio product-journey authoring, completeness diagnostics, compact
  responsive UI, and explicit partial/unimplemented feature mappings.
- Added selectable Ollama/OpenAI evaluation support and upgraded the OpenAI
  path to the Responses API in the already committed evaluation slice.
- Added real browser product-journey execution with isolated Corpus runtimes,
  official Playwright Chromium, Mail.tm mailboxes, real Gmail SMTP delivery,
  sanitized transcripts, screenshots, traces, deterministic backend-state
  assertions, and explicit usage/cost evidence semantics.
- Added durable operation-event evidence and required/allowed/forbidden
  operation assertions to behavior/conversation evaluation.
- Corrected email-verification UI success so refreshed owner state must prove
  verification.

## Real Product-Journey Evidence

Passed:

1. Register, sign out, and sign in:
   `.runtime/evaluations/20260805T141858Z-10626f5f6e/result.json`.
2. Unknown-account reset remains neutral:
   `.runtime/evaluations/20260805T142918Z-4fc25a7849/result.json`.
3. Resend and confirm email verification:
   `.runtime/evaluations/20260805T143746Z-7d1ef1d50f/result.json`.
4. Invalid verification remains rejected and unverified:
   `.runtime/evaluations/20260805T144213Z-fb5e930538/result.json`.

Failed with genuine product evidence:

1. Password reset changes the credential, but credential revocation causes a
   new anonymous principal to remount the old owner conversation; RouteDeck
   correctly returns conversation-not-found instead of reaching Sign in:
   `.runtime/evaluations/20260805T142618Z-6d7d17ba1b/result.json`.
2. Duplicate registration produces a terminal business conflict but the
   surface does not show the account-neutral alert:
   `.runtime/evaluations/20260805T142802Z-3f560646d3/result.json`.
3. Verification rate limiting is enforced before token generation but its
   product alert is not rendered:
   `.runtime/evaluations/20260805T143833Z-9e73f7bede/result.json`.
4. A known reset-mail outage remains a retained/unfinished product mutation
   instead of visible Corpus-owned recovery:
   `.runtime/evaluations/20260805T144054Z-2ea148f657/result.json`.

The product journeys are surface/account workflows and recorded zero model
invocations. Exact billed cost was not estimated.

## Architecture Finding

The intended backend baseline is a modular monolith with feature-oriented
vertical slices, ports/adapters, central composition, server-authoritative
product truth, Corpus-owned identity/conversations, and RouteDeck-owned legal
interaction state.

Current RouteDeck feature ownership is semantically sound but Corpus module
boundaries are only partially enforced:

- Lounge directly imports concrete auth services, settings, exceptions, mail,
  and rate-limit types instead of a narrow Lounge-owned account port.
- Lounge and Sources import Workspace declarations. Cross-feature destination
  references and imported providers are legitimate; importing generic schema
  helpers from Workspace is implementation leakage.
- Password reset lacks a Corpus application coordinator that guarantees the
  credential transition and valid public-conversation handoff together.
- No automated backend import-boundary gate protects feature ownership.

No RouteDeck framework change is currently proven necessary. A valid terminal
409 that remains pending would require a focused runtime trace before proposing
an upstream change.

## Validation Recorded In This Session

- Backend: 86 passed, one upstream deprecation warning.
- Frontend: 47 passed; strict typecheck and production build passed.
- Studio: 33 passed; strict typecheck and production build passed.
- Studio-to-RouteDeck parity passed.
- `git diff --cached --check` passed.
- Official Playwright Chromium baseline passed.
- Real Gmail SMTP to Mail.tm passed; mailbox cleanup returned HTTP 204.
- Desktop and 390 px Studio browser review passed with no horizontal overflow
  or browser console errors/warnings.
- Documentation coverage passed for all ten closeout files. The full-worktree
  advisory timed out while printing the known large unmatched/noisy tree, so it
  was rerun with the explicit closeout file list.
- Staged and unstaged `git diff --check` passed.

## Git And Working Tree Boundary

- Branch: `main`, one commit ahead of `origin/main`.
- Local unpushed commit: `8a07311 feat(corpus): execute Lounge evaluations
  with selectable models`.
- Twenty-seven newer implementation/design/evaluation files are staged and are
  not committed.
- Documentation, context, standalone-runtime references, evidence, and
  `mockruns/` include pre-existing unstaged/untracked work. This closeout did
  not stage, commit, push, reset, or clean anything.

## Next Session

The next foundation slice is Lounge + Workspace + Agents. Source Hub and API
Source are explicitly excluded because their work proceeded in a separate
parallel lane. Start read-only: collect authoritative context, map Studio to
RouteDeck to Corpus, establish module-wise todos, propose the target backend
architecture and exact implementation plan, then stop for approval.

See `context_checkpoints/2026-08-05-lounge-evaluation-and-foundation-handoff.md`.
