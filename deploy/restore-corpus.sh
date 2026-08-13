#!/usr/bin/env bash
set -euo pipefail

object="${1:-}"
bucket_prefix="gs://saastoagent-corpus-backups-42047064897/"
[[ "$object" == "$bucket_prefix"* && "$object" == *.tar.gz ]] || {
    printf 'Supply an explicit Corpus backup object under %s\n' "$bucket_prefix" >&2
    exit 1
}

install -d -m 0750 /srv/corpus/backups
exec 9>/run/lock/corpus-backup.lock
flock -n 9 || { printf 'Another Corpus backup or restore is running.\n' >&2; exit 1; }

name="$(basename "$object")"
archive="/srv/corpus/backups/$name"
manifest="${archive}.sha256"
safety="/srv/corpus/backups/pre-restore-$(date -u +%Y%m%dT%H%M%SZ).tar.gz"
restore_timestamp="$(date -u +%Y%m%dT%H%M%SZ)"

gcloud storage cp "$object" "$archive"
gcloud storage cp "${object}.sha256" "$manifest"
(cd /srv/corpus/backups && sha256sum --check "$(basename "$manifest")")

systemctl stop corpus.service
tar --create --gzip --file "$safety" --directory /srv/corpus state data
mv /srv/corpus/state "/srv/corpus/state.pre-restore-$restore_timestamp"
mv /srv/corpus/data "/srv/corpus/data.pre-restore-$restore_timestamp"
tar --extract --gzip --file "$archive" --directory /srv/corpus
chown -R 10001:10001 /srv/corpus/state /srv/corpus/data
systemctl start corpus.service

for _ in $(seq 1 60); do
    curl --fail --silent --show-error http://127.0.0.1/readyz >/dev/null && break
    sleep 2
done
curl --fail --silent --show-error http://127.0.0.1/readyz >/dev/null
curl --fail --silent --show-error http://127.0.0.1/ >/dev/null
printf 'Corpus restore completed from %s. Pre-restore archive retained at %s\n' "$object" "$safety"
