# 2026-07-23 ToolRouter Integration

## Scope

Implement the first launch milestone's Source foundation without deciding
Agent Designer: generic Sources, API collection connector, proven ToolRouter
OpenAPI normalization, resource-first semantic graph/GRAG retrieval, evalset
generator/reviewer, and an owner-only debug surface. Preserve concurrent
auth/UI work and commit the earlier feature-behavior notebook separately.

## Git Boundary

- Earlier notebook-only commit: `2e2a3d9 docs: add Corpus feature behavior
  notebook`.
- Commit paths: `docs/README.md`, behavior notebook HTML/notes, notebook server,
  and its unit test only.
- ToolRouter/Sources implementation was not committed during this run because
  the checkout also contains concurrent auth/UI changes; no unrelated files
  were staged or swept into the notebook commit.

## Implemented Subsystems

- **ToolRouter integration:** exact namespaced 24-module snapshot plus recipe,
  source hashes/provenance, pinned dependencies, settings/contracts/errors,
  atomic graph/index serialization, and one facade for ingest/retrieve/evalset.
- **Sources backend:** owner-scoped source/revision repository, connector
  protocol, API connector/intake, neutral contracts/errors, lifecycle service,
  same-origin authenticated HTTP, one RouteDeck node, and navigation bindings.
- **Sources frontend:** typed client and owner debug workbench for upload,
  inventory, metrics, retrieval trace, and real evalset evidence.
- **Composition/setup:** Source settings, app composition, local setup, pinned
  MiniLM cache, Gemma/Qwen readiness, and local runner compatibility.
- **Documentation:** requirements, completed plan, component ownership, ADR,
  flow index, code map, validation index, context, log, and checkpoint.

## Upstream Reference Evidence

Source checkout:
`D:\Dev\AI Projects\openapi-toolrouter-benchmark`

Source identity: main `2611801e`, dirty snapshot. Exact bytes are identified by
`backend/src/corpus/integrations/toolrouter/source_manifest.json`.

Focused reference command:

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

Real reference probe: Ory Kratos v26.2.0, 56 endpoints, 477 graph nodes,
876 edges, 477 cards; `create a new identity` produced
`ASK_DISAMBIGUATE`, led by `api:createRecoveryLinkForIdentity`.

## Real Corpus Product Evidence

Runtime location: local Windows checkout only.

Commands:

```powershell
.\scripts\run-backend.ps1
.\scripts\run-frontend.ps1
```

URLs:

- Backend readiness: `http://127.0.0.1:8099/readyz` -> 200 ready.
- Product: `http://127.0.0.1:5199/`.
- Authenticated workbench: `http://127.0.0.1:5199/sources` through RouteDeck.

Real upload:

`D:\Dev\AI Projects\openapi-toolrouter-benchmark\data\evalset_factory\blind\ory_kratos_v26.2.0\source\api.json`

Observed product result:

- validation `valid`, zero repairs;
- 56 endpoints, 316 schemas, two security schemes;
- 477 graph nodes, 876 edges, 477 cards;
- pinned MiniLM revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, CPU, local-files-only.

Retrieval query `create a new identity`:

| Rank | API operation | Score |
| --- | --- | ---: |
| 1 | `api:createRecoveryLinkForIdentity` | 0.4280 |
| 2 | `api:createRecoveryCodeForIdentity` | 0.4259 |
| 3 | `api:createIdentity` | 0.4217 |
| 4 | `api:deleteIdentitySessions` | 0.4177 |
| 5 | `api:deleteIdentity` | 0.4171 |

Decision: `ASK_DISAMBIGUATE`; reason: `low_score_margin`. A hard page reload
restored the source and graph counts, and retrieval succeeded again from the
persisted artifacts.

Real evalset run `api-debug-v1`:

- completed 1/1;
- accepted 1, quarantined 0;
- 2,936 offline tokens;
- accepted query: `Can you show me all the sessions for a specific identity?`;
- selected truth: `api:listIdentitySessions`;
- generator `gemma4:latest`, digest
  `c6eb396dbd5992bbe3f5cdb947e8bbc0ee413d7c17e2beaae69f5d569cf982eb`;
- reviewer `qwen2.5-coder:7b`, digest
  `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`.

The run retained candidates, reviews, generation/review audits, progress,
manifest, JSON/Markdown summary, token ledger, accepted tasks, and accepted
manifest under:

`D:\Dev\AI Projects\saastoagent-v0.1\.runtime\sources\0277396694bae804\3ZChPkMRJQH1_CMB\r\gLpNIgzaYM4wIiS_\a\e\97f14f945cfd07865fc0`

The accepted output is a model-generated, independently reviewed candidate;
this evidence does not claim human-gold quality.

Rendered checks covered desktop and 390x844, upload busy/ready states,
inventory, graph counts, retrieval, reload, responsive horizontal navigation,
and empty browser warning/error logs.

## Automated Closeout

```powershell
.\.venv\Scripts\python.exe -m pytest backend\tests -q
# 52 passed, one Starlette/httpx deprecation warning

.\.venv\Scripts\python.exe -m pip check
# No broken requirements found.

pnpm --dir frontend test
# 6 files, 19 tests passed

pnpm --dir frontend typecheck
# passed

pnpm --dir frontend build
# passed; non-failing >500 kB chunk advisory

python -m unittest discover -v
# 12 passed
```

```powershell
python scripts\validate_design_notebook.py
# passed: 15 features, 53 nodes, 146 edges, zero missing targets

python scripts\check_doc_coverage.py
# exit 0 with zero unmatched-file warnings
```

## Boundaries And Unresolved Work

- Agent Designer planner/executor behavior is intentionally undecided.
- Sandbox pretend-action execution, public Web, Operations, and deployment are
  not implemented here.
- Background workers, production/object storage, multi-worker execution, and
  remote models are not proven.
- The ToolRouter source repository has no root license. The snapshot is an
  internal same-owner transfer and must not be externally redistributed until
  licensing is explicit.
- Semantic GRAG remains experimental.

## Next Step

Use the neutral `SourceService`/Source contracts while reconciling Agent
Designer behavior and agent configuration. Do not let Agent Designer import
ToolRouter or API-connector internals.
