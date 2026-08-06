# Lounge Evaluation And Foundation Architecture Handoff

Date: 2026-08-05

## Resume Boundary

- Authoritative repo: `D:\Dev\AI Projects\saastoagent-v0.1`.
- RouteDeck sibling: `D:\Dev\AI Projects\routedeck`, read-only unless the user
  explicitly authorizes a named upstream change.
- `docs/corpus-agent-design/feature-behavior-notes.md` is user-owned and must
  never be edited.
- `mockruns/**` is reference-only.
- No subagents. No broad TDD ceremony.
- Preserve the current staged, unstaged, and untracked split. Do not perform
  Git operations without a new explicit request.

## Current Git State

- `main` is one commit ahead of `origin/main`.
- `8a07311 feat(corpus): execute Lounge evaluations with selectable models` is
  local and unpushed.
- Twenty-seven newer Studio, evaluation, Lounge, parity, and runner files are
  staged but uncommitted.
- Context/documentation closeout changes are unstaged.

## Completed This Session

- Studio supports behavior evals, adaptive feature-conversation evals, and
  real product-journey definitions.
- Studio supports explicit Chat/Product surface/Both operation sources and
  parity against RouteDeck `allowed_sources`.
- Workspace and Source Hub mappings are explicitly partial; Agents/API Source
  unmapped behavior is not presented as implemented.
- Real isolated Lounge product journeys use Playwright Chromium, Mail.tm,
  Gmail SMTP, disposable SQLite/runtime state, sanitized transcripts,
  screenshots, traces, and deterministic backend assertions.
- Behavior/conversation evaluation records durable operation evidence and
  required/allowed/forbidden operation assertions.
- Backend, frontend, Studio, parity, browser rendering, and real mail baselines
  passed as recorded in
  `logs/20260805_lounge_evaluation_and_foundation_boundary.md`.
- Scoped documentation ownership and both staged/unstaged whitespace checks
  passed. The full-worktree documentation advisory remains too noisy and timed
  out while printing unmatched files.

## Product-Journey Status

Passed 4/8:

- register -> sign out -> sign in;
- unknown-account reset neutrality;
- verification resend and confirmation;
- invalid verification rejection.

Failed 4/8:

- duplicate registration has no visible terminal alert;
- password reset revokes credentials without provisioning/remounting a valid
  conversation for the new anonymous principal;
- verification rate limit has no visible terminal alert;
- known mail outage remains retained/unfinished instead of showing
  Corpus-owned recovery.

These are currently Corpus feature/application-integration bugs. Do not change
RouteDeck unless a trace proves its generic terminal or recovery contract is
incorrect.

## Architecture Baseline To Prove

```text
Design Studio product behavior
  -> implementation manifest
  -> feature-owned RouteDeck declarations and bindings
  -> Corpus application coordinator and domain ports
  -> RouteDeck-supervised operation/session/projection
  -> feature-owned Corpus surface and conversation behavior
```

Backend principles:

- modular monolith;
- feature-oriented vertical slices;
- narrow ports/adapters at domain and external seams;
- one central composition root;
- explicit cross-feature handoffs without implementation leakage;
- Corpus owns authentication and public conversations;
- RouteDeck owns legal interaction and durable runtime state;
- product truth stays server-side; frontend consumes projections;
- failures remain failures and recovery is explicit.

## First Task In The New Session

Work only on the foundation relationship between Lounge, Workspace, and
Agents. Source Hub and API Source are out of scope because their implementation
was developed in a separate parallel lane.

First phase is read-only:

1. Read the repository authority chain required by
   `AGENTIC_CODING_GUIDE.md`, this checkpoint, the Design Studio state, the
   implementation manifest, and current Lounge/Workspace/Agents/auth/runtime/
   frontend source and tests.
2. Inspect current RouteDeck Feature, Node, Operation, provider, guard,
   binding, dispatch, failure, recovery, session, projection, and React client
   contracts read-only.
3. Map `Studio concept -> RouteDeck contract -> Corpus implementation` for all
   three features.
4. Separate legitimate cross-feature references from backend implementation
   leakage.
5. Produce a short module-wise report with current boundaries, violations,
   exact bugs, target package structure, ordered todos, exact affected files,
   E2E evidence, and any true blocker.
6. Stop for approval. Do not implement during this first phase.

## Known Questions For The Plan

- Should Lounge define its own account/recovery ports while `corpus.auth` keeps
  identity invariants and concrete adapters?
- Which application coordinator owns credential transition plus conversation
  replacement/remounting?
- Which shared contract module owns generic empty schemas and cross-feature
  destinations without making Workspace a shared kernel?
- How will Agents own agent identity/configuration/version state while
  Workspace remains a navigation/context home rather than an agent service?
- Which import-boundary check will mechanically prevent future feature
  coupling?

## Stop Conditions

- Do not pull Source Hub/API Source implementation into this slice.
- Do not put technical RouteDeck identifiers into Studio state.
- Do not duplicate RouteDeck interaction state inside Corpus.
- If the approved behavior cannot map to a current RouteDeck contract, report
  the exact missing contract and wait for explicit upstream authorization.
