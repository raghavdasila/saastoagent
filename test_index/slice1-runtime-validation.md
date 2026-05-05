# Slice 1 Runtime Validation

Date: 2026-05-05

## Scope

Manual runtime validation for the implemented Slice 1 workspace shell.

## Commands Run

```bash
docker compose up -d --build
docker compose up -d --remove-orphans
docker compose up -d --force-recreate frontend
```

```powershell
(Invoke-WebRequest 'http://localhost:8085/api/health' -UseBasicParsing).Content
(Invoke-WebRequest 'http://localhost:3005' -UseBasicParsing).StatusCode
```

## What This Validated

- Postgres is healthy on `5435`
- Backend is reachable on `8085`
- `/api/health` returns `{"status":"ok"}`
- Frontend is reachable on `3005` and returns HTTP `200`
- The renamed `frontend` service works after orphan cleanup and recreate

## Gaps

- No automated backend test suite yet
- No frontend unit or integration tests yet
- No end-to-end auth or workspace flow automation yet

## Notes

- The first start failed because orphan container `saastoagent-v01-frontend-v3-1` was still bound to `3005`.
- Successful recovery required orphan cleanup and frontend recreate.
