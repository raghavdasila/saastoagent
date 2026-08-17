# Agent Delivery Runtime Integration

Updated: 2026-08-17

Status: package integrated through Corpus-owned adapters; standalone proof host
remains separate and optional

Standalone authority: `D:\Dev\AI Projects\agent-delivery-runtime`

Canonical source is the private repository
`https://github.com/saastoagent/agent-delivery-runtime` at the exact commit
recorded in
`contracts/dependency-provenance/development-source-checkouts.json`.

## Purpose and authority

The separately owned package supplies immutable deployment revisions,
activation and rollback, channel/public-session state, redacted interaction
evidence, and evaluation-candidate export for an already compiled eligible
Agent.

Corpus installs pinned `agent-delivery-runtime==0.1.0` source into its
backend/worker image and consumes the package in process behind Corpus-owned
delivery adapters and stores. The standalone API/owner/public Web environment
on ports 8880/5280 remains an optional package proof. It is not part of the
ordinary Corpus service topology and its Medusa example is not Corpus product
acceptance.

## Current ownership and integration

| Corpus owner | Package boundary | Current integration |
| --- | --- | --- |
| Agent Designer and RouteDeck mapping | No direct boundary; Delivery accepts an already compiled bundle | Corpus passes only accepted, compiled RouteDeck and product-surface identities. Delivery never compiles or reinterprets Studio state. |
| Agent Builder | trusted immutable deployable bundle | Corpus publishes the exact eligible build through its application adapters while preserving build, RouteDeck app, surface-contract, and eligibility identities. |
| Owner identity | authenticated Corpus operations | Corpus owner authorization remains outside the package. Standalone bearer-token files and its owner UI are proof infrastructure only. |
| Channels/Web | channel state, public slug, sessions, and projections | Corpus owns channel configuration and owner-facing management; the delivery package owns immutable activation and public-session lifecycle behind Corpus adapters. |
| Deployment | request/status, verification, activation, retry, and rollback | Corpus stages RouteDeck review and submits the authorized exact build. The package preserves compatibility checks and transaction-safe activation; failures remain visible. |
| RouteDeck runtime | deployed-Agent runtime port | Corpus provisions/invokes the exact compiled Agent through public RouteDeck contracts. RouteDeck retains state, operation, review, surface, and terminal-execution authority. |
| Product Web rendering | RouteDeck message/surface/suggested-action projection | Corpus owns the hosted Agent route and product components. Package projections never copy owner-only Corpus state into a public session. |
| Operations | redacted interaction records/projections | Corpus authorizes, searches, and presents evidence; provider objects, credentials, and unrestricted bodies remain private. |
| Evaluation | evaluation-candidate export | Corpus retains build/deployment/interaction lineage and decides whether evidence enters an evaluation set. Export alone is not evaluation. |
| Persistence and work queue | delivery store and deployment job ports | Corpus supplies its selected SQLite/Huey adapters in the current single-host topology without changing package domain contracts. |

Application composition is owned by
`backend/src/corpus/app/delivery_runtime_adapters.py`,
`backend/src/corpus/app/delivery_runtime_store.py`, and
`backend/src/corpus/integrations/agent_delivery`. Feature packages consume
neutral `corpus.shared.agent_delivery` contracts.

## Current product flow

```text
accepted Corpus design
-> compiled RouteDeck Agent and product surface contract
-> immutable Corpus Agent Build
-> Corpus evaluation and eligibility decision
-> reviewed deployment publication
-> immutable activation and public session
-> RouteDeck invocation and product projection
-> reviewed public write when requested
-> redacted interaction evidence
-> Corpus Operations and optional Evaluation intake
```

This flow is accepted for the Medusa ecommerce vertical through independent
Surface, Hybrid, and Chat journeys. Exact deployed evidence is owned by
`docs/superpowers/validation/2026-08-15-deployed-boundary-refactor.md`.

## Maintained gates

1. Pass the current Studio-to-RouteDeck mapping/parity gate before build
   compilation.
2. Publish only an exact eligible immutable build; never use the standalone
   proof catalogue as Corpus product storage.
3. Keep Corpus owner authorization and deployed-Agent public identities and
   sessions separate.
4. Package/resolve the exact product surface contract with the compiled Agent.
5. Preserve review, failure, retry, rollback, redaction, and activation lineage
   across every adapter.
6. Prove changes through focused delivery/runtime tests and the real Corpus
   deployment, public interaction, rollback, and Operations path.

## Claim limits

- The standalone 8880/5280 environment still proves only its own RouteDeck
  Medusa example and does not independently prove a Corpus-built Agent.
- Current Corpus persistence, Huey, and single-host topology are internal v0.1
  choices, not multi-host scaling or SLA evidence.
- Built-Agent isolation is logical and identity/state scoped, not hostile-code
  process/container isolation.
- Accepted Corpus evidence covers the Medusa ecommerce vertical, not every
  channel type, external API, or concurrency level.
- No RouteDeck change is implied. If a current public RouteDeck contract cannot
  represent a required compiled-Agent or projection boundary, stop and report
  the exact upstream gap.
