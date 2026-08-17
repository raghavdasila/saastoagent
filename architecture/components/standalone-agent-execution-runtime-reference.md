# Agent Execution Runtime Integration Reference

Updated: 2026-08-17

## Purpose and authority

`D:\Dev\AI Projects\agent-execution-runtime` remains a separately owned
package and standalone proof environment for the agent-to-tool-to-API execution
and evidence boundary. That repository owns its package implementation,
commands, contracts, standalone evidence, and limitations.

Corpus now installs pinned `agent-execution-runtime==0.1.0` source into its
backend/worker image and consumes it behind Corpus-owned application and
integration adapters. The standalone Studio is still optional and is not a
separate Corpus service. Its proof artifacts do not independently prove the
Corpus browser path.

Canonical source is the private repository
`https://github.com/saastoagent/agent-execution-runtime` at the exact commit
recorded in
`contracts/dependency-provenance/development-source-checkouts.json`.

## Proven standalone capabilities

- immutable, content-hashed agent builds with exact model, connection,
  OpenAPI-revision, operation, limit, and write-authorization identity;
- catalogue and explicit build assembly over approved OpenAPI revisions with
  advisory ToolRouter recommendations;
- real model intent decisions, ToolRouter routing/clarification, and
  capability-scoped API execution;
- parallel calls, tenant/session isolation, durable reload, restart/resume,
  cancellation, and visible failure semantics;
- redacted chronological records, run-to-evaluation promotion, exact-build
  evaluation, reviewer evidence, and deployment eligibility.

The standalone repository's `docs/corpus-behavior-coverage.md` and
`test_index/README.md` own its detailed matrix and proof limits.

## Current Corpus integration

| Corpus owner | Package boundary | Current adapter behavior |
| --- | --- | --- |
| Sources / API revision | OpenAPI and connection revision identities | Corpus resolves an approved immutable Source revision and credential without exposing feature persistence to the runtime. |
| Agent Builder | build input and immutable Agent Build | Corpus owns Agent/build lifecycle and durable jobs; the package owns deterministic build contents and hashes. |
| Sandbox and hosted Agent | run command and projection | Corpus authorizes owner/public sessions and maps opaque tenant/session scope through `corpus.app.agent_runtime_adapters`. |
| API execution | model request, ToolRouter decision, and API executor ports | Corpus composes its ToolRouter and reviewed `RoutedApiExecutionAdapter`; RouteDeck policy and build authority constrain the exact operation before one API request. |
| Evaluation | run promotion, evaluation case/run, and eligibility | Corpus owns evaluation definitions and presentation; the package supplies exact-build execution evidence through Corpus-owned adapters. |
| Operations | redacted execution projections | Corpus authorizes and presents runtime evidence without exposing credentials, unrestricted bodies, or provider objects. |
| Deployment | eligibility evidence | Corpus owns deployment legality, review, publication, activation, and rollback. Eligibility never deploys by itself. |

The application composition owners are
`backend/src/corpus/app/agent_product_runtime.py`,
`backend/src/corpus/app/agent_runtime_adapters.py`, and
`backend/src/corpus/app/agent_runtime_store.py`. Feature packages depend on
neutral contracts under `corpus.shared`, not on package persistence or app
composition.

## Maintained gates

1. Preserve the Studio-to-RouteDeck mapping/parity gate before compiling a
   product-approved Agent Build.
2. Keep Corpus principal/conversation authorization, feature persistence, and
   durable job ownership outside the execution package.
3. Keep ToolRouter ranking separate from RouteDeck authority and API execution;
   no layer may silently grant an operation.
4. Keep package persistence and provider objects behind Corpus-owned adapters.
5. Prove runtime changes through focused package/adapter tests and the real
   Corpus Builder, Sandbox, Evaluation, hosted-Agent, and Operations path.
6. Preserve visible failure, explicit review, exact lineage, and no-fallback
   semantics.

## Claim limits

- Standalone package proof is not fresh Corpus integration proof.
- The accepted Corpus evidence covers the Medusa ecommerce vertical, not every
  API definition or model/provider combination.
- Agent isolation is currently logical and identity/state scoped on a shared
  backend/worker host; it is not hostile-code, process, container, or quota
  isolation.
- Local Ollama, SQLite, and standalone proof UIs remain development choices,
  not production topology or SLA evidence.
- The Medusa 2.13.6 response correction is an explicitly selected Corpus
  acceptance adapter, not a generic package fallback.
