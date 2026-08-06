# Standalone Agent Delivery Runtime integration

Status: proven independently; not imported into or invoked by Corpus

Standalone authority: `D:\Dev\AI Projects\agent-delivery-runtime`

## Purpose

The standalone runtime proves the isolated delivery provider needed after an
agent is already compiled and eligible: immutable deployment revisions,
activation and rollback, a hosted Web channel, deployment-pinned public
sessions, real RouteDeck execution, redacted interaction evidence, and
evaluation-candidate export.

It does not compile Corpus Agent Designer state, build an agent, authorize a
Corpus owner, or render Corpus-owned product components. Running it beside
Corpus is module proof, not Corpus integration proof.

## Ownership and integration points

| Corpus owner | Standalone boundary | Required Corpus integration |
| --- | --- | --- |
| Agent Designer and RouteDeck mapping | No direct boundary; Delivery accepts an already compiled bundle | Corpus must first pass the accepted Studio design to current RouteDeck contract mapping/parity gate. Delivery must never compile or reinterpret Studio state. |
| Agent Builder | Trusted immutable deployable bundle | Replace the proof-only Medusa bundle catalogue with a Corpus-authorized artifact publisher/reader. Preserve exact content, RouteDeck app, surface-contract, and eligibility identities. |
| Owner identity | `OwnerIdentityPort` and authenticated control APIs | Supply Corpus owner authorization through a narrow adapter. The local bearer-token file and standalone owner UI are proof infrastructure, not product identity. |
| Channels/Web | Channel create, enable/disable, public slug, session and projection APIs | Corpus owns channel configuration and product-facing management UI. Delivery owns hosting state and public session lifecycle. Deployed-agent users remain separate from Corpus owners. |
| Deployment | Deployment request/status, verification, activation, retry and rollback | Corpus submits only an authorized immutable bundle ID and presents status. Delivery owns queue claims, compatibility checks and transaction-safe activation. Eligibility failure must remain visible. |
| RouteDeck runtime | `DeployedAgentRuntimePort` | A production adapter must provision and invoke the exact compiled agent through public RouteDeck contracts. RouteDeck continues to own agent state, operations, surfaces and terminal execution semantics. |
| Product Web rendering | RouteDeck message/surface/suggested-action projection | The bundle must provide its matching frontend surface registry and private-form/review components. Delivery transports projections but does not copy Corpus components. |
| Operations | Redacted interaction records and detail projections | Corpus owns owner authorization, search/presentation, retention and review workflow. Delivery owns delivery/runtime evidence and must not expose provider objects, credentials or unrestricted bodies. |
| Evaluation | `delivery-runtime.v1` evaluation-candidate export | Corpus Evaluation must ingest through a versioned adapter, retain deployment/build lineage and decide whether the candidate enters an evalset. Export alone is not evaluation. |
| Persistence and work queue | `DeliveryStorePort` and `DeploymentJobPort` | SQLite and Huey are local adapters. Production topology, durability, tenancy, backup and scaling require separately approved adapters without changing domain contracts. |

## Intended product flow

```text
accepted Corpus design
-> compiled RouteDeck agent and product surface bundle
-> immutable Corpus Agent Build
-> Corpus evaluation and eligibility decision
-> authorized Delivery bundle publication
-> Delivery verification and activation
-> public Web session pinned to one activation
-> RouteDeck invocation and product projection
-> redacted Delivery interaction evidence
-> Corpus Operations and optional Evaluation intake
```

## Adoption gates

1. Pass the mandatory current Studio-to-RouteDeck mapping/parity gate.
2. Define the Corpus Agent Build and deployable artifact schema; do not reuse
   the proof-only Medusa catalogue as product storage.
3. Define a versioned Corpus adapter for control commands, public channel
   projections, Operations evidence and evaluation candidates.
4. Replace local token identity with Corpus authorization while keeping
   deployed-agent identity and sessions separate from Corpus owner sessions.
5. Package and verify the exact product frontend surface registry alongside
   the compiled RouteDeck agent.
6. Select approved persistence, queue, secret, public-hosting and observability
   adapters. Preserve fail-closed behavior and immutable activation lineage.
7. Prove the real Corpus browser path from eligible Agent Build through Web
   deployment, public interaction, rollback and Operations.

## Current blockers and claim limits

- Corpus has no Agent-Build-to-Delivery artifact publisher or host adapter.
- The standalone trusted catalogue contains only the verified local Medusa
  proof bundle.
- Corpus owner authentication is not connected to Delivery control APIs.
- Corpus product surface/private-form/review rendering is not packaged into the
  standalone public host.
- Delivery interaction export is not ingested by Corpus Operations or
  Evaluation.
- Local SQLite, Huey, loopback Vite and the generated token are development
  proof choices, not production hosting decisions.

No RouteDeck change is implied by this document. If the current RouteDeck
contracts cannot represent a required compiled-agent or projection boundary,
stop and report the exact upstream gap before implementation.
