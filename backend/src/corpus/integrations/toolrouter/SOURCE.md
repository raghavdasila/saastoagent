# ToolRouter Engine Source

The private `engine/` package is a mechanical source snapshot from:

- checkout: `D:\Dev\AI Projects\openapi-toolrouter-benchmark`
- remote: `https://github.com/raghavdasila/openapi-toolrouter-benchmark.git`
- branch: `main`
- source HEAD: `2611801e docs: add semantic graph retrieval handoff`
- snapshot state: dirty working tree on 2026-07-23

The dirty-state qualifier matters: current evalset factory and semantic-GRAG
files were not all committed in the source checkout. `source_manifest.json`
therefore records the exact source and copied SHA-256 for every transferred
module. Replacement work must compare bytes, not assume that source HEAD alone
identifies this snapshot.

## Corpus Runtime Adaptation

The manifest records Corpus-owned runtime adaptations whose vendored hashes
differ from the source snapshot. The generator and reviewer accept an
operator-configured HTTP Ollama hostname with an explicit port. The experiment
and reviewer also accept an explicit same-model review policy so the Corpus
adapter can run separate generation and review calls through one selected
OpenAI model. The default remains independent Ollama models. Provider selection
is explicit, failures remain explicit, and no provider or model fallback is
added. The semantic-review schema omits JSON Schema `uniqueItems`, which the
OpenAI strict structured-output subset rejects, and preserves the uniqueness
invariant by rejecting duplicate endpoint IDs after parsing. The deployed
`gpt-5.6-luna` Responses reference call and a focused duplicate-output test
both cover this Corpus-owned compatibility adaptation.

## Included Boundary

The 24-module closure plus the versioned v1 recipe pack contains OpenAPI ingestion/repair, resource-first semantic
graph construction/conformance, local embedding retrieval, the semantic GRAG
router and outcomes, the evalset generator/reviewer/experiment/export modules,
and only the local helpers those modules import.

Benchmark datasets, reports, scripts, visualizers, GNN research, provider
selectors, and sibling-repository paths are not copied and are not runtime
dependencies.

## Reference Proof Before Copy

Local source environment: Python 3.11.9.

```powershell
.\.venv\Scripts\python.exe -m pytest `
  tests\test_openapi_loader.py `
  tests\test_semantic_schema_graph.py `
  tests\test_semantic_graph.py `
  tests\test_semantic_graph_retrieval.py `
  tests\test_semantic_grag_router.py `
  tests\test_evalset_factory_contracts.py `
  tests\test_evalset_factory_seed.py `
  tests\test_evalset_factory_generation.py `
  tests\test_evalset_factory_validation.py `
  tests\test_evalset_factory_experiment.py `
  tests\test_evalset_factory_export.py -q
```

Result: `79 passed in 3.32s`.

A real local Ory Kratos v26.2.0 source then completed:

```text
OpenAPI load -> resource_first_v1 graph -> local MiniLM index -> GRAG route
56 endpoints, 477 nodes, 876 edges, 477 cards
query: create a new identity
decision: ASK_DISAMBIGUATE
top endpoint: api:createRecoveryLinkForIdentity
```

Runtime was local Windows. MiniLM used the already-cached model revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41` on CPU. No alternate provider or
fixture replaced the reference path.

## License Boundary

The source repository has no root license file. This is an internal same-owner
source transfer. Do not redistribute the copied engine outside the Corpus
repository until the upstream repository has an explicit license. The selected
Sentence Transformers library and MiniLM model are Apache-2.0; dependencies
retain their own licenses.
