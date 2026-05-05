# Docker Compose Service Rename And Port Rebind

Date: 2026-05-05

## Claim

When a Docker Compose service is renamed, an orphaned container from the old service name can continue holding the published host port.

## Evidence

- Local service rename from `frontend-v3` to `frontend`
- Compose warning reported orphan container `saastoagent-v01-frontend-v3-1`
- New frontend start failed with `Bind for 0.0.0.0:3005 failed: port is already allocated`
- `docker compose up -d --remove-orphans` removed the old container
- `docker compose up -d --force-recreate frontend` restored the expected `3005 -> 3000` mapping

## Reusable Pattern

1. After renaming a service, run `docker compose up -d --remove-orphans`.
2. If the first start failed while binding a published port, recreate the renamed service with `docker compose up -d --force-recreate <service>`.
3. Verify with `docker compose ps` and a direct HTTP check.

## Applies To

- Local runtime renames
- Compose-based developer workflows with published ports
