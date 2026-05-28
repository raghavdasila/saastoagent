# Medusa VPS Deployment For Corpus

This is the smallest practical path for running the Medusa fixture on our own
VPS so hosted Corpus can use it.

Corpus needs only three public values:

- Medusa backend base URL, for example `https://medusa.example.com`
- Store OpenAPI schema URL, for example `https://medusa.example.com/medusa_store.yaml`
- Medusa publishable API key, sent as header `x-publishable-api-key`

Do not use `localhost` in Corpus. From hosted Corpus, `localhost` is the Corpus
server, not the VPS Medusa container.

## VPS Requirements

- Ubuntu VPS with Docker and Docker Compose
- DNS record for the Medusa backend, for example `medusa.example.com`
- HTTPS reverse proxy, such as Caddy, Nginx, or Traefik
- Firewall open for `80` and `443`; keep Postgres and Redis private

The storefront is optional for Corpus. The backend/admin service is required.

## Files To Deploy

Copy the current Medusa target source to the VPS:

```powershell
D:\Dev\AI Projects\agent-core\test_targets\medusa-backend
```

Also copy the Store OpenAPI schema from:

```powershell
D:\Dev\AI Projects\agent-core\agent-lab-powered-projects\saastoagent-v0.1\integration_prep\openapi_toolrouter\vendor\openapi_toolrouter_benchmark\artifacts\raw_openapi\medusa_store.yaml
```

Place it beside the compose file so the reverse proxy can serve it as a static
file, or serve it from any other stable public HTTPS URL.

## Minimal Compose Shape

Create `/opt/medusa/docker-compose.yml` on the VPS. Replace domains and secrets.

```yaml
services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: medusa
      POSTGRES_PASSWORD: change-this-db-password
      POSTGRES_DB: medusa
    volumes:
      - medusa_postgres:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  medusa:
    build:
      context: ./medusa-backend
    restart: unless-stopped
    environment:
      NODE_ENV: production
      MEDUSA_APP_MODE: production
      MEDUSA_BACKEND_URL: https://medusa.example.com
      DATABASE_URL: postgres://medusa:change-this-db-password@postgres:5432/medusa
      REDIS_URL: redis://redis:6379
      JWT_SECRET: change-this-long-random-secret
      COOKIE_SECRET: change-this-long-random-secret
      STORE_CORS: https://corpus.saastoagent.com
      ADMIN_CORS: https://medusa.example.com
      AUTH_CORS: https://medusa.example.com,https://corpus.saastoagent.com
      MEDUSA_DISABLE_ADMIN: "false"
      MEDUSA_SEED_ON_START: "1"
    depends_on:
      - postgres
      - redis
    expose:
      - "9000"

volumes:
  medusa_postgres:
```

Generate real secrets on the VPS:

```bash
openssl rand -base64 48
```

Start Medusa:

```bash
cd /opt/medusa
docker compose up -d --build
docker compose logs -f medusa
```

Check health from the VPS:

```bash
curl http://localhost:9000/health
```

Then check public health:

```bash
curl https://medusa.example.com/health
```

## Reverse Proxy

Example Caddy route:

```caddyfile
medusa.example.com {
  reverse_proxy medusa:9000

  handle /medusa_store.yaml {
    root * /srv/medusa-public
    file_server
  }
}
```

If Caddy runs outside the Docker network, proxy to `127.0.0.1:9000` and publish
the Medusa container port only on localhost:

```yaml
ports:
  - "127.0.0.1:9000:9000"
```

## Admin And Publishable Key

After the service is up:

1. Open `https://medusa.example.com/app`.
2. Create or log in as the admin user.
3. Confirm seeded demo products exist.
4. Copy a publishable API key from Medusa Admin.

If the seed creates the key but the admin UI does not show it clearly, read it
from the database inside the VPS:

```bash
docker compose exec postgres psql -U medusa -d medusa \
  -c "select token from api_key where type = 'publishable' order by created_at asc limit 1;"
```

Treat the key as an environment credential. Do not commit it to the repo.

## Corpus Setup

In hosted Corpus, create or edit the API connection with:

- Base URL: `https://medusa.example.com`
- OpenAPI URL: `https://medusa.example.com/medusa_store.yaml`
- Auth type: `api_key_header`
- Credential: the Medusa publishable API key
- Header name: `x-publishable-api-key`

Save and activate. Expected result: Corpus generates the Store API tools and the
connection reaches `1/1 ready`.

## Smoke Test

In the deployed public Corpus agent, test:

```text
what products do we have
i want to buy medusa tshirt
add the L size to cart
checkout
```

The public chat should not expose endpoint paths, operation IDs, trace IDs,
cart IDs, payment IDs, or raw Medusa internals.

## Operational Notes

- Keep Postgres and Redis off the public internet.
- Run backups for the `medusa_postgres` volume before upgrades.
- Set `MEDUSA_SEED_ON_START=0` after the first successful seed if repeat
  seeding causes duplicate fixture data.
- If Corpus activation fails, verify public `/health`, public
  `/medusa_store.yaml`, CORS values, and the publishable key header.
