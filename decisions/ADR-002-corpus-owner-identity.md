# ADR-002: Corpus Owner Identity And RouteDeck Claims

Status: accepted and locally validated, including Gmail SMTP acceptance

Date: 2026-07-22

## Context

Corpus is multi-user, while users of deployed agents are a different future
identity realm. RouteDeck deliberately leaves product authentication and
principal-to-session selection to its host. Corpus therefore needs durable
owner identity without placing product authentication middleware in RouteDeck.

## Decision

- Implement only Corpus owners in this slice. Do not create deployed-agent user
  tables, cookies, adapters, or placeholder contracts.
- Contain FastAPI Users 15.0.5 behind Corpus-owned managers, services, schemas,
  and a transaction-aware SQLAlchemy adapter.
- Store owner identity in a separate Alembic-managed database. Startup checks
  revision `0001_owner_auth` and never creates or migrates tables.
- Give every owner one personal organization and an `owner` membership.
- Authenticate browsers with revocable opaque cookies whose SHA-256 hashes are
  the only stored credentials. Support multiple browser sessions per owner.
- Permanently claim an adopted guest RouteDeck session and select it later only
  through a matching auth session and opaque owner-route handle.
- Treat verification as advisory. Password reset revokes every auth session and
  owner-route handle for that owner.
- Keep Gmail behind the owner-mail delivery port. The standard-library adapter
  was implemented only after the official STARTTLS reference succeeded with
  the real `no-reply@saastoagent.com` App Password.

## Consequences

- An adopted guest cookie can never select the claimed RouteDeck session again.
- Unknown, cross-owner, revoked, and anonymously replayed claimed sessions share
  the same unavailable response.
- Logout or owned-session recovery revokes the current browser identity and
  starts a new guest Lounge; ownership is never converted back to anonymous.
- FastAPI Users can be replaced without changing the HTTP contract or RouteDeck
  selector because it is not exposed to either boundary.
- Verification delivery returns an explicit 503 when Gmail is unconfigured or
  unavailable; reset requests retain their generic 202 anti-enumeration
  response while logging delivery failure.

## Validation

The backend suite covers atomic provisioning, normalization, password policy,
hashing, expiry, revocation, rate limits, claims, cross-user selection,
verification, reset, Gmail adapter behavior, migrations, and the live RouteDeck continuation. The
frontend suite and rendered browser run cover credential UX, fragment removal,
composer lockout, adoption, reload, sign-in, logout, and recovery.
