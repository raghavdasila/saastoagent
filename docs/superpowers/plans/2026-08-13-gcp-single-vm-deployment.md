# Corpus GCP Single-VM Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy Corpus v0.1 for internal use at `https://corpus.saastoagent.com` on one Google Compute Engine `n2-standard-2` VM in Mumbai, preserving the locally accepted product behavior and providing a documented resize, backup, rollback, and recovery path.

**Architecture:** One Ubuntu 24.04 VM runs a Caddy web container, one Corpus backend container, and one single-process Huey worker. A 160 GB balanced persistent boot disk holds Docker and `/srv/corpus`; Google Secret Manager supplies stable runtime secrets; Artifact Registry holds immutable images; Cloud Storage and scheduled disk snapshots provide recovery. Only ports 80 and 443 are public. Administrative SSH uses OS Login through IAP. OpenAI and Gmail SMTP remain the existing external providers.

**Tech Stack:** Google Compute Engine, `gcloud`, Artifact Registry, Secret Manager, Cloud Storage, Docker Engine with Compose v2, Caddy, FastAPI/Uvicorn, React/Vite, Huey, SQLite, OpenAI API, Gmail SMTP.

## Global Constraints

- Authoritative repository: `D:\Dev\AI Projects\saastoagent-v0.1`.
- RouteDeck remains the sibling dependency at `D:\Dev\AI Projects\routedeck`; deployment work does not authorize unrelated RouteDeck edits.
- VM: `n2-standard-2`, 2 vCPU, 8 GB RAM, Ubuntu 24.04 LTS, 160 GB `pd-balanced`, project `saastoagent`, region `asia-south1`.
- Public URL: `https://corpus.saastoagent.com`; Cloudflare DNS remains user-owned.
- Signup remains open; do not add an email allowlist.
- Keep the existing OpenAI key and `no-reply@saastoagent.com` SMTP identity.
- Never print, commit, copy into an image, or place in VM metadata any OpenAI, SMTP, RouteDeck, credential-vault, reset, or verification secret.
- Keep one backend process and one Huey worker process with worker concurrency one.
- Use OpenAI for Corpus primary and evaluation model work. Do not run Ollama on this VM and do not fall back to another provider.
- Preserve SQLite and filesystem persistence for v0.1; horizontal replicas are out of scope.
- Git authorization covers deployment files/documentation and committing earlier repository changes. Do not push unless the user explicitly authorizes a push.
- Production deployment is performed without Git on the VM: the VM pulls immutable images from Artifact Registry.
- No Cloud SQL, Redis, Kubernetes, load balancer, Cloud Run, or new email provider.
- Cloudflare remains DNS-only for v0.1. Caddy terminates public HTTPS directly on the VM. Cloudflare proxying, WAF, and Full (strict) mode are deferred and are not deployment requirements.

---

## File Structure And Ownership

- Create `Dockerfile.production`: immutable backend, worker-compatible backend, frontend build, and Caddy web targets; no reload server or source bind mounts.
- Create `compose.production.yaml`: production service topology, internal-only backend, persistent `/srv/corpus` mounts, health checks, restart policy, and memory-aware service limits.
- Create `deploy/Caddyfile`: HTTPS origin routing, SPA fallback, backend health/API proxying, upload limit, compression, and security headers.
- Create `deploy/corpus.service`: systemd owner for the production Compose project.
- Create `deploy/fetch-secrets.ps1`: operator-side secret ingestion from existing local values into Secret Manager without echoing values.
- Create `deploy/fetch-runtime-secrets.sh`: VM-side least-privilege retrieval into root-only `/run/corpus/runtime.env`.
- Create `deploy/provision-gcp.ps1`: idempotent GCP API, service-account, IP, firewall, registry, bucket, snapshot policy, and VM provisioning.
- Create `deploy/install-vm.sh`: VM bootstrap for Docker, Google Cloud CLI, directories, systemd, and deployment scripts.
- Create `deploy/deploy.ps1`: build, test, image push, remote rollout, health verification, and previous-image rollback metadata.
- Create `deploy/backup-corpus.sh`: short maintenance-window application archive plus Cloud Storage upload; never copies secret material into the archive.
- Create `deploy/restore-corpus.sh`: explicit stopped-service restore with pre-restore safety copy and post-restore readiness verification.
- Create `deploy/verify-production.ps1`: public and remote smoke checks with no secret output.
- Create `docs/deployment/gcp-single-vm.md`: exact operator runbook, DNS handoff, secrets, deploy, backup, restore, resize, monitoring, rollback, and cost/resource inventory.
- Modify `.env.example`: document production values without secrets.
- Modify `.gitignore`: exclude deployment-generated environment, address, manifest, and secret staging files.
- Modify `architecture/code-map.md`, `SYSTEM_FLOW_INDEX.md`, `test_index/README.md`, and `context.md` only where deployment ownership, runtime flow, executable validation, or restart state actually changes.

---

### Task 1: Establish The Deployment Baseline And Commit Boundary

**Files:**
- Read: `context.md`
- Read: `context_checkpoints/2026-08-13-ecommerce-three-mode-acceptance.md`
- Read: `Dockerfile`
- Read: `compose.yaml`
- Read: `.env.local`
- Read: `backend/pyproject.toml`
- Read: `frontend/package.json`
- Create: `artifacts/deployment/gcp-preflight.json` only if `artifacts/` policy permits committed sanitized evidence; otherwise retain the command results in the deployment runbook

**Interfaces:**
- Consumes: accepted local ecommerce baseline and current environment configuration.
- Produces: sanitized baseline record, exact local dependency paths, active model name, and a clean Git boundary for deployment work.

- [ ] **Step 1: Verify repository and dependency state without mutating Git**

Run:

```powershell
git status --short
git branch --show-current
git rev-parse HEAD
Test-Path 'D:\Dev\AI Projects\routedeck'
Test-Path 'D:\Dev\AI Projects\agent-execution-runtime'
Test-Path 'D:\Dev\AI Projects\agent-delivery-runtime'
```

Expected: branch `main`; all three sibling paths exist. Record any pre-existing changes before touching them. Never discard them.

- [ ] **Step 2: Check required local values by name only**

Run a PowerShell check that reports `present` or `missing` for `OPENAI_API_KEY`, `CORPUS_SMTP_APP_PASSWORD`, `CORPUS_OPENAI_MODEL`, and the four persistent Corpus/RouteDeck secrets without printing values.

Expected: OpenAI key, SMTP password, and OpenAI model are present. Existing local persistent secrets may be imported; missing persistent secrets are generated once with cryptographically secure randomness.

- [ ] **Step 3: Run the proportionate local baseline**

Run:

```powershell
docker compose config --quiet
pnpm --dir frontend typecheck
pnpm --dir frontend build
.\.venv\Scripts\python.exe -m pytest backend\tests\runtime backend\tests\infrastructure backend\tests\persistence -q
```

Expected: all commands pass. A failure blocks packaging and is fixed in its owning module, not bypassed in deployment scripts.

- [ ] **Step 4: Handle earlier repository changes under the explicit authorization**

If Step 1 found pre-existing changes, review their full diff, run their owning tests, stage only verified files, and create a separate descriptive commit before deployment changes. If the worktree is clean, record `No earlier uncommitted changes found` and do not create an empty commit.

---

### Task 2: Reserve The Public IP And Trigger The Early Cloudflare Handoff

**Files:**
- Create: `.runtime/deployment/corpus-origin-ip.txt` (ignored)
- Update during execution: `docs/deployment/gcp-single-vm.md`

**Interfaces:**
- Consumes: GCP project `saastoagent`, region `asia-south1`.
- Produces: static regional IPv4 address `corpus-origin-ip` and the exact user-owned Cloudflare record.

- [ ] **Step 1: Reconfirm account, project, billing, zones, and quota read-only**

Run:

```powershell
gcloud config get-value project
gcloud auth list --filter=status:ACTIVE --format='value(account)'
gcloud billing projects describe saastoagent --format='value(billingEnabled)'
gcloud compute zones list --project=saastoagent --filter='region:(asia-south1)' --format='table(name,status)'
gcloud compute regions describe asia-south1 --project=saastoagent --format=json
```

Expected: project `saastoagent`, billing enabled, at least one zone `UP`, and quota for two N2 vCPUs plus one external IPv4. Corpus uses one VM in one zone. Listing all Mumbai zones only identifies an in-region allocation fallback if the preferred zone has no N2 capacity.

- [ ] **Step 2: Enable only the required GCP APIs**

Run:

```powershell
gcloud services enable compute.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com storage.googleapis.com logging.googleapis.com monitoring.googleapis.com oslogin.googleapis.com iap.googleapis.com --project=saastoagent
```

Expected: each required API is enabled. Do not enable GKE, Cloud SQL, Memorystore, or Cloud Run.

- [ ] **Step 3: Reserve the regional external IPv4 idempotently**

Run an existence check, then create only when absent:

```powershell
gcloud compute addresses describe corpus-origin-ip --region=asia-south1 --project=saastoagent --format='value(address)'
gcloud compute addresses create corpus-origin-ip --region=asia-south1 --network-tier=PREMIUM --project=saastoagent
```

Expected: one stable IPv4. Save it to ignored `.runtime/deployment/corpus-origin-ip.txt` without adding other state.

- [ ] **Step 4: Immediately send the user the Cloudflare action**

Provide exactly:

```text
Type: A
Name: corpus
IPv4 address: use the exact value returned by `gcloud compute addresses describe corpus-origin-ip --region=asia-south1 --project=saastoagent --format='value(address)'`
Proxy status: DNS only
TTL: Auto
```

Ask the user to add it immediately. Do not wait for propagation; continue Tasks 3-8. TLS verification waits at Task 9.

- [ ] **Step 5: Verify propagation opportunistically without blocking**

Run periodically at natural task boundaries, never in a tight loop:

```powershell
Resolve-DnsName corpus.saastoagent.com -Type A
```

Expected eventually: the reserved IPv4. Do not change Cloudflare through automation.

---

### Task 3: Build Production Containers And Reverse Proxy

**Files:**
- Create: `Dockerfile.production`
- Create: `compose.production.yaml`
- Create: `deploy/Caddyfile`
- Modify: `.dockerignore`
- Modify: `.env.example`
- Test: `backend/tests/runtime/test_production_configuration.py`
- Test: `frontend/src/tests/production-routing.test.ts` only if routing logic is moved into testable frontend code; otherwise validate through the Caddy container smoke

**Interfaces:**
- Consumes: sibling RouteDeck, Agent Execution Runtime, and Agent Delivery Runtime sources during the controlled image build.
- Produces: `corpus-backend:<git-sha>` and `corpus-web:<git-sha>` images; backend image also runs the Huey worker command.

- [ ] **Step 1: Add failing production-configuration tests**

Tests must parse `compose.production.yaml` and assert:

```python
assert services == {"web", "backend", "worker"}
assert "--reload" not in backend_command
assert backend_has_no_host_port
assert worker_count == 1
assert all(service["restart"] == "unless-stopped" for service in services.values())
assert "/srv/corpus/state" in declared_mounts
assert "/srv/corpus/data" in declared_mounts
assert no_service_uses_env_file_dot_env_local
```

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests\runtime\test_production_configuration.py -q
```

Expected: FAIL because production files do not exist.

- [ ] **Step 2: Implement the immutable production Docker targets**

`Dockerfile.production` must:

- pin the existing Python, Node, pnpm, Torch, Corpus, RouteDeck, Agent Execution Runtime, and Agent Delivery Runtime versions;
- install backend production dependencies without the testing extra in the final runtime layer;
- cache the exact MiniLM model already pinned by Corpus;
- compile frontend assets with Vite;
- copy only runtime code and built assets into final images;
- run as a non-root application user where application filesystem permissions allow it;
- contain no `.env.local`, Git metadata, test artifacts, runtime databases, or source bind mounts.

- [ ] **Step 3: Implement the production Compose topology**

Use these service contracts:

```yaml
services:
  web:
    image: ${CORPUS_WEB_IMAGE}
    ports: ["80:80", "443:443"]
  backend:
    image: ${CORPUS_BACKEND_IMAGE}
    command: ["python", "-m", "uvicorn", "corpus.main:create_live_app", "--factory", "--host", "0.0.0.0", "--port", "8099", "--workers", "1"]
  worker:
    image: ${CORPUS_BACKEND_IMAGE}
    command: ["python", "-m", "huey.bin.huey_consumer", "corpus.app.worker.huey", "--workers", "1"]
```

> Historical plan snapshot: ADR-005 supersedes the worker module shown above.
> Current Compose and runbooks use `corpus.app.worker.huey`; do not copy the
> earlier feature-owned command.

Both backend and worker mount the same `/srv/corpus/state` and `/srv/corpus/data`. Only `web` publishes host ports. The Compose project consumes `/run/corpus/runtime.env` and an ignored image-manifest file.

- [ ] **Step 4: Implement Caddy routing and headers**

`deploy/Caddyfile` must:

- serve `corpus.saastoagent.com`;
- reverse proxy `/api/*`, `/healthz`, and `/readyz` to `backend:8099`;
- serve compiled assets and use `try_files {path} /index.html` for the application shell;
- preserve host and forwarding headers;
- enable gzip/zstd;
- apply `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-Frame-Options: DENY`, and a tested Content Security Policy compatible with the application;
- cap request bodies at 20 MiB, matching the current Source upload limit.

- [ ] **Step 5: Build and test locally**

Run:

```powershell
docker build -f Dockerfile.production --target backend-runtime -t corpus-backend:production-test ..
docker build -f Dockerfile.production --target web-runtime -t corpus-web:production-test ..
docker compose -f compose.production.yaml config --quiet
.\.venv\Scripts\python.exe -m pytest backend\tests\runtime\test_production_configuration.py -q
```

Start the production stack with disposable local paths and non-production generated secrets, then verify `/`, `/healthz`, `/readyz`, SPA fallback, and that `8099` is not host-published. Do not reuse or overwrite `.runtime` accepted evidence.

---

### Task 4: Implement Stable Secret Delivery

**Files:**
- Create: `deploy/fetch-secrets.ps1`
- Create: `deploy/fetch-runtime-secrets.sh`
- Modify: `.gitignore`
- Test: `backend/tests/runtime/test_deployment_secret_contract.py`

**Interfaces:**
- Consumes: existing local OpenAI key and SMTP password plus four existing-or-new persistent application secrets.
- Produces: six Secret Manager secrets and root-only `/run/corpus/runtime.env` on the VM.

- [ ] **Step 1: Define the exact secret inventory**

Use these Secret Manager names:

```text
corpus-openai-api-key
corpus-smtp-app-password
corpus-routedeck-state-encryption-key
corpus-credential-vault-key
corpus-reset-secret
corpus-verification-secret
```

The first two retain their existing values. The remaining four retain existing values when present; generate them once only when absent. Do not use the development entrypoint's automatic secret generation in production.

- [ ] **Step 2: Write tests for secret-name completeness and output safety**

Tests assert the operator script contains all six names, never uses `Write-Output` or `echo` on secret values, and writes only ignored staging files with restrictive permissions.

- [ ] **Step 3: Implement operator-side ingestion**

`deploy/fetch-secrets.ps1` reads `.env.local` locally, reports only `present`, `created`, or `new version added`, pipes values to `gcloud secrets versions add --data-file=-`, and removes temporary files in `finally`. It must fail when OpenAI or SMTP values are absent instead of prompting through chat or inventing replacements.

- [ ] **Step 4: Implement VM-side retrieval**

`deploy/fetch-runtime-secrets.sh` uses the attached service account through `gcloud secrets versions access latest`, sets `umask 077`, writes `/run/corpus/runtime.env.tmp`, validates all required names are non-empty, then atomically renames it to `/run/corpus/runtime.env`. It never logs values.

- [ ] **Step 5: Verify without exposing values**

Run tests and a dry run that reports only the number of retrieved variables and file mode `0600`. Search logs and generated configuration for `sk-`, SMTP password fragments, and secret values using an in-memory comparison that prints only offending file names.

---

### Task 5: Provision Least-Privilege GCP Infrastructure

**Files:**
- Create: `deploy/provision-gcp.ps1`
- Create: `deploy/install-vm.sh`
- Create: `deploy/corpus.service`
- Test: `backend/tests/runtime/test_gcp_provisioning_contract.py`

**Interfaces:**
- Consumes: static IP from Task 2 and image/secrets contracts from Tasks 3-4.
- Produces: service account, Artifact Registry repository, backup bucket, firewall rules, snapshot policy, and stopped/bootstrapped VM.

- [ ] **Step 1: Add failing provisioning-contract tests**

Tests inspect scripts and assert:

- project is always explicitly `saastoagent`;
- VM type is exactly `n2-standard-2`;
- disk is exactly 160 GB `pd-balanced`;
- no default service account is used;
- no service-account key file is created;
- firewall exposes only 80/443 publicly and SSH only from IAP `35.235.240.0/20`;
- Shielded VM, OS Login, and deletion protection are enabled;
- VM metadata contains no application secret;
- every create operation is preceded by an existence check.

- [ ] **Step 2: Create the dedicated service account and IAM bindings**

Create `corpus-vm@saastoagent.iam.gserviceaccount.com` with only:

```text
roles/artifactregistry.reader on the corpus Artifact Registry repository
roles/secretmanager.secretAccessor on the six Corpus secrets
roles/storage.objectCreator and roles/storage.objectViewer on the Corpus backup bucket
roles/logging.logWriter on the project
roles/monitoring.metricWriter on the project
```

Do not grant Owner, Editor, Compute Admin, Service Account User, or project-wide Storage Admin to the VM identity.

- [ ] **Step 3: Create registry, bucket, and backup policies**

Create:

- Docker repository `corpus` in `asia-south1` with immutable deployment tags/digests;
- globally unique private bucket `saastoagent-corpus-backups-42047064897` in `asia-south1`, uniform bucket-level access, public-access prevention, object versioning, and lifecycle retention suitable for seven daily plus four weekly archives;
- daily disk snapshot schedule with seven retained snapshots.

Keep application archives secret-free; the keys stay solely in Secret Manager.

- [ ] **Step 4: Create firewall rules**

Create target-tagged rules:

```text
corpus-web: tcp:80,tcp:443 from 0.0.0.0/0 and ::/0
corpus-iap-ssh: tcp:22 from 35.235.240.0/20
```

No rule exposes ports 8099, 5199, 8771, 8782, 11434, Docker, SQLite, or Huey.

- [ ] **Step 5: Create the VM**

Choose the first `UP` zone in `asia-south1` with N2 capacity, preferring `asia-south1-a`, then `b`, then `c`. Attach:

- the reserved `corpus-origin-ip`;
- dedicated VM service account with `cloud-platform` scope controlled by IAM;
- Ubuntu 24.04 LTS;
- 160 GB balanced persistent boot disk;
- Shielded Secure Boot, vTPM, integrity monitoring;
- OS Login and block project-wide SSH keys;
- deletion protection;
- tags `corpus-web,corpus-iap-ssh`.

If the preferred zone reports capacity unavailable, retry the next `UP` Mumbai zone. Do not change machine family or region silently.

- [ ] **Step 6: Bootstrap the VM**

Through IAP, run `deploy/install-vm.sh` to install Docker Engine, Compose v2, Google Cloud CLI, Ops Agent, Caddy data directories, `/srv/corpus/{state,data,deploy,backups}`, `/run/corpus`, and the systemd unit. Enable unattended security upgrades. Do not clone repositories or store Git credentials on the VM.

- [ ] **Step 7: Verify infrastructure before application rollout**

Verify the VM identity, IP, disk, service account, firewall effective rules, OS Login/IAP access, Docker versions, directories, and absence of public response on `8099`.

---

### Task 6: Publish Immutable Images And Record Provenance

**Files:**
- Create: `deploy/deploy.ps1`
- Generated ignored: `.runtime/deployment/image-manifest.env`
- Update: `docs/deployment/gcp-single-vm.md`

**Interfaces:**
- Consumes: production images and Artifact Registry from prior tasks.
- Produces: digest-pinned backend and web images plus a sanitized deployment manifest.

- [ ] **Step 1: Authenticate Docker with short-lived gcloud credentials**

Run:

```powershell
gcloud auth configure-docker asia-south1-docker.pkg.dev --quiet
```

Do not create or download a service-account JSON key.

- [ ] **Step 2: Build images from the exact multi-repository context**

Use the parent `D:\Dev\AI Projects` build context because the approved Docker boundary consumes `routedeck`, `agent-execution-runtime`, `agent-delivery-runtime`, and `saastoagent-v0.1`. Tag both images with the Corpus Git SHA and a deployment timestamp. Record the Git SHAs or content hashes of all four inputs in a sanitized manifest.

- [ ] **Step 3: Run image-level gates before pushing**

Run backend import/version assertions, frontend static serving smoke, `pip check`, Compose config validation, production configuration tests, and the focused runtime/infrastructure/persistence tests.

- [ ] **Step 4: Push and resolve immutable digests**

Push both images, query Artifact Registry for their `sha256:` digests, and write only the digest-qualified image URLs to `.runtime/deployment/image-manifest.env`.

- [ ] **Step 5: Reject mutable rollout inputs**

The remote deployment must fail unless both `CORPUS_BACKEND_IMAGE` and `CORPUS_WEB_IMAGE` contain `@sha256:`. Do not deploy `latest`.

---

### Task 7: Configure Production Runtime And Backups

**Files:**
- Create: `deploy/backup-corpus.sh`
- Create: `deploy/restore-corpus.sh`
- Modify: `deploy/corpus.service`
- Update: `docs/deployment/gcp-single-vm.md`

**Interfaces:**
- Consumes: VM filesystem, Secret Manager values, image manifest, Compose definition.
- Produces: stable runtime environment, systemd-managed stack, daily archive timer, and tested restore command.

- [ ] **Step 1: Write the non-secret runtime configuration**

Set exactly:

```text
CORPUS_MODEL_PROVIDER=openai
CORPUS_OPENAI_MODEL=<existing configured model>
CORPUS_OPENAI_REASONING_EFFORT=low
CORPUS_PUBLIC_FRONTEND_URL=https://corpus.saastoagent.com
ROUTEDECK_BROWSER_ORIGINS=https://corpus.saastoagent.com
CORPUS_TRUSTED_PROXIES=<Docker network proxy address/range verified at runtime>
ROUTEDECK_WORKER_COUNT=1
CORPUS_DATABASE_URL=sqlite+aiosqlite:////srv/corpus/state/corpus.sqlite3
ROUTEDECK_DATABASE_URL=sqlite+pysqlite:////srv/corpus/state/routedeck.sqlite
CORPUS_JOB_QUEUE_PATH=/srv/corpus/state/corpus-jobs.sqlite3
CORPUS_SOURCE_DATA_ROOT=/srv/corpus/data/sources
CORPUS_API_SOURCE_MAX_UPLOAD_BYTES=20971520
CORPUS_MIGRATION_REVISION=0019_builder_assembly_lifecycle
CORPUS_SMTP_USERNAME=no-reply@saastoagent.com
CORPUS_SMTP_FROM_ADDRESS=no-reply@saastoagent.com
```

ToolRouter generation/reviewer settings must use the configured OpenAI-compatible production path if supported by current code. If the current ToolRouter snapshot still requires Ollama, stop and report that exact dependency; do not deploy a hidden provider fallback or claim full Source/evaluation readiness.

- [ ] **Step 2: Bind systemd startup ordering**

`corpus.service` runs the secret fetch first, validates image digests and required directories, executes migrations exactly once through the backend image, then starts Compose. Backend and worker startup do not each regenerate secrets or independently race migrations.

- [ ] **Step 3: Implement application-consistent nightly archives**

At the scheduled maintenance time:

1. acquire `/run/lock/corpus-backup.lock`;
2. stop web writes, worker, then backend with bounded timeout;
3. archive `/srv/corpus/state` and `/srv/corpus/data` excluding Caddy certificates, runtime secrets, temporary files, and logs;
4. calculate SHA-256 and write a sanitized manifest;
5. restart backend, worker, and web;
6. require `/readyz` success;
7. upload archive and manifest to the private bucket;
8. delete only the local archive after confirmed upload.

If shutdown, archive, restart, readiness, or upload fails, retain the local archive/error and emit a failed systemd unit status. Never label a partial backup successful.

- [ ] **Step 4: Implement guarded restore**

Restore requires an explicit object name, downloads and verifies its SHA-256, stops services, makes a local pre-restore safety archive, replaces only `/srv/corpus/state` and `/srv/corpus/data`, preserves secrets/Caddy state, restarts, and verifies `/readyz` plus the frontend. On failure it stops and reports; it does not silently roll forward.

- [ ] **Step 5: Test backup and restore before user onboarding**

Create disposable state, run backup, mutate the disposable state, restore it, and verify exact hashes. Then take the first real pre-launch archive and verify it is private in Cloud Storage.

---

### Task 8: Deploy The Application While DNS Propagates

**Files:**
- Modify remotely: `/srv/corpus/deploy/compose.production.yaml`
- Modify remotely: `/srv/corpus/deploy/Caddyfile`
- Modify remotely: `/srv/corpus/deploy/image-manifest.env`
- Modify remotely: `/etc/systemd/system/corpus.service`
- Generated remotely: `/run/corpus/runtime.env`

**Interfaces:**
- Consumes: digest-pinned images, VM, secrets, production configuration.
- Produces: origin application ready by static IP and local Host-header checks, pending public DNS/TLS completion.

- [ ] **Step 1: Copy only deployment artifacts through IAP**

Transfer production Compose, Caddyfile, systemd unit, image manifest, backup/restore scripts, and VM secret-fetch script. Do not copy the repository, `.git`, `.env.local`, accepted evidence, or local runtime data.

- [ ] **Step 2: Fetch runtime secrets and validate names only**

Run the VM secret fetch, verify file owner `root:root`, mode `0600`, six secret variables present, and no secret values in journald.

- [ ] **Step 3: Pull images and run the one-time migration gate**

Pull digest-qualified images, run `corpus.persistence.migrations` once, then verify the configured Alembic revision and tables before starting services.

- [ ] **Step 4: Start through systemd**

Run:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now corpus.service
sudo systemctl status corpus.service --no-pager
```

Expected: backend healthy, worker running one process, web running. No public backend port exists.

- [ ] **Step 5: Verify origin before DNS/TLS**

From the VM, call backend health/readiness directly on the Compose network. From the operator machine, call the origin IP with the correct Host header over HTTP and verify the Caddy redirect/configuration path without weakening TLS or adding a temporary insecure public application port.

---

### Task 9: Complete DNS And Direct Origin TLS

**Files:**
- Update: `docs/deployment/gcp-single-vm.md`
- Generated sanitized evidence: `artifacts/deployment/<timestamp>/public-smoke.json`

**Interfaces:**
- Consumes: user-created Cloudflare DNS-only A record and running origin.
- Produces: valid public HTTPS endpoint at `corpus.saastoagent.com`.

- [ ] **Step 1: Confirm DNS points only to the reserved IP**

Run:

```powershell
Resolve-DnsName corpus.saastoagent.com -Type A
```

Expected: the exact `corpus-origin-ip`. If it differs, stop and ask the user to correct Cloudflare.

- [ ] **Step 2: Verify Caddy certificate issuance**

Inspect Caddy status and certificate logs without printing unrelated environment values. Confirm HTTPS returns a valid certificate for `corpus.saastoagent.com` and HTTP redirects to HTTPS.

- [ ] **Step 3: Keep the Cloudflare record DNS-only**

Confirm the record remains:

```text
Proxy status: DNS only
TTL: Auto
```

Caddy owns certificate issuance, HTTP-to-HTTPS redirection, and TLS termination directly. Cloudflare proxying, WAF, cache rules, and Full (strict) mode are deferred beyond this internal v0.1 deployment.

- [ ] **Step 4: Reverify the direct public origin**

Verify certificate, redirects, security headers, frontend, `/healthz`, `/readyz`, API mutation behavior, and that the origin IP does not expose ports other than 80/443.

---

### Task 10: Run Real Production Acceptance

**Files:**
- Create: `deploy/verify-production.ps1`
- Create: `artifacts/deployment/<timestamp>/verification.json`
- Update: `docs/deployment/gcp-single-vm.md`

**Interfaces:**
- Consumes: public HTTPS Corpus deployment.
- Produces: sanitized production evidence covering the actual internal-user path and dependency readiness.

- [ ] **Step 1: Implement non-destructive infrastructure smoke**

Verify:

- HTTPS certificate and redirect;
- frontend load and SPA route fallback;
- `/healthz` and `/readyz` return 200;
- backend `8099` and SSH `22` are not publicly reachable;
- systemd, backend, web, and worker are active;
- disk, memory, and CPU headroom;
- no secret-shaped strings appear in public responses or recent service logs.

- [ ] **Step 2: Exercise signup and authentication through the browser**

Create one internal test account using an address controlled by the user, sign out, sign in, reload, and verify the owner conversation remains authorized. Open signup remains enabled.

- [ ] **Step 3: Verify real SMTP behavior**

Request verification and password reset, confirm mail is sent from `no-reply@saastoagent.com`, and complete at least verification. Tokens must remain in URL fragments and must not appear in server logs.

- [ ] **Step 4: Verify the existing OpenAI key and configured model**

Run one normal Corpus owner-language interaction that requires the configured OpenAI model. Record only model identity, status, latency, and request ID if safe; never record the key or private prompt content unnecessarily.

- [ ] **Step 5: Verify Source, worker, and persistence behavior**

Stage a small real OpenAPI definition, explicitly start analysis, observe queued/running/terminal state, and confirm the single worker processes it. Use an approved safe external target; do not use the local-only Medusa URL from development.

- [ ] **Step 6: Verify restart recovery**

Restart `corpus.service`, then verify account, conversation, Source state, RouteDeck state, worker, and readiness survive. No key or state may regenerate.

- [ ] **Step 7: Record honest claim boundaries**

The internal deployment is accepted only for behaviors actually exercised against available real dependencies. If ToolRouter generation/review or ecommerce Medusa execution lacks a production target/provider, record it as unavailable rather than substituting a mock or describing the whole local acceptance as deployed proof.

---

### Task 11: Monitoring, Resize, Rollback, And Operational Drill

**Files:**
- Update: `docs/deployment/gcp-single-vm.md`
- Update: `test_index/README.md`

**Interfaces:**
- Consumes: running VM and production verification.
- Produces: alerts, tested image rollback, tested backup restore, and exact resize procedure.

- [ ] **Step 1: Configure lean monitoring**

Create Cloud Monitoring alerts for:

- VM unavailable for five minutes;
- memory above 80% for ten minutes;
- CPU above 85% for fifteen minutes;
- disk above 75% warning and 85% critical;
- public `/readyz` failure;
- backup timer failure.

Send alerts to the existing project notification channel or create one user-approved email notification channel. Do not add a third-party monitoring dependency.

- [ ] **Step 2: Test image rollback**

Retain the previous digest manifest. Roll forward to the current digest, then perform a controlled rollback to the previous known-good digest and forward again, checking readiness each time. Database migrations must be backward-compatible for this exact deployment; otherwise rollback stops at the documented data boundary.

- [ ] **Step 3: Document and dry-run resize commands**

Document:

```powershell
$corpusZone = gcloud compute instances list --project=saastoagent --filter="name=('corpus-v01')" --format='value(zone.basename())'
if (-not $corpusZone) { throw 'The corpus-v01 VM was not found.' }
gcloud compute instances stop corpus-v01 --zone=$corpusZone --project=saastoagent
gcloud compute instances set-machine-type corpus-v01 --machine-type=n2-standard-4 --zone=$corpusZone --project=saastoagent
gcloud compute instances start corpus-v01 --zone=$corpusZone --project=saastoagent
```

Do not execute the resize unless observed thresholds justify it and the user approves the cost change.

- [ ] **Step 4: Perform one restore drill**

Use the first production backup to restore into a disposable attached disk or temporary VM, verify database and artifact hashes, then delete only the explicitly named disposable resources after recording proof. Do not risk the active production data merely to test restoration.

---

### Task 12: Documentation Closeout And Deployment Commit

**Files:**
- Create/update: `docs/deployment/gcp-single-vm.md`
- Modify: `architecture/code-map.md`
- Modify: `SYSTEM_FLOW_INDEX.md`
- Modify: `test_index/README.md`
- Modify: `context.md`
- Create: `logs/20260813_gcp_single_vm_deployment.md`
- Create: `context_checkpoints/2026-08-13-gcp-single-vm-deployment.md`

**Interfaces:**
- Consumes: exact resource inventory, commands, public verification, backup/restore proof, and known limitations.
- Produces: complete operator documentation, concise restart context, and one deployment commit.

- [ ] **Step 1: Complete the deployment runbook**

Document:

- GCP project, region, zone, VM, machine type, disk, IP resource name, registry, bucket, service account, and firewall rule names;
- Cloudflare DNS-only record and direct Caddy TLS ownership;
- exact build/deploy/rollback commands;
- secret names and rotation procedure without values;
- backup, restore, resize, monitoring, and cost-check commands;
- exact runtime command and public smoke URL;
- known single-node/SQLite limitations;
- dependency/provider claim boundaries.

- [ ] **Step 2: Update architecture and validation owners**

Update only the Docker/deployment runtime row and affected runtime flows. Do not rewrite product feature documentation when behavior has not changed.

- [ ] **Step 3: Run the final gates**

Run:

```powershell
docker compose -f compose.production.yaml config --quiet
.\.venv\Scripts\python.exe -m pytest backend\tests\runtime backend\tests\infrastructure backend\tests\persistence -q
pnpm --dir frontend typecheck
pnpm --dir frontend build
.\.venv\Scripts\python.exe scripts\check_doc_coverage.py
```

Also rerun `deploy/verify-production.ps1` against `https://corpus.saastoagent.com` and record the exact outcome.

- [ ] **Step 4: Review the complete diff and secret hygiene**

Run `git diff --check`, inspect every deployment file, verify ignored runtime files are absent from `git status`, and scan tracked files for secret-shaped content. The scan reports file names only and never prints suspected secret values.

- [ ] **Step 5: Commit only the authorized deployment scope**

Stage the production Docker/Compose/proxy/scripts/tests/runbook and required architecture/context updates. Commit with a descriptive message such as:

```text
deploy: add lean GCP single-VM production runtime
```

Do not push. Report the commit hash, changed files, exact production URL, runtime location, verification outcome, resource inventory, and any remaining limitation.

---

## Completion Gate

Deployment is complete only when all of the following are true:

- `https://corpus.saastoagent.com` serves a valid certificate directly from Caddy while Cloudflare remains DNS-only.
- Only ports 80/443 are public; SSH works through IAP and OS Login.
- Backend, worker, and web are systemd-managed and survive VM restart.
- Signup, sign-in, real SMTP, one real OpenAI interaction, and one real worker job are verified.
- Persistent state survives service and VM restart without regenerating keys.
- A private backup exists and a restore drill succeeds away from production.
- Monitoring alerts exist for uptime, resource pressure, disk, readiness, and backup failure.
- Production images are digest-pinned and rollback is tested.
- Documentation contains exact commands, resource names, smoke URL, limits, and recovery steps.
- The final Git commit contains no secrets, local runtime data, or unrelated RouteDeck changes.
