# Standalone Agent Execution Runtime Reference

## Purpose and authority

`D:\Dev\AI Projects\agent-execution-runtime` is a separately built proof of the
agent-to-tool-to-API execution and evidence boundary. That repository owns its
implementation, commands, contracts, evidence, and limitations. Corpus does not
currently import it, invoke it, or depend on it at runtime.

This document records the intended integration seam only. It does not authorize
a Corpus or RouteDeck implementation change.

## Proven standalone capabilities

- immutable, content-hashed agent builds with exact model, connection,
  OpenAPI-revision, operation, limit, and write-authorization identity;
- catalogue and explicit build assembly over approved OpenAPI revisions with
  advisory ToolRouter recommendations;
- real Ollama intent decisions, ToolRouter route/ambiguity/missing-parameter
  decisions, and capability-scoped API execution;
- real Medusa read, preauthorized write and read-after-write evidence;
- parallel calls across two APIs, tenant/session isolation, durable reload,
  restart/resume and cancellation;
- visible invalid credentials, schema drift, and unknown-write outcomes without
  automatic retry;
- redacted chronological records, run-to-evaluation promotion, exact-build
  evaluation, independent reviewer evidence, and deployment eligibility;
- a replaceable browser proof Studio using only public application commands and
  projections.

The complete behavior matrix and claim limits remain owned by the standalone
repository's `docs/corpus-behavior-coverage.md` and `test_index/README.md`.

## Intended Corpus integration points

| Corpus owner | Standalone boundary | Required adapter behavior |
| --- | --- | --- |
| Agent Designer and RouteDeck mapping | Neutral build-assembly input | Corpus first completes the mandatory accepted-Studio-design to existing-RouteDeck-contract mapping. A Corpus host adapter then translates only compiled, product-approved values; RouteDeck IDs never enter runtime contracts. |
| Sources / API revision | OpenAPI and connection revision identities | Corpus owns source upload, revisions, approval, credentials, and authorization. The adapter resolves an approved immutable artifact without exposing the Corpus database. |
| Agent Builder | `BuildAssemblyCommand` and immutable `AgentBuild` | Corpus owns agent lifecycle and async job state; the runtime owns deterministic build contents and hashes. |
| Owner conversation and Sandbox | `RunCommand` and `RunProjection` | Corpus authenticates the principal and authorizes the public conversation before mapping opaque tenant/session scope. Runtime identifiers are not credentials. |
| Evaluation | run promotion, `EvalCase`, `EvalRun`, eligibility | Corpus owns evalset management and review surfaces; the runtime owns exact-build execution evidence. |
| Operations | redacted durable execution records/projections | Corpus authorizes and presents activity. Deployed-channel retention and indexing remain Corpus-owned. |
| Deployment | `EligibilityDecision` as input evidence | Corpus owns deployment legality, publishing, activation and rollback. Eligibility never deploys. |

## Required gates before integration

1. Inspect the current RouteDeck contracts read-only and pass the mandatory
   Studio mapping/parity gate. Stop on missing mappings.
2. Replace development-only local ToolRouter and API Runtime paths with approved
   package/artifact boundaries.
3. Define a Corpus-owned adapter and serialization conformance suite. Do not
   import proof UI, LangGraph state, ToolRouter objects, API-runtime classes, or
   SQLite stores.
4. Add Corpus principal/conversation authorization and durable background-job
   ownership outside the execution domain.
5. Prove the real Corpus browser path through build, Sandbox, evaluation, and
   Operations. Standalone proof is not Corpus integration proof.

## Known blockers and claim limits

- No accepted RouteDeck-design-to-`AgentBuild` compiler exists.
- No Corpus host/auth/conversation adapter or background worker exists.
- Channels, deployment, and deployed/public Operations are not implemented by
  the standalone runtime.
- The local ToolRouter subprocess and API Runtime editable reference are
  development-only and non-releaseable.
- Real Medusa `GetProducts` returns HTTP 200, but the currently approved OpenAPI
  response schema rejects its shape. This remains visible until a user approves
  an effective contract revision.
