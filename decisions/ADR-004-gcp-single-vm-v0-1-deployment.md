# ADR-004: GCP Single-VM Deployment for Corpus v0.1

Status: accepted, deployed, and validated

Date: 2026-08-13

## Context

Corpus needed to move from a local Docker acceptance stack to a real internet
deployment where a small internal group could sign up and exercise the complete
product. The initial target is approximately five internal users. This is a
lean v0.1 deployment, not a high-availability or production-SLA platform.

The deployed product has more than a static frontend: it requires a web proxy,
the Corpus backend, a durable background worker, persistent application and
Source data, migrations, runtime secrets, email delivery, OpenAI access, image
distribution, backups, and restart recovery. The deployment also had to retain
the existing Corpus/RouteDeck ownership boundary and avoid putting source
checkouts or Git credentials on the server.

Three deployment methodologies were considered.

### 1. Conventional VM

Run the containerized application on one general-purpose VM, with systemd and
Docker Compose owning its lifecycle. Use selected cloud services only where
they materially reduce operational risk: image storage, secret delivery,
backups, snapshots, DNS, and certificate issuance.

This gives the current multi-process application one host, one filesystem, a
simple restore boundary, direct logs, and no forced redesign. The trade-off is
that the team owns OS patching, Docker, service recovery, disk capacity, and
the single-host availability boundary.

### 2. Managed cloud services

Split the application across managed compute and data services, for example
Cloud Run or GKE plus Cloud SQL, managed Redis, object storage, load balancing,
and a managed secret system.

This is a stronger future fit for independent scaling, managed availability,
and reduced host administration. It was rejected for v0.1 because it adds
service count, networking and IAM edges, recurring baseline cost, and migration
work before the five-user workload demonstrates a need. Corpus still has
filesystem-backed state and a durable worker lifecycle that would need to be
made explicitly compatible with stateless managed compute.

### 3. Docker-stack platform as a service

Deploy the existing containers to a Docker-oriented platform such as Railway,
Render, Fly.io, or a similar stack host. This can be the fastest path for a
small application when the platform supplies builds, TLS, logs, persistent
volumes, and managed databases.

This was not selected because Corpus has a multi-repository image closure,
durable local state, a continuously running worker, strict private integration
requirements, and explicit backup/restore needs. A platform could support
those requirements, but its volume, networking, sleep, build-context, and
egress semantics would need separate proof. GCP was already authenticated and
the project was configured, so introducing another control plane did not make
the first deployment leaner.

## Decision

### Provider and topology

- Use Google Cloud project `saastoagent` and `gcloud` as the deployment control
  plane.
- Run Corpus on exactly one Compute Engine VM, `corpus-vm-1`, in
  `asia-south1-a` (Mumbai).
- Use the other Mumbai zones only as allocation fallbacks if the preferred
  zone lacks N2 capacity. Checking or listing all zones does not create a VM;
  the provisioner creates or reuses exactly one named Corpus instance.
- Keep Cloud SQL, Memorystore, GKE, Cloud Run, and a load balancer out of this
  v0.1 topology.

GCP was preferred because `gcloud` was already authenticated, the user had set
the default project, the target audience is close to Mumbai, and Compute Engine
allows the current Docker application to run without an architectural rewrite.

### Initial Corpus capacity

- Start with `n2-standard-2`: two vCPUs and 8 GB RAM.
- Attach a 160 GB balanced persistent boot disk.
- Treat vertical resizing as the first capacity response if real internal use
  shows sustained CPU pressure, memory pressure, swap, or unacceptable latency.

The earlier conservative estimate of four dedicated vCPUs and 16 GB RAM was
appropriate for more headroom, but unnecessary for an initial five-user test.
Compute Engine allows the instance machine type to be changed after stopping
the VM, so starting smaller was a reversible cost decision. The deployed
three-mode acceptance later measured a 2.90 GB memory peak, zero swap, zero OOM
kills, a 1.53 peak one-minute load, and 21-30% average sampled CPU despite brief
90-100% peaks. That evidence supports retaining `n2-standard-2` for the current
internal target; it is not a broader production capacity claim.

The balanced disk provides space for immutable Docker images, application and
Source state, deployment files, operational headroom, and recovery activity.
Application archives are uploaded off-host, and the disk also has a seven-day
snapshot policy.

### Application runtime and delivery

- Build immutable production images locally from the approved Corpus,
  RouteDeck, Agent Execution Runtime, and Agent Delivery Runtime closure.
- Store images in Artifact Registry and deploy digest-qualified references;
  mutable tags are rejected by the VM prestart gate.
- Do not clone repositories or store Git credentials on the VM. Git is not the
  deployment transport.
- Run Caddy, one Uvicorn backend process, and one Huey worker through Docker
  Compose, owned by `corpus.service`.
- Run migrations once in the prestart path before bringing up the stack.
- Keep durable state under `/srv/corpus`, with nightly application archives and
  scheduled disk snapshots.

This keeps the deployed runtime reproducible while preserving the application's
existing process and persistence boundaries. Systemd provides boot recovery and
one operational owner for the Compose stack.

### DNS and TLS

- Reserve a static regional IPv4 address before application rollout.
- Ask the user to create the Cloudflare `A` record for
  `corpus.saastoagent.com` early, so DNS propagation can proceed while the
  remaining deployment work continues.
- Keep the Cloudflare record DNS-only for v0.1.
- Let Caddy terminate TLS directly, redirect HTTP to HTTPS, and renew the
  public certificate.

Cloudflare proxying is not required to make the service secure or reachable.
`Full (strict)` becomes relevant only if Cloudflare proxying is enabled later:
it tells Cloudflare to validate the origin certificate instead of weakening
the Cloudflare-to-origin leg. Proxying, WAF rules, and Cloudflare caching are
deferred so TLS has one clear owner in v0.1.

### Security and secrets

- Expose only TCP 80 and 443 publicly.
- Permit administrative SSH only through Google IAP and OS Login; targeted
  firewall denies override permissive default-network SSH/RDP rules for this
  VM.
- Give the VM a dedicated least-privilege service account; do not create or
  copy a service-account JSON key.
- Store the existing OpenAI API key, SMTP app password, encryption keys, vault
  key, and auth secrets in Secret Manager.
- Materialize secrets atomically at service startup into root-only
  `/run/corpus/runtime.env`, not an image, repository file, instance metadata,
  or deployment log.
- Pin runtime images by digest, fail closed when required secrets or providers
  are unavailable, and retain verified backup/restore procedures.

This is deliberately lean hardening for an internet-facing v0.1. It does not
claim a complete enterprise security program, centralized SIEM, multi-zone
availability, or a managed WAF.

### OpenAI and email

- Reuse the existing OpenAI API key rather than creating per-environment keys
  for this internal v0.1.
- Configure the model through the provider boundary as `gpt-5.6-luna` with low
  reasoning effort. The model name is configuration, not a product or code
  identity, so it remains naturally swappable.
- Use the existing `saastoagent.com` sender and SMTP configuration.
- Do not add email-domain limiting for the initial internal test.
- Do not silently fall back to Ollama or another model/provider in production;
  provider failure remains a visible operation failure.

Reusing the credentials and sender reduced launch work, while Secret Manager
and the existing narrow provider/mail adapters avoided embedding either value
in the application or VM image.

### Medusa acceptance dependency

The ecommerce acceptance target is intentionally a separate deployment
boundary, not a second Corpus application VM:

- Run pinned Medusa 2.13.6, PostgreSQL 16, and Redis 7 on
  `medusa-test-vm-1`, a non-preemptible `e2-micro` in Free Tier-eligible
  `us-west1-a` with a 30 GB standard persistent disk.
- Give it no external IPv4 address. Permit TCP 9100 only from the exact Corpus
  VM private address, and use IAP for SSH.
- Allow private image pulls through Private Google Access.
- Keep credentials and seeded state root-readable under persistent VM state.
- Allow an upgrade only to the cheapest suitable paid VM if the Free Tier VM
  cannot complete the real reference workflow. No upgrade was needed.

Free Tier capacity in `us-central1` was unavailable at provisioning time, so
the attempt moved to another eligible region rather than changing the machine
class. The real reference deployment, canonical seed, restart, full guest
reboot recovery, Corpus-to-Medusa private probe, and three ecommerce journeys
all passed. Peak observed memory was 658 MB with about 42.5 MB swap, zero OOM,
and low average CPU. Retaining `e2-micro` is therefore acceptable for this
test-only, non-SLA dependency, but its limited memory and roughly five-minute
cold recovery make it unsuitable as an assumed production commerce tier.

Cross-region VM traffic and Artifact Registry activity may incur small charges
even when the VM itself fits the Free Tier allowance.

## Alternatives Considered

### Start with a four-vCPU, 16 GB Corpus VM

Rejected for the five-user internal phase. It buys additional headroom but
spends before measurement. The chosen VM passed the real deployed workload and
can be resized later during a controlled stop.

### Put Corpus and Medusa on the same VM

Rejected. Medusa is acceptance infrastructure with different ownership,
lifecycle, cost, exposure, and production-readiness claims. Co-location would
consume Corpus headroom and blur whether a failure belongs to Corpus or the
test target.

### Expose Medusa publicly

Rejected. Only Corpus needs the Store API for acceptance. A private address,
an exact source-address firewall rule, and IAP administration provide the
needed path without creating a public commerce endpoint.

### Enable Cloudflare proxying immediately

Rejected for v0.1. It would add another TLS and request-routing hop before it
was needed. DNS-only plus direct Caddy TLS is simpler to diagnose. Proxying can
be introduced later with `Full (strict)` after its caching, headers, WAF, and
origin-access policy are explicitly designed and tested.

### Use mutable image tags or deploy from a Git checkout on the VM

Rejected. Mutable references weaken rollback and provenance, while a live Git
checkout expands credentials and mutable source on the host. Digest-pinned
Artifact Registry images make the executable release explicit.

## Consequences

- The deployment is inexpensive, understandable, and matches the application
  proven locally without converting it to a distributed system.
- The Corpus VM remains a single point of failure. Snapshots, archives, and
  restart automation improve recovery but do not provide high availability.
- Scaling is vertical first. Multi-instance scaling would require externalizing
  remaining filesystem state, reviewing worker concurrency and request/session
  ownership, and choosing managed data services.
- Maintenance includes OS security updates, Docker/runtime health, disk usage,
  certificate renewal, backups, restore drills, and capacity observation.
- The private Medusa VM is acceptance infrastructure only. Its successful
  Free Tier run is not a recommendation for production Medusa traffic.
- Cloudflare remains user-owned DNS. Future proxy/WAF adoption is a separate
  decision with a new end-to-end validation requirement.

## Validation

- Public signup, TLS, SPA, `/healthz`, and `/readyz` passed at
  `https://corpus.saastoagent.com`.
- A real protected OpenAI Responses call used the exact configured
  `gpt-5.6-luna` model with no provider fallback.
- Surface, Hybrid, and Chat deployed journeys passed 39/39, 40/40, and 39/39,
  each with independent lineage, one audited quantity-1 Medusa T-shirt cart,
  continuous video, successful Corpus restart recovery, and zero unexpected
  diagnostics.
- The Corpus VM had zero swap and zero OOM events across acceptance; Medusa had
  zero OOM events and remained within the accepted marginal test boundary.
- Detailed operating procedures are in
  `docs/deployment/gcp-single-vm.md` and
  `docs/deployment/gcp-medusa-acceptance-vm.md`.
- Exact run IDs, capacity samples, and evidence paths are in
  `docs/superpowers/validation/2026-08-13-deployed-ecommerce-three-mode.md`.

## Revisit Triggers

Re-evaluate this decision when any of the following becomes true:

- sustained CPU saturation, memory pressure, swap, disk pressure, or latency
  under normal internal use;
- a requirement for production SLA, multi-zone availability, zero-downtime VM
  maintenance, or horizontal scaling;
- backup or restore objectives exceed the current snapshot/archive approach;
- filesystem persistence prevents safe multi-instance or managed-compute use;
- Medusa becomes a real production dependency rather than an acceptance target;
- centralized logging, managed WAF, Cloudflare proxying, or stricter environment
  credential separation becomes an explicit requirement.

