# OpenAPI ToolRouter: Product-Readiness Handoff Brief

Prepared for: ChatGPT Pro next-step discussion  
Reason: ChatGPT Pro could not access the branch, so this brief is self-contained.  
Repo root: `D:\Dev\AI Projects\agent-core`  
Benchmark folder: `D:\Dev\AI Projects\agent-core\research\openapi_toolrouter_benchmark`  
Current target: Medusa v2 Admin and Store OpenAPI specs

## 1. Current Direction

The project has been realigned from a pure graph-vs-RAG benchmark into a practical SaaStoAgent-style OpenAPI tool router.

It still keeps the research harness, but the product-readiness path is now the primary practical track:

- Route realistic natural user requests to OpenAPI endpoints.
- Return top-k candidates when confidence is not strong enough.
- Ask follow-up questions for missing params, ambiguity, or missing policy.
- Block destructive DELETE/delete-class calls unless explicitly confirmed.
- Log runtime feedback.
- Run an offline synthetic-feedback experiment separately from real feedback claims.

The low-overlap suite remains a research stress track. It should not drive the product headline.

## 2. Hard Boundaries

- OpenAPI specs are the routing source of truth.
- Repaired specs are validation artifacts only.
- Repaired specs do not replace raw specs for routing, graph, RAG, or task generation.
- No Medusa endpoint maps.
- No Medusa-specific routing rules.
- No action lexicons.
- No stopword lists.
- No GraphSAGE yet.
- Writes are dry-run only unless explicitly confirmed.
- Do not infer hidden business policy from OpenAPI.

## 3. Current CLI

Run from:

```powershell
cd D:\Dev\AI Projects\agent-core\research\openapi_toolrouter_benchmark
```

Main product-readiness flow:

```powershell
python -m toolrouter natural-tasks --artifacts artifacts/ --coverage data/medusa_task_coverage.json --task-prefix medusa_nat --out data/medusa_natural_tasks.json --min-count 100
python -m toolrouter recovery-tasks --artifacts artifacts/ --coverage data/medusa_task_coverage.json --task-prefix medusa_rec --out data/medusa_recovery_tasks.json
python -m toolrouter split-tasks --tasks data/medusa_natural_tasks.json --tasks data/medusa_recovery_tasks.json --out data/medusa_product_task_splits.json
python -m toolrouter benchmark --mode product_readiness --tasks data/medusa_natural_tasks.json --tasks data/medusa_recovery_tasks.json --artifacts artifacts/ --splits data/medusa_product_task_splits.json --synthetic-feedback --out results_product_readiness.json
python -m toolrouter report --results results_product_readiness.json --out reports/
```

Runtime route command:

```powershell
python -m toolrouter route --query "start a checkout for a shopper" --artifacts artifacts/ --feedback-log data/feedback_events.jsonl --feedback-model artifacts/feedback_ranker.joblib
```

Feedback ranker training:

```powershell
python -m toolrouter train-feedback --feedback data/feedback_events.jsonl --artifacts artifacts/ --out artifacts/feedback_ranker.joblib
```

Research low-overlap stress run remains separate:

```powershell
python -m toolrouter low-overlap-tasks --artifacts artifacts/ --coverage data/medusa_task_coverage.json --task-prefix medusa_low --out data/medusa_low_overlap_tasks.json --min-routing 100 --min-ambiguous 50 --min-policy 50
python -m toolrouter split-tasks --tasks data/medusa_low_overlap_tasks.json --out data/medusa_low_overlap_task_splits.json
python -m toolrouter benchmark --tasks data/medusa_low_overlap_tasks.json --artifacts artifacts/ --splits data/medusa_low_overlap_task_splits.json --out results_low_overlap.json
python -m toolrouter report --results results_low_overlap.json --out reports/low_overlap/
```

Latest verification:

```text
python -m pytest tests -q
35 passed
```

## 4. Product Tracks

### `natural_routing`

Primary product-readiness track. Tasks are realistic, short, deterministic user-like queries derived from OpenAPI metadata without passing endpoint IDs, provenance, resource, operation class, or task type to the router.

File:

- `data/medusa_natural_tasks.json`
- Current count: `100`

### `recovery_followup`

Follow-up quality track. These tasks are not mixed into one headline routing accuracy number.

Expected decision types:

- `ASK_PARAM`
- `ASK_DISAMBIGUATE`
- `ASK_POLICY`
- `BLOCK_UNSAFE`

File:

- `data/medusa_recovery_tasks.json`
- Current count: `85`

### `spec_close_smoke`

Endpoint-summary-like sanity tasks for pipeline debugging only.

### `low_overlap_stress`

Hard robustness benchmark. Report separately.

## 5. Decision Layer

Implemented decision types:

- `ROUTE`: high-confidence endpoint selection.
- `SHOW_TOPK`: medium confidence; return top 3 endpoint candidates with reasons.
- `ASK_PARAM`: endpoint is clear, but OpenAPI-required inputs are missing.
- `ASK_DISAMBIGUATE`: multiple endpoint families are plausible.
- `ASK_POLICY`: OpenAPI exposes possible actions but not the needed business policy.
- `BLOCK_UNSAFE`: destructive OpenAPI DELETE/delete-class endpoint needs confirmation.

Recent calibration slice changes:

- Added `toolrouter/product_calibration.py`.
- Product benchmark now creates or reads deterministic product splits.
- `DecisionConfig` is selected on dev rows only.
- Tuning grid covers:
  - `route_confidence_threshold`
  - `route_margin_threshold`
  - `param_confidence_threshold`
  - `show_topk_confidence_threshold`
  - `unsafe_write_threshold`
- Optimization order:
  - enforce false execution rate `<= 10%` when possible
  - maximize natural top1 route accuracy
  - maximize correct decision type
  - minimize false overclarification
  - deterministic config name tie-break
- Ranking and retrieval are computed once per query; threshold configs are applied over cached candidate contexts.
- Missing params now win over unsafe blocking.
- Unsafe blocking uses OpenAPI evidence only: DELETE method or `operation_class == "delete"`.
- Non-delete create/update dry-run candidates are not blocked just because they write.

Selected config from the latest product run:

```json
{
  "selected_from": "dev",
  "name": "route0.30_margin0.00_param0.00_topk0.18_unsafe0.20",
  "route_confidence_threshold": 0.3,
  "route_margin_threshold": 0.0,
  "param_confidence_threshold": 0.0,
  "show_topk_confidence_threshold": 0.18,
  "unsafe_write_threshold": 0.2
}
```

## 6. Decision Diagnostics

Every product detail row now includes:

- query
- expected decision type
- actual decision type
- expected endpoint
- selected endpoint
- top 3 candidates
- confidence
- margin
- missing params
- unsafe flag
- validation result
- stable decision reason

Stable `decision_reason` labels include:

- `policy_gap`
- `missing_required_inputs`
- `unsafe_unconfirmed_write`
- `low_confidence_topk`
- `low_margin_topk`
- `vague_query_disambiguation`
- `high_confidence_route`

Confusion matrix reporting includes the important pairs:

- `ROUTE` vs `SHOW_TOPK`
- `ROUTE` vs `ASK_PARAM`
- `ROUTE` vs `BLOCK_UNSAFE`
- `ASK_PARAM` vs `ASK_DISAMBIGUATE`
- `ASK_POLICY` vs `ASK_DISAMBIGUATE`

New report:

- `reports/decision_calibration.md`

## 7. Current Product Results

Generated result file:

- `results_product_readiness.json`

Generated product reports:

- `reports/product_readiness.md`
- `reports/natural_routing.md`
- `reports/recovery_followup.md`
- `reports/decision_calibration.md`
- `reports/feedback_learning.md`

Latest all-split product-readiness metrics:

| Split | Track | Tasks | Top1 route | Top3 recover | Top10 recall | Decision type | Follow-up type | Param questions | False execution | False overclarification | Validation |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| all | natural_routing | 100 | 72.0% | 92.0% | 100.0% | 68.0% | 0.0% | 0.0% | 0.0% | 32.0% | 59.0% |
| all | recovery_followup | 85 | 71.4% | 88.6% | 100.0% | 65.9% | 65.9% | 94.1% | 7.1% | 0.0% | 78.8% |

Latest held-out test metrics:

| Split | Track | Tasks | Top1 route | Top3 recover | Top10 recall | Decision type | Follow-up type | Param questions | False execution | False overclarification | Validation |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| test | natural_routing | 19 | 73.7% | 94.7% | 100.0% | 78.9% | 0.0% | 0.0% | 0.0% | 21.1% | 68.4% |
| test | recovery_followup | 22 | 75.0% | 87.5% | 100.0% | 68.2% | 68.2% | 95.5% | 13.6% | 0.0% | 81.8% |

Interpretation:

- Natural routing still clears the first product milestone:
  - top1 target `>= 50%`; current all-split value is `72.0%`.
  - top3 target `>= 75%`; current all-split value is `92.0%`.
  - top10 target `>= 90%`; current all-split value is `100.0%`.
  - false execution target `<= 10%`; current all-split value is `0.0%`.
- Decision calibration improved materially on natural routing from the earlier `38.0%` to `68.0%` all-split and `78.9%` test.
- Recovery follow-up improved from `60.0%` to `65.9%` all-split and `68.2%` test.
- Recovery false execution is still a risk: all-split is `7.1%`, but held-out test is `13.6%`, which exceeds the desired 10% ceiling.
- Natural false overclarification worsened from `18.0%` to `32.0%` all-split because false overclarification is now stricter and counts any non-`ROUTE` decision on expected-route tasks.

## 8. Synthetic Feedback Experiment

Synthetic feedback is an offline experiment only. It is generated from benchmark corrections and must not be presented as real runtime feedback.

Generated files:

- `data/synthetic_feedback_events.jsonl`
- `artifacts/synthetic_feedback_ranker.joblib`
- `artifacts/synthetic_feedback_ranker.manifest.json`

Latest experiment:

- Synthetic event count: `185`
- Model status: `trained`
- Source label: `synthetic_offline`

All-split before/after:

| Track | Metric | Before | After |
|---|---|---:|---:|
| natural_routing | top1 route | 72.0% | 62.0% |
| natural_routing | top3 recover | 92.0% | 90.0% |
| natural_routing | top10 recall | 100.0% | 99.0% |
| natural_routing | decision type | 68.0% | 57.0% |
| recovery_followup | decision type | 65.9% | 68.2% |
| recovery_followup | follow-up type | 65.9% | 68.2% |
| recovery_followup | false execution | 7.1% | 4.7% |

Interpretation:

- Synthetic feedback helps recovery decision type slightly and reduces recovery false execution.
- Synthetic feedback hurts natural routing top1 and decision calibration in this run.
- This suggests the feedback ranker needs better split discipline or task-family balancing before it should influence product routing by default.

## 9. Feedback Learning

Real runtime feedback log schema:

- `data/feedback_events.jsonl`

Runtime events include:

- query
- decision type
- top candidates
- selected endpoint
- confidence
- missing params
- follow-up question
- user-selected endpoint
- corrected endpoint
- rejected endpoints
- validation result
- execution result
- timestamp
- source

Feedback ranker:

- Local scikit-learn model.
- Output model: `artifacts/feedback_ranker.joblib`
- Output manifest: `artifacts/feedback_ranker.manifest.json`
- If feedback lacks both positive and negative labels, training returns `model_status=insufficient_data`.

Feature surface:

- `rag_score`
- `bm25_score`
- `graph_sparse_score`
- `grag_score`
- `schema_param_match`
- `operation_class_confidence`
- `resource_overlap`
- `path_token_overlap`
- `auth_required_param_compatibility`
- `previous_successful_usage_count`
- `previous_correction_count`
- `previous_rejection_count`

Current real feedback status:

- Runtime feedback events observed: `0`
- Runtime feedback model status: `not_loaded`

## 10. Research Harness Still Present

Existing research infrastructure remains:

- RAG endpoint-only and all-doc TF-IDF baselines.
- BM25 all-doc baselines.
- `graph_text` ablation.
- `graph_sparse` sparse propagation.
- GRAG baselines: `grag_expand`, `grag_rerank`, `grag_constrained`.
- Dev-selected hybrid.
- Learned feature ablations.
- Deterministic train/dev/test and leave-domain-out splits.
- Leakage audit.
- Task audit.
- Strict OpenAPI validation and repaired validation specs.

Low-overlap stress remains separate:

- `200` tasks total.
- `100` low-overlap routing tasks.
- `50` ambiguous abstention tasks.
- `50` policy-required abstention tasks.
- Earlier mixed headline complete score was `50%` because abstention-required tasks pass.
- Earlier routing-only complete@1/@10 under low-overlap stress was `0%`.

## 11. Important Modules

- `toolrouter/openapi_loader.py`: OpenAPI loading, repair artifact integration, normalized endpoint catalog.
- `toolrouter/tasks.py`: spec-close, natural, recovery, and low-overlap task generation.
- `toolrouter/decision_router.py`: product ranking context, decision layer, product metrics, optional feedback model scoring.
- `toolrouter/product_calibration.py`: dev-only decision config tuning, confusion rows, calibration rows, synthetic feedback generation.
- `toolrouter/feedback.py`: feedback event schema, feedback stats, scikit-learn model training/loading/inference.
- `toolrouter/retrieval_indices.py`: TF-IDF, BM25, graph sparse, graph utilities, doc-to-graph mapping.
- `toolrouter/router_baselines.py`: research ranking baselines and GRAG scoring.
- `toolrouter/evaluator.py`: research metrics.
- `toolrouter/reports.py`: research reports and product-readiness reports.
- `toolrouter/__main__.py`: CLI.

## 12. Recommended Next Slice

The next product risk is not top-k candidate recall. It is decision and recovery reliability.

Recommended next priorities:

1. Reduce recovery false execution on held-out test below 10% without damaging natural routing.
2. Improve `ASK_PARAM` vs `ASK_DISAMBIGUATE` separation using only OpenAPI-derived missing input evidence.
3. Improve natural false overclarification while keeping false execution at or below 10%.
4. Add better calibration plots or threshold tables from `decision_calibration.md`.
5. Improve synthetic feedback so it does not degrade natural routing before enabling it in product routing.
6. Keep low-overlap stress separate and do not optimize retrieval until decision quality stabilizes.

Do not add GraphSAGE yet.

## 13. Prompt For ChatGPT Pro

```text
I have a local OpenAPI ToolRouter project at:
D:\Dev\AI Projects\agent-core\research\openapi_toolrouter_benchmark

It ingests Medusa v2 Admin and Store OpenAPI specs and builds routing artifacts from raw OpenAPI only. Repaired specs are used only for strict validation. There are no Medusa endpoint maps, no Medusa routing rules, no action lexicons, no stopword lists, and no GraphSAGE.

The project was realigned from a pure graph-vs-RAG benchmark into a practical SaaStoAgent-style API tool router.

Current product features:
- deterministic natural task generation
- recovery follow-up task generation
- product decision layer: ROUTE, SHOW_TOPK, ASK_PARAM, ASK_DISAMBIGUATE, ASK_POLICY, BLOCK_UNSAFE
- dev-selected DecisionConfig
- per-task decision calibration diagnostics
- decision confusion matrix
- top-k candidate output with reasons
- required param/body field follow-up questions
- policy gap detection
- DELETE/delete-class unsafe blocking only from OpenAPI evidence
- runtime route command
- feedback_events.jsonl schema
- local scikit-learn feedback ranker
- offline synthetic-feedback experiment
- product reports separated from research reports

Latest all-split Medusa product-readiness results:
- natural_routing: 100 tasks
- natural top1 route accuracy: 72.0%
- natural top3 recoverability: 92.0%
- natural top10 candidate recall: 100.0%
- natural correct decision type: 68.0%
- natural false execution: 0.0%
- natural false overclarification: 32.0%

Recovery follow-up:
- 85 tasks
- correct decision type: 65.9%
- correct follow-up type: 65.9%
- required param question accuracy: 94.1%
- false execution: 7.1% all-split, but 13.6% on held-out test

Synthetic feedback:
- 185 offline events
- model trained
- helped recovery slightly but hurt natural routing, so it should remain an experiment for now.

The low-overlap suite is still present as a research stress track, but it is no longer the product-readiness headline.

Please review this as a practical SaaStoAgent API routing system. What should the next slice prioritize to improve decision and recovery reliability without changing retrieval: stricter unsafe calibration, ASK_PARAM vs ASK_DISAMBIGUATE separation, natural false-overclarification reduction, feedback ranker balancing, or better decision calibration diagnostics?
```

## 14. Bottom Line

The practical router clears the initial natural-routing milestone. Decision calibration improved substantially, and follow-up quality improved modestly. The main remaining product issue is recovery reliability: held-out recovery false execution is still above the 10% target. Retrieval should stay frozen until decision and recovery behavior are stable.
