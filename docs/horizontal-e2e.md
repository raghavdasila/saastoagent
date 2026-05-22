# SaaStoAgent v0.1 Horizontal E2E

This is the repeatable Docker UI harness for the horizontal sandbox slice.
Backend-only tests are not sufficient evidence for end-to-end claims on this
slice.

## Ports

- Frontend: `http://localhost:3007`
- Backend: `http://localhost:8085`
- Postgres: Docker-internal only
- Mock Storefront/Admin fixture: host port `9109`
- Backend-to-fixture URL from Docker: `http://host.docker.internal:9109`

## Command

Run Docker first:

```bash
docker compose up -d --build backend frontend
```

Then run the UI harness from `frontend`:

```bash
npm run e2e:docker
```

The harness starts `frontend/scripts/mock-storefront-api.mjs` on port `9109`
when a compatible fixture is not already running.

## Covered Flow

The harness proves:

- UI signup.
- UI SaaSAgent creation.
- Corpus intent opens the connection setup surface.
- UI connection activation against deterministic Storefront OpenAPI.
- Deployment enablement.
- Public `/a/:slug` chat read execution.
- Public rendered chat has no router/tool/path/score/trace leaks.
- UI activation of deterministic Admin OpenAPI.
- Public write request creates pending owner approval instead of executing.
- Builder owner approval executes the Admin fixture exactly once.
- Builder owner cancel does not call the Admin fixture.

## Evidence

By default screenshots are written outside source under:

```text
%TEMP%/saastoagent-ui-e2e-<timestamp>
```

Override with:

```bash
SAASTOAGENT_E2E_ARTIFACT_DIR=/path/outside/source npm run e2e:docker
```

The command prints compact JSON with account, slug, fixture URL, artifact path,
and screenshot paths.

## Known Limits

- Slack is intentionally out of scope for this pass.
- The fixture names are acceptance data only; product runtime stays OpenAPI
  driven.
- The deployed chat does not yet live-push owner approval results to an already
  open visitor browser. The approval result is persisted to the visitor session
  and the fixture execution is verified by the harness.
- The command assumes Docker Desktop-style `host.docker.internal` reachability
  from the backend container.
