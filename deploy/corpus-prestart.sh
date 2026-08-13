#!/usr/bin/env bash
set -euo pipefail

deploy_root="/srv/corpus/deploy"
manifest="$deploy_root/image-manifest.env"
compose_file="$deploy_root/compose.production.yaml"

for required in "$manifest" "$compose_file" "$deploy_root/fetch-runtime-secrets.sh"; do
    [[ -f "$required" ]] || { printf 'Missing deployment file: %s\n' "$required" >&2; exit 1; }
done

backend_image="$(sed -n 's/^CORPUS_BACKEND_IMAGE=//p' "$manifest")"
web_image="$(sed -n 's/^CORPUS_WEB_IMAGE=//p' "$manifest")"
[[ "$backend_image" =~ @sha256:[0-9a-f]{64}$ ]] || { printf 'Backend image is not digest-pinned.\n' >&2; exit 1; }
[[ "$web_image" =~ @sha256:[0-9a-f]{64}$ ]] || { printf 'Web image is not digest-pinned.\n' >&2; exit 1; }

"$deploy_root/fetch-runtime-secrets.sh"
docker compose --env-file "$manifest" -f "$compose_file" pull
docker compose --env-file "$manifest" -f "$compose_file" run --rm --no-deps backend python -m corpus.persistence.migrations

