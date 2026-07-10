# Medusa VPS Deployment For Corpus

> Historical deployment design. It has not been revalidated against the
> extracted RouteDeck Medusa fixture and its compose shape below predates the
> protected `examples/medusa-agent/infra/compose.yaml` stack. Do not execute it
> as a current runbook. Use `medusa-api-agent-test-guide.md` for the verified
> local acceptance path, and produce a reviewed VPS-specific compose before a
> future deployment.

This is the smallest practical path for running the Medusa fixture on our own
VPS so hosted Corpus can use it.

Target public URLs:

- Storefront: `https://medusa.test-targets.saastoagent.com`
- Backend/API: `https://medusa-backend.test-targets.saastoagent.com`
- Admin: `https://medusa-backend.test-targets.saastoagent.com/app`
- Store OpenAPI schema:
  `https://medusa-backend.test-targets.saastoagent.com/medusa_store.yaml`

Corpus needs only three public values:

- Medusa backend base URL:
  `https://medusa-backend.test-targets.saastoagent.com`
- Store OpenAPI schema URL:
  `https://medusa-backend.test-targets.saastoagent.com/medusa_store.yaml`
- Medusa publishable API key, sent as header `x-publishable-api-key`

Do not use `localhost` in Corpus. From hosted Corpus, `localhost` is the Corpus
server, not the VPS Medusa container.

## VPS Requirements

- Ubuntu VPS with Docker and Docker Compose
- DNS records for:
  - `medusa.test-targets.saastoagent.com`
  - `medusa-backend.test-targets.saastoagent.com`
- HTTPS reverse proxy, such as Caddy, Nginx, or Traefik
- Firewall open for `80` and `443`; keep Postgres and Redis private

The storefront is not required by Corpus, but this deployment hosts it too so
the full Medusa fixture is available.

## Files To Deploy

Copy the current Medusa target source from the sibling standalone RouteDeck
repository to the VPS:

```powershell
D:\Dev\AI Projects\routedeck\examples\medusa-agent\medusa
D:\Dev\AI Projects\routedeck\examples\medusa-agent\infra\medusa-setup.sh
```

Also copy the Store OpenAPI schema from:

```powershell
D:\Dev\AI Projects\saastoagent-v0.1\integration_prep\openapi_toolrouter\vendor\openapi_toolrouter_benchmark\artifacts\raw_openapi\medusa_store.yaml
```

Place it beside the compose file so the reverse proxy can serve it as a static
file, or serve it from any other stable public HTTPS URL.

The VPS layout should look like:

```text
/opt/medusa/
  docker-compose.yml
  medusa_store.yaml
  docker/
    medusa-image-setup.sh
  medusa-backend/
  medusa/
```

## Minimal Compose Shape

Create `/opt/medusa/docker-compose.yml` on the VPS. Replace passwords and
secrets.

```yaml
services:
  medusa-postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: medusa
      POSTGRES_PASSWORD: change-this-db-password
      POSTGRES_DB: medusa
    volumes:
      - medusa_postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U medusa -d medusa"]
      interval: 5s
      timeout: 5s
      retries: 30

  medusa-redis:
    image: redis:7-alpine
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 30

  medusa-setup:
    build:
      context: ./medusa-backend
    working_dir: /server
    environment:
      DATABASE_URL: postgres://medusa:change-this-db-password@medusa-postgres:5432/medusa
      REDIS_URL: redis://medusa-redis:6379
      JWT_SECRET: change-this-long-random-secret
      COOKIE_SECRET: change-this-long-random-secret
      STORE_CORS: https://medusa.test-targets.saastoagent.com,https://corpus.saastoagent.com
      ADMIN_CORS: https://medusa-backend.test-targets.saastoagent.com
      AUTH_CORS: https://medusa-backend.test-targets.saastoagent.com,https://medusa.test-targets.saastoagent.com,https://corpus.saastoagent.com
      MEDUSA_DISABLE_ADMIN: "false"
      MEDUSA_ADMIN_EMAIL: admin@example.com
      MEDUSA_ADMIN_PASSWORD: change-this-admin-password
      MEDUSA_SHARED_DIR: /shared
    volumes:
      - ./docker/medusa-image-setup.sh:/fixture/medusa-image-setup.sh:ro
      - medusa_shared:/shared
    depends_on:
      medusa-postgres:
        condition: service_healthy
      medusa-redis:
        condition: service_healthy
    command: ["sh", "/fixture/medusa-image-setup.sh"]

  medusa-backend:
    build:
      context: ./medusa-backend
    restart: unless-stopped
    working_dir: /server
    environment:
      NODE_ENV: production
      MEDUSA_APP_MODE: production
      MEDUSA_BACKEND_URL: https://medusa-backend.test-targets.saastoagent.com
      DATABASE_URL: postgres://medusa:change-this-db-password@medusa-postgres:5432/medusa
      REDIS_URL: redis://medusa-redis:6379
      JWT_SECRET: change-this-long-random-secret
      COOKIE_SECRET: change-this-long-random-secret
      STORE_CORS: https://medusa.test-targets.saastoagent.com,https://corpus.saastoagent.com
      ADMIN_CORS: https://medusa-backend.test-targets.saastoagent.com
      AUTH_CORS: https://medusa-backend.test-targets.saastoagent.com,https://medusa.test-targets.saastoagent.com,https://corpus.saastoagent.com
      MEDUSA_DISABLE_ADMIN: "false"
      MEDUSA_SEED_ON_START: "0"
    depends_on:
      medusa-postgres:
        condition: service_healthy
      medusa-redis:
        condition: service_healthy
      medusa-setup:
        condition: service_completed_successfully
    ports:
      - "127.0.0.1:9000:9000"
    healthcheck:
      test: ["CMD-SHELL", "node -e \"fetch('http://localhost:9000/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))\""]
      interval: 10s
      timeout: 5s
      retries: 30

  medusa-storefront:
    image: node:20-bookworm-slim
    restart: unless-stopped
    working_dir: /app/apps/storefront
    environment:
      NEXT_PUBLIC_MEDUSA_BACKEND_URL: https://medusa-backend.test-targets.saastoagent.com
      MEDUSA_BACKEND_INTERNAL_URL: http://medusa-backend:9000
      NEXT_PUBLIC_BASE_URL: https://medusa.test-targets.saastoagent.com
      NEXT_PUBLIC_DEFAULT_REGION: dk
      NODE_ENV: production
      MEDUSA_SHARED_DIR: /shared
    ports:
      - "127.0.0.1:8000:8000"
    volumes:
      - ./medusa:/app
      - medusa_storefront_node_modules:/app/apps/storefront/node_modules
      - medusa_storefront_next:/app/apps/storefront/.next
      - medusa_shared:/shared:ro
    depends_on:
      medusa-backend:
        condition: service_healthy
      medusa-setup:
        condition: service_completed_successfully
    command:
      - sh
      - -lc
      - |
        while [ ! -f /shared/storefront.env ]; do sleep 1; done
        set -a
        . /shared/storefront.env
        set +a
        npm install --no-audit --no-fund --legacy-peer-deps --workspaces=false
        npm run build
        npm run start

volumes:
  medusa_postgres:
  medusa_storefront_node_modules:
  medusa_storefront_next:
  medusa_shared:
```

Generate real secrets on the VPS:

```bash
openssl rand -base64 48
```

Start Medusa:

```bash
cd /opt/medusa
docker compose up -d --build
docker compose logs -f medusa-backend medusa-storefront
```

Check health from the VPS:

```bash
curl http://localhost:9000/health
curl http://localhost:8000
```

Then check public health:

```bash
curl https://medusa-backend.test-targets.saastoagent.com/health
curl https://medusa.test-targets.saastoagent.com
```

## Reverse Proxy

Example Caddy route:

```caddyfile
medusa-backend.test-targets.saastoagent.com {
  handle /medusa_store.yaml {
    root * /srv/medusa-public
    file_server
  }

  handle {
    reverse_proxy 127.0.0.1:9000
  }
}

medusa.test-targets.saastoagent.com {
  reverse_proxy 127.0.0.1:8000
}
```

Copy the OpenAPI schema into the static directory:

```bash
mkdir -p /srv/medusa-public
cp /opt/medusa/medusa_store.yaml /srv/medusa-public/medusa_store.yaml
```

The backend domain intentionally serves both admin/API and the static Store
OpenAPI schema:

```text
https://medusa-backend.test-targets.saastoagent.com/app
https://medusa-backend.test-targets.saastoagent.com/store
https://medusa-backend.test-targets.saastoagent.com/medusa_store.yaml
```

If the reverse proxy runs inside the same Docker network instead, proxy to the
service names:

```caddyfile
medusa-backend.test-targets.saastoagent.com {
  handle /medusa_store.yaml {
    root * /srv/medusa-public
    file_server
  }

  handle {
    reverse_proxy medusa-backend:9000
  }
}

medusa.test-targets.saastoagent.com {
  reverse_proxy medusa-storefront:8000
}
```

## Admin And Publishable Key

After the service is up:

1. Open `https://medusa-backend.test-targets.saastoagent.com/app`.
2. Create or log in as the admin user.
3. Confirm seeded demo products exist.
4. Copy a publishable API key from Medusa Admin.

If the seed creates the key but the admin UI does not show it clearly, read it
from the database inside the VPS:

```bash
docker compose exec medusa-postgres psql -U medusa -d medusa \
  -c "select token from api_key where type = 'publishable' order by created_at asc limit 1;"
```

Treat the key as an environment credential. Do not commit it to the repo.

## Corpus Setup

In hosted Corpus, create or edit the API connection with:

- Base URL: `https://medusa-backend.test-targets.saastoagent.com`
- OpenAPI URL:
  `https://medusa-backend.test-targets.saastoagent.com/medusa_store.yaml`
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
