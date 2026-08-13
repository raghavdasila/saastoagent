#!/usr/bin/env bash
set -euo pipefail

bucket="gs://saastoagent-corpus-backups-42047064897"
kind="${1:-daily}"
[[ "$kind" == "daily" || "$kind" == "weekly" ]] || { printf 'Backup kind must be daily or weekly.\n' >&2; exit 1; }

install -d -m 0750 /srv/corpus/backups
exec 9>/run/lock/corpus-backup.lock
flock -n 9 || { printf 'Another Corpus backup is running.\n' >&2; exit 1; }

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive="/srv/corpus/backups/corpus-${timestamp}.tar.gz"
manifest="${archive}.sha256"
restart_required=0

restore_service() {
    if [[ "$restart_required" -eq 1 ]]; then
        systemctl start corpus.service || true
    fi
}
trap restore_service EXIT

systemctl stop corpus.service
restart_required=1
tar --create --gzip --file "$archive" --directory /srv/corpus state data
sha256sum "$archive" > "$manifest"

systemctl start corpus.service
restart_required=0
for _ in $(seq 1 60); do
    curl --fail --silent --show-error http://127.0.0.1/readyz >/dev/null && break
    sleep 2
done
curl --fail --silent --show-error http://127.0.0.1/readyz >/dev/null

gcloud storage cp "$archive" "$manifest" "$bucket/$kind/"
rm -f "$archive" "$manifest"
printf 'Corpus %s backup completed and uploaded: %s\n' "$kind" "$timestamp"

