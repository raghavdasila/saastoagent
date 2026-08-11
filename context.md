# Corpus Current Context

Updated: 2026-08-10

## Current State

Corpus is the authoritative checkout. The horizontal Source -> Agent ->
Designer -> Builder -> Sandbox -> Evaluation -> Channels/Deployment -> public
session -> Operations launch baseline is implemented and accepted through
independent ordinary-chat-only, surface-only, and hybrid evidence. The three
recordings are normal-speed and uncut; chat uses ordinary owner language and the
hybrid run proves surface-completed state continuing through later chat.

Architecture-visible product state now follows one exact lineage: Source Hub
renders the persisted ToolRouter semantic graph; Designer renders the shared
proposed topology; Builder compiles and renders the same topology as the
immutable per-build RouteDeck NavGraph; Sandbox shows RouteDeck projection and
ToolRouter clarification evidence; Evaluation and Channels show the exact build
NavGraph; Operations shows the owner-only deployed NavGraph plus safe routing,
clarification, and execution provenance. The public hosted Agent intentionally
does not expose owner diagnostics.

The neutral Source, execution, and delivery runtimes remain behind
Corpus-owned adapters. The user-owned
`docs/corpus-agent-design/feature-behavior-notes.md` remains untouched.

## Current Evidence

- Surface-only run `20260809T153004Z-7cd51d776b` passed 24/24.
- Ordinary-chat-only run `20260809T165131Z-63d1c6220b` passed 24/24 using the
  configured OpenAI model and ordinary owner requests rather than feature,
  operation, route, or UI instructions.
- Hybrid run `20260809T210136Z-853c33486c` passed 25/25. It retained 18
  screenshots, one 474.28-second raw 1x WebM, 968 allowlisted safe-trace events,
  and zero unexpected HTTP, console, page, or request failures. The run visibly
  includes the Source semantic graph, Designer topology, compiled build,
  Evaluation and deployed NavGraphs, Sandbox and public ToolRouter
  clarification, owner-only Operations evidence, restart persistence, and
  390x844 rendering.
- Fresh backend: 421 passed with 6 dependency deprecation warnings.
- Fresh frontend: 25 files / 121 passed; strict typecheck and production build
  passed with the existing large-chunk warning.
- Design Studio: 9 files / 58 passed; strict typecheck passed.
- Generated contract, Studio parity, architecture boundaries, shared
  Designer/Builder topology, and deployed runtime evidence gates are green.

The horizontal launch-baseline evidence requirement is closed. Later feature
depth must retain the same evidence discipline: normal-speed uncut recording,
ordinary owner-language chat, direct surfaces, mixed continuation, and omission
only for sensitive credential entry.

## Runtime

- Start the model-backed local stack with
  `docker compose up -d backend frontend source-worker`.
- Corpus: `http://127.0.0.1:5199/`.
- Backend readiness: `http://127.0.0.1:8099/readyz`.
- Local Medusa: `http://127.0.0.1:9100/health`.
- Horizontal chat evidence used the configured OpenAI provider. There is no
  model fallback in the accepted run.
- Configured migration head: `0012_builder_navgraph`. Runtime current must be
  rechecked before the next browser campaign.

## Remaining Product Work

Proceed to individual behavior-note depth without reopening the accepted
horizontal baseline. Explicit follow-ups include Builder runtime controls,
ToolRouter-generated evaluation CRUD, channel rollback/availability changes,
Operations promotion, and any other binding still marked
`pending_external_evidence`. Do not weaken validation or replace any path with
fixtures or fallbacks.

## Boundaries

- No Git operation was performed.
- RouteDeck changes were made only for proven framework gaps and are recorded in
  `audits/2026-08-10-horizontal-routedeck-changes.md`.
- No user-owned behavior note was modified.
- This is validated local-product evidence, not a production deployment or
  service-level claim.

## Restart Owners

- First controlling authority:
  `docs/corpus-agent-design/final-integration-tasks-and-process.md`
- Owner-authored behavior authority (read-only):
  `docs/corpus-agent-design/feature-behavior-notes.md`
- The active work is the complete final-integration task recorded in the first
  authority above. No narrow feature plan, recorder failure, or previous
  implementation checkpoint supersedes it.
- Supporting historical plan:
  `plans/2026-08-09-designer-navgraph-alignment.md`
- Superseded baseline checkpoint: `context_checkpoints/2026-08-08-horizontal-product-completion.md`
- Accepted horizontal checkpoint: `context_checkpoints/2026-08-10-horizontal-evidence-closeout.md`
- Current validation: `docs/superpowers/validation/2026-08-10-horizontal-chat-surface-hybrid.md`
- Historical validation log: `logs/20260808_horizontal_product_completion.md`
- Architecture: `architecture/code-map.md`
- Runtime flows: `SYSTEM_FLOW_INDEX.md`
- Validation meaning: `test_index/README.md`
