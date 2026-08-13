# Deployed Ecommerce Three-Mode Validation

Validated 2026-08-13/14 against `https://corpus.saastoagent.com`, real OpenAI
`gpt-5.6-luna`, and private pinned Medusa 2.13.6 at `10.138.0.2:9100`.
RouteDeck remained read-only. No mock, fallback, direct database mutation,
rate-limit bypass, instance resize, or evidence reclassification was used.

## Accepted runs

| Mode | Run | Result | Video | Restart |
| --- | --- | --- | --- | --- |
| Surface | `20260813T183912Z-76fa3a454a` | 39/39, zero unexpected diagnostics | 603.28 s, SHA-256 `33464b978b697690d7d699bffb87ef2c36089885e0721d0078f791c1763f4762` | 131.75 s |
| Hybrid | `20260813T191806Z-5249834ee9` | 40/40, zero unexpected diagnostics | 904.76 s, SHA-256 `6fbae09c2921d0014ff649b6bbd2a850dd197acf7e89a0299ade3113a28816b5` | 116.00 s |
| Chat | `20260813T193405Z-5f81fb0b5f` | 39/39, zero unexpected diagnostics | 1010.08 s, SHA-256 `a2f66f43b7d128ce23ebafc8a972df9c193f7fe41d6199adbed40f0c16c13315` | 88.09 s |

Each run used an independent owner, conversation, Source, Agent, build,
deployment, public session, and cart lineage. The root-only Medusa audit found
exactly one new cart per accepted run, each containing one `Medusa T-Shirt`
variant at quantity 1. The retained artifacts are under
`artifacts/horizontal-product-{surface,hybrid,chat}/<run-id>/result.json`.

Expected restart interruptions are retained separately from unexpected
diagnostics. They are bounded to GET `/api/**` connection closures/refusals
observed only during the intentional single-VM restart window. All three final
runs have zero unexpected HTTP, console, page, and request failures.

## Capacity

| VM | Peak memory | Swap | Peak load 1m | Host CPU peak / average | Disk free minimum | OOM | Decision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Corpus `n2-standard-2` | 2.90 GB | 0 | 1.53 | 100% brief / 29.65% worst run average | 152.6 GB | 0 | Sufficient for internal five-user v0.1; keep size |
| Medusa `e2-micro` | 658 MB | 42.5 MB | 0.40 | 44.90% brief / 1.43% worst run average | 23.39 GB | 0 | Sufficient but intentionally marginal/non-SLA; keep Free Tier |

Corpus container CPU can exceed 100% because Docker reports usage across its
two vCPUs. Queue progress, readiness, all reviewed writes, and three restart
recoveries completed. Medusa remained far below sustained CPU saturation and
needed no paid-tier upgrade.

## Corrections proven in production

- The strict OpenAI semantic-review schema now uses the supported Structured
  Outputs subset; duplicate selected endpoint IDs are rejected after parsing.
- Natural clarification selection deduplicates identical operation candidates.
- The production recorder handles already-active destination surfaces,
  multi-step operation/input clarification, and intentional restart diagnostics.
- Telemetry records an IAP SSH timeout as an error sample and continues.

Earlier failed/partial runs remain immutable historical evidence and are not
listed as passes. The current claim is deployed internal acceptance, not SLA or
broad concurrent-load certification.
