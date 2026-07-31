# Server-Owned Conversations And Lounge Runtime Checkpoint

Date: 2026-07-31

## Resume Boundary

- Authoritative repo: `D:\Dev\AI Projects\saastoagent-v0.1`.
- RouteDeck sibling: read-only by default. The prior named-plan modification
  permission is complete and does not carry forward.
- Never edit
  `docs/corpus-agent-design/feature-behavior-notes.md`.
- No Git operation was performed.

## Completed

- Bearer identity and public Corpus conversation selection replace browser
  cookie session authority.
- Corpus owns authorization and opaque conversation mapping; central
  `RouteDeckRuntime.provision_session(...)` owns all runtime session creation.
- Browser persistence and locking are behind platform adapters; HTTP transports
  are split into bearer-only and conversation-scoped boundaries.
- Lounge credential transitions use an injected Corpus port, with HTTP behavior
  isolated in an adapter.
- Active legacy history/SSE wire models and TypeScript decoders share strict
  generated field authority and exact scalar domains.
- The real restart proof owns a disposable backend plus both SQLite databases,
  proves durable interruption, and removes all owned state on success.
- Docker backend, frontend, and Studio/notebook are healthy locally.

## Current Evidence

- Corpus backend: 69 passed.
- Restart tooling: 27 passed.
- Frontend: 32 passed plus typecheck/build in the completed slice.
- RouteDeck core: 88 passed plus typecheck.
- RouteDeck focused public contract/generation: 36 passed.
- Real local restart smoke passed with request
  `restart-smoke-0a4e5b3c291340dea63ad5736bee94da`.
- Documentation coverage mapped the changed owners; the full advisory retains
  unrelated `mockruns/**/node_modules` warnings.
- URLs: `http://127.0.0.1:5199/`,
  `http://127.0.0.1:8099/readyz`, `http://127.0.0.1:8771/`.

Detailed evidence: `logs/20260731_server_owned_conversations.md`.

## Next Concrete Step

Audit the first Lounge message path before editing it:

1. map Design Studio Lounge entry intent and policies to the current compiled
   Node/Capability/policy context;
2. confirm from current RouteDeck source how node-scoped prompt/policies reach
   the assistant-initiated entry graph;
3. decide whether `backend/src/corpus/features/lounge/prompt.py` should be wired,
   removed, or replaced by scoped AgentPolicies;
4. present any material design correction in the Studio first.

Current fact: the first message is model-generated through
`create_corpus_entry_agent`; no literal greeting is hardcoded. The entry agent
currently receives `CORPUS_AGENT_PROMPT`, while `LOUNGE_AGENT_PROMPT` is unused.

## Known Risks

- Normal `.runtime/routedeck.sqlite` may contain internal sessions from older
  pre-isolation probes; no safe deletion contract currently exists.
- Two failed disposable diagnostic directories may remain in Windows Temp:
  `corpus-restart-smoke-egaf2mrf` and `corpus-restart-smoke-ihqvn53s`.
- A fresh rendered registration/sign-in adoption run after the final
  credential-transition refactor remains unverified.
- Multi-worker live-run handoff and native secure credential adapters remain
  future work.
