# Private Medusa Acceptance VM on GCP

Status: deployed and validated for Corpus production acceptance on 2026-08-13

The reason this target is a separate private Free Tier VM, its upgrade boundary,
and the alternatives considered are recorded in
[`ADR-004`](../../decisions/ADR-004-gcp-single-vm-v0-1-deployment.md). This
runbook owns Medusa-specific operations.

## Boundary

This is a real Medusa 2.13.6 acceptance target for the deployed Corpus
ecommerce journeys. It is not a public storefront or a production commerce
service. Corpus's production allowlist and the three-mode journey runner are
outside this deployment slice and were not changed here.

The server source, protected seed workflow, and data contract come unchanged
from the read-only RouteDeck reference at
`D:\Dev\AI Projects\routedeck\examples\medusa-agent`. The Medusa image was
built locally from that pinned source and lockfile; no build ran on the small
VM and no RouteDeck file was modified.

## Live inventory

- GCP project: `saastoagent`
- VM: `medusa-test-vm-1`
- zone: `us-west1-a` (Free Tier eligible)
- machine: non-preemptible `e2-micro`
- image: Container-Optimized OS stable
- boot disk: 30 GB `pd-standard`
- private address: `10.138.0.2`; no external IPv4 address
- VM identity: `medusa-test-vm@saastoagent.iam.gserviceaccount.com`
- VM role: Artifact Registry reader only
- persistent runtime root: `/var/lib/medusa-acceptance`
- swap: 2 GiB file under that persistent runtime root
- owner: `medusa-acceptance.service`, restored at each COS boot by Compute
  Engine startup metadata

The private Store endpoint is `http://10.138.0.2:9100`. Firewall priority
allows only:

- IAP `35.235.240.0/20` to TCP 22;
- Corpus VM `10.160.0.2/32` to TCP 9100;
- an explicit lower-priority deny blocks every other ingress protocol/source
  for the `medusa-acceptance` target tag.

The `us-west1` default subnet has Private Google Access enabled so the VM can
pull private images without an external IP or Cloud NAT.

Corpus retains the exact reviewed OpenAPI Source bytes whose primary server is
`http://localhost:9000`; those bytes and their reviewed correction hashes are
immutable acceptance evidence. The owner-protected Corpus connection profile,
not the Source document, supplies `http://10.138.0.2:9100` as the deployed
execution origin. Production allows exactly that normalized origin.

## Immutable images

All runtime references are digest-qualified in
`/var/lib/medusa-acceptance/run-medusa.sh`:

- Medusa 2.13.6:
  `asia-south1-docker.pkg.dev/saastoagent/corpus/medusa-acceptance@sha256:bb3c35bd38b96ad3d47d4897cbd166dbf2c3b6924857f228c91569e8045bba5d`
- PostgreSQL 16 Alpine:
  `asia-south1-docker.pkg.dev/saastoagent/corpus/postgres@sha256:9298b1741941b306c6fe40aa30acdbf5ce2934ab4bddaa4536e53f1817ff677f`
- Redis 7 Alpine:
  `asia-south1-docker.pkg.dev/saastoagent/corpus/redis@sha256:b9f6cf0cab55fdd102fd2182deeae150457943d33439d18c6e2fc5666d3228c1`

PostgreSQL and Redis are private Docker-network dependencies and publish no
host port. Medusa alone binds host TCP 9100; VPC firewall rules keep it private
to the Corpus VM.

## Runtime and credentials

The protected RouteDeck provisioner performed Medusa migrations, the
deterministic seed, seed fingerprinting, credential generation, and sentinel
creation exactly once. Generated values remain root-readable only under
`/var/lib/medusa-acceptance`; they are not stored in repository files, instance
metadata, logs, or this runbook.

The retained canonical seed fingerprint is
`5bda6e5cfc873107f535e573b626739bc127a741e60ec482062245e1f3ec47ba`.
The database has exactly one protected `routedeck_demo_sentinel` row.

Container limits are deliberately tight for acceptance use:

| Service | Memory limit | Memory plus swap ceiling |
| --- | ---: | ---: |
| Medusa | 640 MiB | 2 GiB |
| PostgreSQL | 256 MiB | 768 MiB |
| Redis | 64 MiB | 128 MiB |

Medusa runs the reference's development-mode command because that is the
accepted executable configuration. Startup reruns idempotent migrations and
takes roughly 4.5 minutes on `e2-micro`; health checks must tolerate that cold
start. Do not replace it with a different build/mode and call it equivalent
without a new reference proof.

## Operations

Use IAP only:

```powershell
gcloud compute ssh medusa-test-vm-1 `
  --project=saastoagent `
  --zone=us-west1-a `
  --tunnel-through-iap
```

On the VM:

```bash
sudo systemctl status medusa-acceptance.service
sudo journalctl -u medusa-acceptance.service -n 200 --no-pager
sudo docker ps
sudo docker stats --no-stream
sudo /bin/bash /var/lib/medusa-acceptance/probe-medusa.sh
sudo /bin/bash /var/lib/medusa-acceptance/audit-medusa-carts \
  2026-08-13T16:00:00Z
```

The probe reports status, product identity, response size, seed fingerprint,
and sentinel count without displaying the publishable key or response body.
The root-only cart audit requires one RFC 3339 UTC timestamp and emits CSV with
only `cart_id,product_title,variant_title,variant_id,quantity` for non-deleted
carts created after that timestamp. It reports empty carts with blank item
fields and rejects malformed timestamps before SQL execution.

Stopping the VM stops Compute Engine billing; its disk and private registry
storage remain allocated. Starting the same VM retains its private IP and
state. After a start or reboot, allow about five minutes for automatic Medusa
recovery before expecting the endpoint to be ready.

## Validation evidence

The following passed on 2026-08-13:

- local `GET /health` returned HTTP 200 with `OK`;
- authenticated `GET /store/products` returned HTTP 200 and contained the
  real `Medusa T-Shirt` (10,054-byte response at validation time);
- service restart completed in 88 seconds with stable seed fingerprint and
  all three containers reporting no OOM;
- a full guest reboot changed the kernel boot ID, restored the COS systemd
  unit from persistent state, and returned the same health/product/fingerprint
  and sentinel results after 4 minutes 29 seconds;
- from `corpus-vm-1` (`10.160.0.2`), private
  `http://10.138.0.2:9100/health` returned HTTP 200 with `OK`;
- the steady snapshot used about 377 MiB for Medusa, 28 MiB for PostgreSQL,
  and 4 MiB for Redis, with 295 MiB host memory available, 22 MiB swap used,
  and zero kernel/container OOM events.

## Cost boundary

Google Cloud Free Tier covers an eligible monthly amount equivalent to one
non-preemptible `e2-micro` in `us-west1`, plus 30 GB-month of standard
persistent disk, aggregated across eligible usage. It is not an unconditional
billing guarantee: other eligible instances/disks on the billing account share
the allowance.

Private traffic between `us-west1` and `asia-south1` is cross-region data
transfer. Current VPC pricing charges North America-to-Asia VM traffic at
USD 0.08/GiB to the sending project; acceptance traffic should be small but is
not free merely because both endpoints use private IPs. Artifact Registry
storage and cross-region image pulls can also incur small charges. No external
IPv4 address, Cloud NAT, load balancer, or DNS record is used.

Authoritative pricing references:

- <https://docs.cloud.google.com/free/docs/free-cloud-features>
- <https://cloud.google.com/vpc/pricing>
- <https://cloud.google.com/artifact-registry/pricing>

## Known operational note

The VM service account deliberately lacks Cloud Logging writer permission.
The Google startup-script runner therefore logs a harmless failure to flush
its own messages to Cloud Logging after the startup script has exited zero.
Systemd/journald logs remain locally available through IAP. Do not widen the
service account merely to remove that warning unless centralized logging is
explicitly required.
