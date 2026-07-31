# Corpus Current Context

Updated: 2026-07-31

## Repository Boundary

- Authoritative Corpus checkout: `D:\Dev\AI Projects\saastoagent-v0.1`.
- `docs/corpus-agent-design/feature-behavior-notes.md` is user-owned and must
  never be edited by Codex.
- Sibling `D:\Dev\AI Projects\routedeck` is read-only by default. The
  server-owned-conversation work included explicit, plan-limited permission to
  change RouteDeck; that permission is exhausted. Obtain new explicit approval
  for any further upstream change.
- No Git operation was performed during the 2026-07-30/31 session.

## Live Product State

- Corpus is a bearer-authenticated, chat-first RouteDeck host with public
  Lounge, authenticated Workspace Home, and the experimental Sources/API path.
- The frontend keeps access tokens in memory, browser refresh credentials in
  IndexedDB behind Web Locks, and a public Corpus conversation ID per tab.
  Platform-neutral transport/storage contracts allow a native client to supply
  its own secure adapters; no native adapter is implemented yet.
- Corpus owns identity, conversation authorization, and the opaque mapping from
  public conversation IDs to internal RouteDeck session IDs. RouteDeck alone
  provisions and owns runtime sessions, active runs, durable interaction state,
  replay, and restart interruption.
- `RouteDeckRuntime.provision_session(...)` is the single session-creation
  boundary used by both RouteDeck HTTP and Corpus conversation creation.
- The frontend has a bearer-only authorized transport and a conversation
  transport that adds only `X-Corpus-Conversation-ID`. Sources uses the injected
  authorized transport and has no global fetch/session singleton.
- Lounge account Operations use an injected Corpus credential-transition port;
  feature handlers have no HTTP dependency. Browser headers are an adapter,
  while credential values remain outside RouteDeck state/history.
- Active Python/TypeScript conversation contracts are generated from strict
  Pydantic models. Legacy SSE/history decoders enforce exact field sets,
  request-ID Unicode-code-point limits, JavaScript-safe version integers, and
  aligned history identifier semantics.
- `lounge.home` declares a generic RouteDeck entry turn. Its first assistant
  text is model-generated, not a hardcoded frontend/backend message. Current
  implementation uses the generic Corpus system prompt; the Lounge-specific
  `features/lounge/prompt.py` instruction exists but is not wired into the
  entry agent.

## Runtime

Local Docker services were healthy at closeout:

```powershell
docker compose up --build -d
```

- Product: `http://127.0.0.1:5199/`
- Backend readiness: `http://127.0.0.1:8099/readyz`
- RouteDeck Agent Design Studio / notebook: `http://127.0.0.1:8771/`
- Real local model: host Ollama `gemma4:latest`; no model fallback exists.

The canonical restart proof is:

```powershell
.\.venv\Scripts\python.exe -m scripts.smoke_restart_recovery_isolated
```

It owns a disposable backend process plus fresh Corpus-auth and RouteDeck
SQLite databases, proves durable interruption across immediate restart, and
removes the owned runtime on success. It never selects `.runtime` databases.

## Validation At Closeout

- Corpus backend: 69 passed; one upstream Starlette/httpx warning.
- Restart safeguards: 27 passed.
- Frontend: 32 passed; strict typecheck and production build passed earlier in
  the same implementation slice.
- RouteDeck core: 88 passed plus typecheck.
- RouteDeck focused public-contract/generation lane: 36 passed.
- Real isolated restart smoke passed against local Ollama: owner authorized,
  public conversation preserved, run recovered as `turn_interrupted`, temporary
  auth and RouteDeck databases removed, normal runtime untouched.
- Local product, readiness, and Studio URLs returned HTTP 200; all three Docker
  services reported healthy.
- Documentation coverage mapped every changed Corpus owner. The full advisory
  still emits unrelated warnings from checked-in `mockruns/**/node_modules`.

Detailed evidence: `logs/20260731_server_owned_conversations.md` and
`context_checkpoints/2026-07-31-server-owned-conversations.md`.

## Known Risks And Next Step

- The normal `.runtime/routedeck.sqlite` may contain internal RouteDeck sessions
  created by pre-isolation restart probes. They were not directly deleted
  because no safe public RouteDeck deletion contract exists. New restart proofs
  do not add such rows.
- Two failed disposable diagnostic directories may remain under Windows Temp;
  they are inactive, isolated from the running stack, and recorded in the
  checkpoint.
- Multi-worker active-run handoff, native secure credential adapters, broader
  product features, and production persistence remain unimplemented.
- Next session: inspect the compiled prompt/context policy path for
  `lounge.home` and decide whether the unused Lounge-specific prompt should be
  wired, removed, or represented solely through scoped AgentPolicies. Follow
  the mandatory Studio-to-RouteDeck mapping gate before changing behavior.

## Documentation Owners

- Runtime/auth/session boundary:
  `architecture/components/corpus-routedeck-boundary.md`
- Executable validation meaning: `test_index/README.md`
- Runtime flows: `SYSTEM_FLOW_INDEX.md`
- Completed implementation plan:
  `docs/superpowers/plans/2026-07-30-server-owned-conversations-and-agent-session-selection.md`
- Product design authority: RouteDeck Agent Design Studio and
  `contracts/corpus-agent-design-routedeck-manifest.json`
