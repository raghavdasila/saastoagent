# Corpus Current Context

Updated: 2026-08-05

## Repository Boundary

- Authoritative checkout: `D:\Dev\AI Projects\saastoagent-v0.1`.
- RouteDeck at `D:\Dev\AI Projects\routedeck` is read-only by default.
- `docs/corpus-agent-design/feature-behavior-notes.md` is user-owned and must
  never be edited.
- Main Corpus and `docs/corpus-agent-design/workbench/design-state.json` are
  authoritative; `mockruns/**` is reference-only.
- Source Hub/API Source work exists in a separate parallel lane and is out of
  scope for the next Lounge + Workspace + Agents foundation slice.

## Current Product And Design State

- Corpus is a chat-first RouteDeck host with public Lounge, owner identity and
  conversations, authenticated Workspace Home, and an experimental Sources/API
  path.
- Corpus owns authentication, public conversation authorization/mapping,
  product behavior, domain truth, and user-visible recovery. RouteDeck owns
  legal interaction topology, operation supervision, internal sessions,
  durable run state, projections, replay, and framework diagnostics.
- Design Studio now authors single-turn behavior evals, adaptive
  feature-conversation evals, product journeys, operation source availability,
  readiness/completeness diagnostics, and product-semantic behavior without
  technical RouteDeck IDs.
- `contracts/corpus-agent-design-routedeck-manifest.json` owns the accepted
  Studio-to-compiled implementation mapping. Current global parity passes.
- Primary and evaluation model providers are independently selectable between
  Ollama and OpenAI without fallback. OpenAI uses the Responses API.
- NavGraph Agent Context and Invocation Trace remain read-only RouteDeck-owned
  diagnostics rendered inside the Corpus shell.

## Evaluation Evidence

- Behavior/conversation execution records model usage, durable operation
  events, deterministic state/operation assertions, transcripts, and semantic
  judge evidence in `.runtime/evaluations/**`.
- Real product-journey execution uses isolated Corpus backends/frontends,
  disposable SQLite state, official Playwright Chromium, Mail.tm, and real
  Gmail SMTP.
- Product journeys currently pass 4/8: register/sign-in, unknown reset
  neutrality, email verification, and invalid-verification rejection.
- Product journeys currently fail 4/8: duplicate-registration alert,
  password-reset credential/conversation handoff, verification rate-limit
  alert, and known mail-outage recovery.
- These four failures are currently Corpus feature/application-integration
  bugs; no RouteDeck framework change is proven.

Detailed evidence:
`logs/20260805_lounge_evaluation_and_foundation_boundary.md`.

## Architecture Finding

The intended backend is a modular monolith with vertical feature slices,
ports/adapters, central composition, explicit cross-feature handoffs,
server-authoritative product truth, and fail-closed recovery. RouteDeck feature
ownership is semantically sound, but Corpus package boundaries are only
partially enforced: Lounge depends on concrete auth types, generic/shared
contracts leak through Workspace declarations, password-reset transition lacks
one application coordinator, and there is no import-boundary gate.

## Validation

- Backend: 86 passed; one upstream deprecation warning.
- Frontend: 47 passed; typecheck and production build passed.
- Design Studio: 33 passed; typecheck and production build passed.
- Studio-to-RouteDeck parity passed.
- Official Playwright Chromium and real Gmail-to-Mail.tm delivery passed.
- Desktop and 390 px Studio checks had no horizontal overflow or browser
  console errors/warnings.
- Four of eight real Lounge product journeys passed; four retained genuine
  failures and evidence rather than being rewritten to pass.

## Runtime

```powershell
docker compose up --build -d backend frontend
pnpm --dir docs/corpus-agent-design/workbench dev --host 0.0.0.0 --port 8782 --strictPort
```

- Corpus frontend: `http://127.0.0.1:5199/`
- Backend readiness: `http://127.0.0.1:8099/readyz`
- Authoritative Studio: `http://127.0.0.1:8782/`
- `8771` and `8783` are stale Studio/notebook paths.
- Product-journey runs use isolated ports recorded in each result artifact;
  they do not mutate normal `.runtime` databases.

## Git And Working Tree

- Branch `main` is one commit ahead of `origin/main`.
- Local unpushed commit: `8a07311 feat(corpus): execute Lounge evaluations
  with selectable models`.
- Twenty-seven newer implementation/design/evaluation files are staged and
  uncommitted.
- Documentation/context and pre-existing standalone-reference/evidence work
  remain unstaged or untracked. Do not commit, push, reset, clean, or restage
  without explicit user authorization.

## Next Step

Start from
`context_checkpoints/2026-08-05-lounge-evaluation-and-foundation-handoff.md`.
The next session first collects context and produces a module-wise audit,
ordered todos, target architecture, and exact plan for Lounge + Workspace +
Agents. Source Hub/API Source is excluded. Stop for approval before
implementation.

## Documentation Owners

- Current handoff:
  `context_checkpoints/2026-08-05-lounge-evaluation-and-foundation-handoff.md`
- Session evidence:
  `logs/20260805_lounge_evaluation_and_foundation_boundary.md`
- Runtime/auth/RouteDeck boundary:
  `architecture/components/corpus-routedeck-boundary.md`
- Source ownership: `architecture/code-map.md`
- Runtime flows: `SYSTEM_FLOW_INDEX.md`
- Executable validation: `test_index/README.md`
- Local execution: `docs/local-runtime-runbook.md`
