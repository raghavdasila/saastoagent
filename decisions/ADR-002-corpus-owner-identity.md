# ADR-002: Corpus Bearer Identity And Conversation Selection

Status: accepted and locally validated

Date: 2026-07-30

## Context

Corpus is multi-user and must support browser, mobile, desktop, and CLI clients.
RouteDeck deliberately leaves product authentication and principal-to-session
selection to its host. Raw RouteDeck session identifiers must not become public
identity or conversation handles.

## Decision

- Keep owner identity in the separate Alembic-managed Corpus auth database.
- Use opaque 15-minute bearer access tokens and rotating refresh credentials
  with 7-day idle and 30-day absolute limits. Persist only credential hashes.
- Issue anonymous principals through `POST /api/auth/anonymous`; store browser
  access tokens in memory and refresh credentials in IndexedDB behind Web Locks.
  Native clients use platform-secure storage through the same adapter boundary.
- Give every owner one personal organization and an `owner` membership.
- Model a public Corpus conversation separately from its internal RouteDeck
  session ID. Authenticate the bearer and authorize
  `X-Corpus-Conversation-ID` before selecting the internal session.
- Registration and sign-in atomically adopt the selected anonymous
  conversation, revoke the anonymous credentials, and issue owner credentials.
- Disallow direct Corpus use of RouteDeck `POST /sessions`; conversations are
  created through `POST /api/conversations`.
- Password reset revokes every owner auth session and access credential.

## Consequences

- Browser cookies are not part of identity or RouteDeck session selection.
- Anonymous callers may own one active conversation; owners may own multiple.
- Foreign, malformed, archived, or missing conversations fail explicitly and
  never select another conversation.
- A missing backing RouteDeck session is removed from the caller's catalog so
  an anonymous client can return to first-open conversation creation.
- RouteDeck receives only an authorized internal session ID. Public APIs and
  projections never expose that ID.
- FastAPI Users remains replaceable behind Corpus-owned services and schemas.

## Validation

Backend tests cover issuance, hash-only storage, rotation, stale refresh
rejection, access selection, rate limits, atomic concurrent adoption, sign-out,
password-reset revocation, catalog authorization, direct-session rejection,
and the live bearer-selected host path. Frontend tests cover IndexedDB adapter
behavior, cross-tab rotation locking, selective stale-session reset, bearer and
conversation headers, and owner-credential adoption.
