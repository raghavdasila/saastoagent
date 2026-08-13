# Deployed Three-Mode Ecommerce Acceptance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove the deployed Corpus product through the same complete Medusa ecommerce lifecycle in surface, hybrid, and ordinary-chat modes while measuring whether the current Corpus and Medusa VM sizes are sufficient.

**Architecture:** A separate private Medusa 2.13.6 acceptance VM provides the real ecommerce API and canonical seeded data. Corpus retains the exact previously accepted OpenAPI Source bytes and reviewed hashes, while its protected connection profile supplies the private execution base URL through one exact outbound allowlist entry. A production-aware local controller drives the public Corpus UI, performs VM-local restart actions through IAP, audits Medusa without publishing credentials, and samples both VMs throughout each run. The three modes run sequentially against independent owner, conversation, Source, Agent, build, deployment, public-session, and cart lineages.

**Tech Stack:** GCP Compute Engine and VPC, Docker Compose, systemd, Medusa 2.13.6, PostgreSQL 16, Redis 7, Corpus/FastAPI/Huey/Caddy, Playwright, PowerShell, Python, OpenAI `gpt-5.6-luna`.

## Global Constraints

- Corpus remains on `corpus-vm-1`, `n2-standard-2`, `asia-south1-a`; no Corpus tier upgrade is authorized.
- Medusa starts on non-preemptible Free Tier `e2-micro`; upgrade only to `e2-small` if measured evidence shows the free tier cannot complete the required real workflow.
- Medusa must not expose an application port publicly. Administrative access uses IAP; Corpus uses the exact private VPC address.
- Use the pinned RouteDeck-owned Medusa 2.13.6 reference and canonical seed read-only. Never edit the sibling RouteDeck repository.
- No mocks, fixtures substituted for the real target, silent fallback, direct Corpus database mutation, test-only product branch, or alternate model/provider.
- OpenAI remains `gpt-5.6-luna`; credentials remain in Secret Manager or protected product forms and never enter retained evidence.
- Run modes sequentially in the order surface, hybrid, chat. Each mode gets an independent lineage and exactly one audited cart containing one `Medusa T-Shirt`, quantity 1.
- Back up Corpus before changing its production allowlist. Keep only 80/443 public on Corpus.
- Git is authorized for deployment/test changes and earlier changes, including plan documentation and commits. Never push.

---

### Task 1: Private Medusa acceptance target

**Files:**
- Create or modify only deployment-owned files under `deploy/medusa-test/` if durable scripts are required.
- Modify: `docs/deployment/gcp-single-vm.md` only when the deployed dependency boundary changes.

**Interfaces:**
- Consumes: read-only pinned Medusa 2.13.6 source and seed from the RouteDeck checkout.
- Produces: one private normalized base URL, a protected publishable credential, canonical seed sentinel, restart command, and read-only health/product/cart-audit commands.

- [ ] Verify `medusa-test-vm-1` is non-preemptible `e2-micro` in a Free Tier region, has no external IP, uses at most 30 GB `pd-standard`, and has swap enabled.
- [ ] Finish schema migration and canonical seeding without recovering from partial state through an alternate seed or fixture.
- [ ] Start PostgreSQL, Redis, and Medusa 2.13.6 and verify `/health` locally on the Medusa VM.
- [ ] Call the real `GetProducts` path with the protected publishable key and require a `Medusa T-Shirt` plus a usable variant ID.
- [ ] Restart the complete Medusa service and re-run health, product, and seed-sentinel checks.
- [ ] From `corpus-vm-1`, call the private health endpoint and prove that no public application firewall rule exists.
- [ ] Record idle and startup CPU, memory, swap, disk, container, and kernel OOM evidence.

### Task 2: Production-aware controller and telemetry contracts

**Files:**
- Modify: `scripts/run_horizontal_product_journey.py`
- Create: `scripts/deployed_e2e_runtime.py`
- Create: `scripts/collect_gcp_vm_telemetry.py`
- Create: `tests/test_deployed_e2e_runtime.py`
- Create: `tests/test_collect_gcp_vm_telemetry.py`

**Interfaces:**
- Consumes: public Corpus URL, private Medusa base URL, GCP project/zone/VM identities, existing protected Medusa credential file, and the existing three-mode assertions.
- Produces: an explicit `local` or `gcp-production` runtime controller plus timestamped JSONL telemetry and a summarized per-VM performance report.

- [ ] Write focused tests proving production mode refuses localhost Medusa, missing VM identities, mutable/empty target URLs, and any attempt to use local Docker restart commands.
- [ ] Add explicit CLI inputs for Medusa connection-profile base URL, Medusa credential source, runtime mode, Corpus/Medusa VM identities, and telemetry output. Preserve the exact accepted Source bytes, local defaults, and behavior.
- [ ] Implement the production restart boundary through `gcloud compute ssh --tunnel-through-iap` and `sudo systemctl restart corpus.service`; require a new backend/worker container generation and three stable public `/readyz` successes.
- [ ] Replace hard-coded runtime evidence values with the exact supplied endpoints and verified provider identity.
- [ ] Sample both VMs at a fixed interval during each journey: `/proc/loadavg`, CPU counters, `free`, swap, disk usage, diskstats, Docker container usage, uptime, service state, and kernel OOM messages. Never collect environment variables, headers, bodies, or secrets.
- [ ] Derive peak memory, peak swap, peak load, CPU saturation intervals, disk headroom, restart duration, request latency evidence available from safe traces, and OOM count.
- [ ] Run the focused controller and telemetry tests before touching production.

### Task 3: Back up and wire Corpus to the exact private target

**Files:**
- Modify: `compose.production.yaml`
- Modify: `deploy/corpus-prestart.sh` or an existing production environment owner only if needed to supply the exact allowlist safely.
- Modify: `backend/tests/runtime/test_production_deployment.py` or the current production deployment contract test.
- Modify: `docs/deployment/gcp-single-vm.md`

**Interfaces:**
- Consumes: normalized private Medusa URL from Task 1.
- Produces: one exact `CORPUS_API_CHECK_ALLOWED_BASE_URLS` entry available to backend and worker, with no additional destination authorized.

- [ ] Run and verify an application-consistent Corpus backup before rollout.
- [ ] Add a failing deployment-contract test requiring an explicit single acceptance-target URL and rejecting an empty or wildcard allowlist.
- [ ] Implement the smallest production configuration change that supplies only the private Medusa URL to backend and worker.
- [ ] Validate Compose configuration, production contract tests, digest pins, firewall posture, and secret-free rendered configuration.
- [ ] Roll out through the existing systemd/IAP procedure and require healthy backend, worker, web, `/healthz`, and `/readyz`.
- [ ] Confirm port 8099 and the Medusa application port remain unavailable publicly.

### Task 4: Bounded production preflight

**Files:**
- Retain results under `artifacts/deployed-ecommerce-preflight/<run-id>/`.
- Modify no product source unless a feature-owned defect is reproduced independently.

**Interfaces:**
- Consumes: Tasks 1-3.
- Produces: a secret-free proof that production Corpus can ingest the target contract and execute the exact real API safely before a horizontal run begins.

- [ ] Take baseline telemetry from both VMs and snapshot the preflight Medusa cart count.
- [ ] Create one disposable owner through the real public authentication path using an accepted mailbox identity.
- [ ] Stage and explicitly analyze the production-target Medusa OpenAPI definition.
- [ ] Save the protected connection profile and require a successful safe connection/product-search call through Corpus.
- [ ] Stage a cart write and prove zero external calls before review; reject it and prove the cart count remains unchanged.
- [ ] Delete or archive the disposable product objects only through supported product behavior if such behavior exists; otherwise label and retain them.
- [ ] If preflight fails, stop the horizontal campaign and return to the owning feature with a bounded reproduction.

### Task 5: Sequential surface, hybrid, and chat acceptance

**Files:**
- Retain each run under `artifacts/horizontal-product-<mode>/<run-id>/`.
- Create: `docs/superpowers/validation/2026-08-13-deployed-ecommerce-three-mode.md` after all outcomes are immutable.

**Interfaces:**
- Consumes: passing preflight and production-aware controller.
- Produces: three independent result manifests, continuous videos, screenshots, safe traces, VM telemetry, post-run Medusa audits, and explicit pass/fail status.

- [ ] Record the initial Medusa cart identity set, start telemetry, and run surface mode from fresh owner state.
- [ ] Require all 39 surface assertions, zero unexpected diagnostics, one continuous video, restart recovery, reviewed writes, and exactly one new audited cart with one T-shirt quantity 1.
- [ ] Stop telemetry, generate the surface capacity summary, and verify evidence contains no owner password or Medusa credential.
- [ ] Repeat from fresh owner state for hybrid mode and require all 40 assertions plus the exact chat/surface interaction boundary.
- [ ] Repeat from fresh owner state for ordinary-chat mode and require all 39 assertions, surface-only credential entry, and ordinary business-language prompts.
- [ ] Never reclassify a failed or partial run. Diagnose a failure in its feature lane before deciding whether a replacement horizontal run is warranted.

### Task 6: Capacity decision and closeout

**Files:**
- Modify: `docs/superpowers/validation/2026-08-13-deployed-ecommerce-three-mode.md`
- Modify: `docs/deployment/gcp-single-vm.md`
- Modify: `context.md`
- Create: `logs/20260813_deployed_ecommerce_three_mode.md`
- Create: `context_checkpoints/2026-08-13-deployed-ecommerce-three-mode.md`

**Interfaces:**
- Consumes: immutable outcomes and telemetry from all prior tasks.
- Produces: a blunt sufficiency decision for each VM, exact remaining risks, reproducible operational commands, and a clean restart handoff.

- [ ] Classify Corpus sufficiency using peak memory/swap, sustained CPU/load, OOMs, restart duration, readiness, queue progress, and user-visible latency. Do not resize it.
- [ ] Classify Medusa `e2-micro` as sufficient, marginal, or unusable. Upgrade only to `e2-small` when the real target cannot complete setup/restart/three-mode load or exhibits OOM, unrecoverable thrashing, or repeated timeout failures attributable to resource pressure.
- [ ] If upgraded, rerun the failed bounded preflight first and record before/after telemetry; do not silently replace evidence from the free VM.
- [ ] Verify production health, Medusa health, timers/backups, firewall posture, and absence of public administrative/application ports.
- [ ] Run focused tests, deployment contracts, documentation coverage, and secret scans over retained evidence.
- [ ] Update the validation report, run log, checkpoint, and concise `context.md` without overstating production/SLA readiness.
- [ ] Review the exact diff, commit only authorized deployment/test/documentation changes, and do not push.

## Self-Review

- The plan covers the real Medusa dependency, private networking, exact allowlist, protected credentials, production restart semantics, all three independent modes, cart audits, performance measurement, the constrained upgrade decision, documentation, and Git boundaries.
- A failed preflight or feature blocks horizontal testing; no mock, fallback, permissive allowlist, direct database mutation, or tier escalation is used to manufacture success.
- Local and production controllers remain explicit modes so existing local acceptance behavior is preserved.
