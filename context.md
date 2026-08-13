# Corpus Current Context

Updated: 2026-08-13

## Current State

Corpus is the authoritative checkout. The current local product slice is
accepted from Lounge through Source, Agent, Designer, Builder, Sandbox,
Evaluation, Channels/Deployment, the hosted Agent, and Operations in three
independent interaction modes: direct surfaces, ordinary owner-language chat,
and a continuing hybrid conversation.

The accepted ecommerce path stages an attached API definition without
processing it, explicitly analyzes it, renders its persisted ToolRouter
semantic graph, reviews the effective API definition, curates product search,
cart creation, and add-to-cart, creates and sources an Agent, generates and
reviews its design, assembles one immutable build asynchronously, schedules
exact-build evaluation coverage, runs a real Medusa product search in Sandbox,
deploys an eligible build through review, survives backend/worker restart,
searches the hosted Agent, creates a cart and adds one item through separate
public reviews, and exposes owner-only Operations evidence and promotion.

The immutable lineage remains owner and conversation scoped. RouteDeck owns
legality, review, state transitions, projection, and NavGraph execution.
Corpus owns product persistence, adapters, public routes, surfaces, and the
Source/Agent/design/build/evaluation/deployment/interaction identities. The
neutral Source, execution, and delivery runtimes remain behind Corpus-owned
adapters. The user-owned
`docs/corpus-agent-design/feature-behavior-notes.md` remains untouched.

## Accepted Ecommerce Evidence

- Surface-only run `20260812T183856Z-02c48c5a50` passed 39/39 with 28
  screenshots, a 478.44-second raw uncut 1x video, 734 allowlisted safe-trace
  events, and zero unexpected HTTP, console, page, or request failures.
- Hybrid run `20260812T221223Z-0e9ec6eb55` passed 40/40 with 27 screenshots,
  26 chat-operation events plus direct surface actions in the same
  conversation, a 790.64-second raw uncut 1x video, 1,863 safe-trace events,
  and zero unexpected diagnostics.
- Ordinary-chat-only run `20260812T222652Z-403a886798` passed 39/39 with 27
  screenshots, 44 operation events across ordinary owner messages, a
  921.60-second raw uncut 1x video, 2,214 safe-trace events, and zero
  unexpected diagnostics.

All three runs used the same behavior and real local Medusa integration, but
created independent owner/conversation/Source/Agent/build lineages. Each
completed one real product search, one reviewed cart creation, and one reviewed
add-to-cart for exactly one `Medusa T-Shirt`; no write occurred before review.
Credentials remained surface-only. Chat prompts contain business intent rather
than Corpus/RouteDeck operation IDs, feature IDs, routes, or UI instructions.

The exact hashes, video paths, retained IDs, diagnostic allowlists, and claim
boundaries are in
`docs/superpowers/validation/2026-08-13-horizontal-ecommerce-chat-surface-hybrid.md`.
Earlier failed and partial campaigns remain immutable historical evidence in
the controlling task/process document; they are not reclassified by these
passes.

## Product Corrections In This Slice

- Source inventory now refreshes while Source Hub is mounted, including when
  chat creates the first Source after an initially empty inventory.
- Builder and Evaluation refresh authoritative asynchronous state without
  object-identity polling races.
- The reviewed effective local Medusa API definition adds response-identity
  corrections for `GetProducts` and `PostCartsIdLineItems`; its canonical hash
  is `c0b9c6bf1b149a0e458de9fbda4f7bad3cf6f9f7eb4ff383bded3b09d23e50ef`.
- Sandbox and hosted-Agent execution retain bounded same-session response
  references so an explicitly approved cart can receive the product variant
  selected by the prior search without exposing response bodies or credentials.
- Public hosted-Agent write operations stage a RouteDeck review and expose
  Corpus-owned Approve/Reject controls; rejection or missing review makes no
  external call.
- Public failure-event projection omits superseded provisional failures, while
  owner Operations retains the complete safe interaction evidence.
- Operations can promote the exact matching deployed interaction requested by
  the owner without turning read-only inspection into promotion.

## QA And Review Boundary

The product pipeline is ready for code review and structured QA, not a
production/SLA claim. The final ecommerce behavior is accepted locally. The
remaining known work is product polish and broader behavior-note depth, not a
blocker to reviewing this committed slice:

- several later surfaces still need stronger visual hierarchy and designed
  empty/loading/error/review states;
- docked non-maximized complex surfaces can overflow in the wrong direction;
- some internal review copy and older recorder prompts overuse the word
  `consequences` and should be replaced with natural product language;
- custom domains remain exploratory/deferred;
- behavior-note breadth beyond the accepted ecommerce Agent path remains
  tracked feature by feature in the controlling task/process document.

No new full journey should be used as a debugger. A QA defect returns to its
owning feature, is reproduced and checked in isolation, and receives a short
normal-speed feature artifact before any replacement horizontal acceptance.

## Runtime

- Local stack: `docker compose up -d backend frontend source-worker`.
- Corpus: `http://127.0.0.1:5199/`.
- Backend readiness: `http://127.0.0.1:8099/readyz`.
- Local Medusa: `http://127.0.0.1:9100/health`.
- The accepted runs used the configured real model provider with no fallback.
- Runtime and migration health must be checked again before a future QA
  campaign; this closeout did not relaunch or mutate the stack.

## Boundaries

- The sibling RouteDeck checkout remains separate. This closeout makes no
  RouteDeck change.
- The user-owned behavior notes are read-only and were not edited.
- Runtime videos and screenshots remain local artifacts; their paths and hashes
  are committed in validation documentation rather than committing large media.
- This commit is a meaningful WIP review checkpoint. It is not a push or a
  production deployment.

## Restart Owners

- Controlling task and process:
  `docs/corpus-agent-design/final-integration-tasks-and-process.md`
- Owner behavior authority (read-only):
  `docs/corpus-agent-design/feature-behavior-notes.md`
- Current validation:
  `docs/superpowers/validation/2026-08-13-horizontal-ecommerce-chat-surface-hybrid.md`
- Current checkpoint:
  `context_checkpoints/2026-08-13-ecommerce-three-mode-acceptance.md`
- Current log:
  `logs/20260813_ecommerce_three_mode_acceptance.md`
- Architecture ownership: `architecture/code-map.md`
- Runtime flows: `SYSTEM_FLOW_INDEX.md`
- Validation meaning: `test_index/README.md`
- Historical accepted baseline:
  `context_checkpoints/2026-08-10-horizontal-evidence-closeout.md`
