# Corpus GCP Single-VM Deployment

Status: deployed for internal v0.1 testing on 2026-08-13

## Live boundary

- URL: `https://corpus.saastoagent.com`
- GCP project: `saastoagent`
- region/zone: `asia-south1` / `asia-south1-a`
- VM: `corpus-vm-1`, `n2-standard-2`, 160 GB `pd-balanced`
- static IP: `8.231.125.65` (`corpus-origin-ip`)
- VM identity: `corpus-vm@saastoagent.iam.gserviceaccount.com`
- public ports: 80 and 443 only; SSH is available only through IAP
- application services: Caddy web, one Uvicorn backend process, one Huey worker
- persistence: `/srv/corpus/state` and `/srv/corpus/data`
- deployment manager: `corpus.service`
- nightly archive: `corpus-backup.timer`

Cloudflare remains DNS-only. Caddy terminates TLS directly and renews the public
certificate. Cloudflare Full (strict) is relevant only if the record is later
proxied; it is not required for this deployment.

## Runtime providers

The primary runtime, evaluation models, and ToolRouter generation/review use an
explicit OpenAI provider with `gpt-5.6-luna` and low reasoning effort. Local
development retains the explicit Ollama default. Provider failures fail the
operation; there is no automatic provider fallback.

The VM receives the existing OpenAI and SMTP values from Secret Manager. The
six regional secrets are:

- `corpus-openai-api-key`
- `corpus-smtp-app-password`
- `corpus-routedeck-state-encryption-key`
- `corpus-credential-vault-key`
- `corpus-reset-secret`
- `corpus-verification-secret`

Values are written atomically to root-only `/run/corpus/runtime.env` at service
startup. No service-account JSON key is used.

## Provisioning sequence

From the repository root:

```powershell
.\deploy\fetch-secrets.ps1 -ProjectId saastoagent -EnvironmentFile .env.local
.\deploy\provision-gcp.ps1 -ProjectId saastoagent
```

The provisioning script is existence-checked and safe to rerun. It creates or
reuses the dedicated service account, Artifact Registry repository, private
versioned backup bucket, least-privilege bindings, daily disk snapshot policy,
firewall rules, reserved IP, and exactly one VM. Zone fallback changes only the
Mumbai zone when N2 capacity is unavailable; it never creates multiple VMs.

## Build and rollout

The Docker build context is `D:\Dev\AI Projects` because the approved image
closure consumes Corpus, RouteDeck, Agent Execution Runtime, and Agent Delivery
Runtime. RouteDeck is copied read-only into the image build; it is not modified.

```powershell
docker build -f saastoagent-v0.1/Dockerfile.production --target backend-runtime -t corpus-backend:production-test .
docker build -f saastoagent-v0.1/Dockerfile.production --target web-runtime -t corpus-web:production-test .
gcloud auth configure-docker asia-south1-docker.pkg.dev --quiet
```

Push commit- and timestamp-tagged images, resolve their registry digests, and
write only digest-qualified values to the ignored file
`.runtime/deployment/image-manifest.env`. Copy these files to
`/srv/corpus/deploy` through IAP:

- `compose.production.yaml`
- `deploy/Caddyfile`
- `deploy/fetch-runtime-secrets.sh`
- `deploy/corpus-prestart.sh`
- `deploy/corpus.service`
- `.runtime/deployment/image-manifest.env`

Then install the unit and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now corpus.service
```

The prestart gate rejects mutable image references, fetches secrets, pulls the
two digest-pinned images, and runs migrations exactly once before Compose.

## Operations

```bash
sudo systemctl status corpus.service
sudo journalctl -u corpus.service -n 200 --no-pager
sudo docker compose --env-file /srv/corpus/deploy/image-manifest.env \
  -f /srv/corpus/deploy/compose.production.yaml ps
curl -fsS https://corpus.saastoagent.com/readyz
```

Backend and worker publish no host ports. The worker intentionally has no HTTP
healthcheck; process exit is handled by Compose/systemd, and jobs expose their
durable state through Corpus.

## Backups and restore

The VM has a seven-day disk snapshot policy. The application backup timer stops
the stack, archives state and Source data without runtime secrets or Caddy
certificates, restarts and verifies readiness, then uploads to the private
bucket `gs://saastoagent-corpus-backups-42047064897`.

```bash
sudo systemctl enable --now corpus-backup.timer
sudo systemctl start corpus-backup.service
sudo /srv/corpus/deploy/backup-corpus.sh weekly
sudo /srv/corpus/deploy/restore-corpus.sh \
  gs://saastoagent-corpus-backups-42047064897/daily/<explicit-archive>.tar.gz
```

Restore requires an explicit object, verifies its SHA-256 manifest, and retains
both a pre-restore archive and the moved pre-restore directories.

## 2026-08-13 acceptance evidence

- DNS A record resolved to `8.231.125.65`.
- public TLS, SPA shell, `/healthz`, and `/readyz` returned successfully.
- production images passed `pip check`, backend imports, frontend build, and
  Caddy validation.
- 35 focused provider/deployment tests passed before image publication.
- the VM completed a real strict-schema OpenAI Responses call through Corpus's
  ToolRouter transport with `gpt-5.6-luna`.
- public browser signup completed for
  `info+corpus-smoke-20260813122921@saastoagent.com` with zero console errors.

