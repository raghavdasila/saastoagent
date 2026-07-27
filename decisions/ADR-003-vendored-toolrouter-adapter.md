# ADR-003: Vendored ToolRouter Behind A Sources Connector Adapter

Status: accepted and locally validated

Date: 2026-07-23

## Context

The authoritative ToolRouter work lives in
`D:\Dev\AI Projects\openapi-toolrouter-benchmark`. Corpus needs its OpenAPI
normalization, resource-first semantic graph/GRAG retrieval, and evalset
generator/reviewer now, but Agent Designer is deliberately deferred. Corpus
also needs Sources to support future connector families whose retrieval and
evalset semantics are not OpenAPI.

Importing the sibling checkout would make deployment depend on a mutable local
path. Copying its modules directly into the Sources feature would make API
semantics generic, leak engine contracts throughout the product, and make a
later GRAG replacement invasive. The upstream checkout was also dirty and had
no root license, so a commit ID alone was insufficient provenance.

## Decision

- Keep **Sources** as the only product feature/node. API is connector key
  `api` under `features/sources/connectors/api/`.
- Copy the exact 24-module ToolRouter dependency closure and v1 recipe pack
  into `corpus.integrations.toolrouter.engine`.
- Record the sibling path, remote, branch, commit `2611801e`, dirty-state
  qualifier, and exact per-file source/copied SHA-256 values.
- Expose the snapshot only through `ToolRouterAdapter.ingest`, `retrieve`, and
  `generate_evalset` plus immutable integration contracts and explicit error
  categories.
- Keep `ApiSourceConnector` dependent on an `ApiSourceEngine` protocol. An
  explicit `connectors/api/toolrouter.py` bridge translates ToolRouter values
  once into generic Sources contracts. No generic Sources file or core API
  connector imports ToolRouter.
- Keep API upload configuration/HTTP inside the API connector and all
  embedding, Ollama, generator/reviewer, and timeout values inside
  `ToolRouterSettings`. Host composition constructs these boundaries without
  copying their settings into generic Sources.
- Persist normalized input, graph, embeddings, traces, evalset audits, model
  digests, token ledger, quarantine, and accepted exports below the owning
  source revision.
- Use only the pinned local MiniLM revision and explicit local Ollama Gemma/Qwen
  models. Missing dependencies or artifacts fail; no provider fallback exists.
- Label semantic GRAG experimental and factory output reviewed candidates, not
  human gold.

## Alternatives Considered

### Runtime import from the sibling checkout

Rejected. It would make the application non-self-contained and allow sibling
working-tree changes to alter Corpus behavior without a Corpus diff.

### Put copied modules inside `features/sources/connectors/api`

Rejected. The connector should translate API product semantics, not own a
large replaceable algorithm implementation. Keeping the integration sibling to
features allows Sandbox/Evaluation to use a future approved facade without
reaching through Sources internals.

### Reimplement or simplify ToolRouter

Rejected for this milestone. The user asked to bring the proven parser, graph,
retrieval, and evalset factory as-is; changing algorithms while defining the
boundary would erase the existing evidence baseline.

### Adopt a new parsing or embedding dependency

Rejected. Prance/OpenAPI validators and Sentence Transformers/MiniLM are the
actual upstream reference path. FastEmbed and direct Transformers were viable
embedding alternatives but would change retrieval behavior before the adapter
boundary was proven.

## Consequences

- Corpus is deployable without the sibling ToolRouter checkout, while the
  copied bytes remain auditable and replaceable.
- Generic Source identity, storage, list/get/retrieve/evalset HTTP, RouteDeck
  behavior, and frontend contracts remain free of endpoint-specific contracts.
- Upstream changes require an intentional snapshot replacement, manifest
  update, focused upstream proof, adapter regression suite, and real product
  rerun.
- The copied source cannot be redistributed outside Corpus until upstream
  licensing is explicit. Dependency licenses remain their own.
- The current local filesystem implementation is a launch/debug boundary, not
  a production object-store or worker design.

## Validation

- Upstream focused suite: 79 passed.
- Corpus backend suite: 52 passed, including provenance, ingestion, artifact
  reload, retrieval, evalset, Source isolation, HTTP, and RouteDeck contracts.
- Frontend suite: 19 passed; strict typecheck and production build passed.
- Real Ory Kratos upload: 56 endpoints, 477 graph nodes, 876 edges, 477 cards.
- Real GRAG query and post-reload query returned the same explicit
  `ASK_DISAMBIGUATE` decision and ranking.
- Real Gemma/Qwen factory run completed one candidate, accepted one,
  quarantined zero, and retained 2,936 offline-token evidence.
