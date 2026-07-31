# Corpus Owner Authentication

This package owns Corpus owner identity. It does not model users of deployed
agents.

## Dependencies

- `fastapi-users[sqlalchemy]==15.0.5` - MIT; user-manager password,
  verification, and reset contracts, contained behind Corpus interfaces.
- `fastapi-users-db-sqlalchemy==7.0.0` - MIT; adapted so Corpus owns commit.
- `sqlalchemy==2.0.51`, `aiosqlite==0.22.1`, `alembic==1.18.5`, and
  `email-validator==2.3.0`.

FastAPI Users is in maintenance mode. Corpus does not expose its browser token
strategies, routes, database session strategy, or persistence types.

## Runtime

`scripts/init-local.ps1` generates separate reset/verification secrets, adds
the explicit bearer-token and SMTP settings, and applies Alembic migrations to
`.runtime/corpus-auth.sqlite3`. Backend startup only verifies the configured
revision. Run an upgrade explicitly with:

```powershell
.\.venv\Scripts\python.exe -m corpus.auth.migrations
```

The API returns opaque access and refresh tokens to clients. Access tokens are
short-lived and kept in client memory; refresh tokens are stored by the client
appropriate to its platform. The database stores only their SHA-256 digests.
Public Corpus conversation IDs select conversations without exposing internal
RouteDeck session IDs.

## Gmail Delivery

The Gmail SMTP reference passed on 2026-07-22 using the dedicated
`no-reply@saastoagent.com` account, its App Password, and STARTTLS on
`smtp.gmail.com:587`. `GmailSmtpMailDelivery` uses Python's standard SMTP
client through `asyncio.to_thread`; SMTP and network failures become explicit
`MailDeliveryUnavailable` failures. When no credential is configured,
`UnconfiguredMailDelivery` fails explicitly and never reports synthetic
success. Real Corpus verification and reset requests were accepted by Gmail
for `raghavdasila@highpolar.io`.
