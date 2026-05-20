# OpenAPI ToolRouter Staged Accuracy And Autonomy Ladder Plan

## Summary

Build an experiment ladder in `research/openapi_toolrouter_benchmark` that advances the router one technique at a time from the current `product_readiness` baseline through calibration, validation, conversation context, LLM-assisted routing, feedback learning, autonomy gating, dense retrieval, and finally GraphSAGE. Each stage gets its own immutable experiment folder, before/after metrics, guardrail audit, promotion decision, and cumulative rollup.

The first implementation slice should add the ladder infrastructure plus Stage 0 baseline lock. Later stages must only start after the previous stage is reported and classified as `promote`, `keep_as_ablation`, or `discard`.

## Key Changes

- Add an experiment harness with a stable CLI:
  - `python -m toolrouter experiment-run --stage stage0_baseline_lock --artifacts artifacts/ --natural-tasks data/medusa_natural_tasks.json --recovery-tasks data/medusa_recovery_tasks.json --low-overlap-tasks data/medusa_low_overlap_tasks.json --splits data/medusa_product_task_splits.json --out experiments/`
  - `python -m toolrouter experiment-report --experiments experiments/ --out reports/autonomous_router_ladder.md`
- Each run creates `experiments/YYYYMMDD_<stage>/` and `reports/experiments/<stage>/` with:
  - `summary.md`
  - `metrics.csv`
  - `failure_cases.csv`
  - `query_diagnostics.jsonl`
  - `decision_confusion_matrix.csv`
  - `guardrail_audit.md`
  - `promotion_decision.json`
  - `artifact_hashes.json`
  - `stage_config.json`
- Add a shared metric schema so every stage reports natural routing, recovery/follow-up, autonomy, learning, validation, latency, and label-quality fields even when a field is not yet enabled. Non-enabled metrics should be reported as `null` with `metric_status=not_enabled`, not silently omitted.
- Add a guardrail config file, `data/router_guardrails.json`, used by all stages:
  - `false_execution_limit: 0.10`
  - `write_modes: observe | suggest | dry_run | auto_read | confirm_write | block_write`
  - GET/HEAD/OPTIONS may become `auto_read` only when confidence, validation, and guardrail checks pass.
  - POST/PATCH/PUT stay dry-run or confirmation-gated unless explicitly allowed.
  - DELETE/delete-class endpoints stay confirmation-gated or blocked.
  - policy-required, missing-param, and validation-failed cases never auto-execute.
- Add a hardcoding audit to every experiment:
  - scan reusable `toolrouter/*.py` for Medusa endpoint maps, Medusa routing rules, action lexicons, stopword lists, hidden business-policy inference, and GraphSAGE before Stage 10.
  - report findings in `guardrail_audit.md`.
  - do not block Stage 0 baseline lock on existing findings; block promotion for newly introduced violations.

## Stage Ladder

- **Stage 0: Baseline lock**
  - Freeze current `product_readiness` behavior.
  - Save current `DecisionConfig`, retrieval/ranker configs, task file hashes, artifact hashes, dependency versions, test output, and current product/research metrics.
  - This becomes the rollback point for all later stages.

- **Stage 1: Decision calibration max-out**
  - Change only the decision layer.
  - Tune route confidence, margin, top-k, ASK_PARAM, unsafe/block, and overclarification penalty on dev only.
  - Add confidence/margin calibration plots, confusion matrix, false-overclarification breakdown, and false-execution breakdown.
  - Retrieval code must not change.

- **Stage 2: Validation and param/body binding max-out**
  - Improve required param/body/header/auth extraction and source classification:
    `user_provided`, `conversation_context`, `defaultable`, `unavailable`.
  - Generate synthetic bodies only for validation.
  - Add validation error explanations and ASK_PARAM usefulness scoring.
  - Do not execute writes.

- **Stage 3: Conversation context routing**
  - Add `conversation_context` input to product routing.
  - Carry forward prior selected endpoint, resource, params, and resolved follow-up answers.
  - Generate turn-level benchmark tasks such as “do that for this order” and “same but for cart”.
  - Measure context route accuracy, follow-up resolution, param carry-forward, and wrong-context risk.

- **Stage 4: LLM query canonicalization**
  - Add optional preprocessing only; LLM cannot choose endpoints.
  - Logged output schema:
    `canonical_query`, `likely_resource_terms`, `likely_operation_terms`, `missing_information`, `policy_gap`, `safety_concern`.
  - Compare with no-LLM baseline and report latency/cost.
  - LLM output must not bypass validation or guardrails.

- **Stage 5: LLM top-k reranker**
  - LLM reranks only top 5 or top 10 existing candidates.
  - LLM may only output provided endpoint IDs.
  - Validation and guardrails remain authoritative.
  - Compare against classical learned ranker.

- **Stage 6: Feedback-aware ranker max-out**
  - Expand feedback training with explicit, implicit, and synthetic labels kept separate.
  - Add logistic regression, random forest/gradient boosting, and calibrated classifier variants.
  - Report feature ablations: lexical only, graph only, schema only, LLM only, feedback only, lexical+graph, lexical+graph+feedback, all features.
  - Synthetic-feedback results remain labeled as offline experiments.

- **Stage 7: Active learning and agentic UI loop**
  - Add uncertainty sampling, endpoint explanations, one-click correction/rejection events, param correction capture, guardrail override capture, and policy-source request capture.
  - Measure feedback collection rate, correction-to-improvement rate, repeated error reduction, and user intervention burden.

- **Stage 8: Autonomy gating**
  - Implement autonomy modes: `observe`, `suggest`, `dry_run`, `auto_read`, `confirm_write`, `block_write`.
  - Produce autonomy eligibility and safety reports.
  - Validation failure, missing params, policy gaps, unsafe DELETE/delete-class, and guardrail violations always prevent auto-execution.

- **Stage 9: Dense embeddings / semantic retriever**
  - Add dense retriever as an additional candidate source without removing lexical/BM25/graph baselines.
  - Index endpoint, parameter, schema, auth, and graph-neighborhood docs.
  - Compare dense, dense+BM25, dense+graph, dense+GRAG, and dense+LLM reranker.

- **Stage 10: GraphSAGE experiment**
  - Start only after Stages 0-9 are reported.
  - Build graph nodes and edges exactly from OpenAPI artifacts, feedback, tenant/integration metadata, and task/query events.
  - Evaluate GraphSAGE as candidate reranker over existing retriever unions.
  - Promote only if it beats the best non-GNN router on test without increasing false execution or guardrail violations.

## Promotion Protocol

- Before each stage, run and save the previous promoted baseline.
- After each stage, run:
  - product readiness benchmark
  - recovery follow-up benchmark
  - low-overlap stress benchmark
  - guardrail tests
  - full regression tests
- Promotion decision is one of:
  - `promote`
  - `keep_as_ablation`
  - `discard`
- Promote only if:
  - natural top1 improves or stays stable while another key metric improves.
  - top3 recoverability does not materially regress.
  - false execution stays `<= data/router_guardrails.json.false_execution_limit`.
  - guardrail tests pass.
  - validation does not regress.
  - test split improves, not just dev.

## Test Plan

- Add tests for experiment folder creation, artifact hashing, metric schema completeness, and cumulative ladder report generation.
- Add tests that Stage 0 does not modify routing behavior and records the current baseline exactly.
- Add promotion-rule tests for promote, keep-as-ablation, and discard decisions.
- Add guardrail audit tests for Medusa maps, routing rules, action lexicons, stopword lists, hidden policy inference, premature GraphSAGE, unsafe writes, and validation bypass.
- Add stage-specific tests as each stage is implemented:
  - Stage 1: dev-only config tuning and calibration output.
  - Stage 2: param/body/header/auth binding and validation explanations.
  - Stage 3: context carry-forward and wrong-context prevention.
  - Stage 4-5: LLM audit logs, schema-constrained outputs, endpoint-candidate restrictions, latency/cost reporting.
  - Stage 6: label quality separation and model ablations.
  - Stage 7: feedback event capture quality.
  - Stage 8: autonomy eligibility and blocked unsafe actions.
  - Stage 9: dense retriever ablations.
  - Stage 10: GraphSAGE split discipline, graph construction, and non-GNN comparison.

## Assumptions

- Stage 0 plus the ladder harness should be implemented first; stages 1-10 are implemented one at a time after each prior stage is reported.
- Existing current product metrics are the starting baseline, not the target to retroactively optimize.
- No stage may silently change task generation, validation, guardrails, or retrieval unless that is the explicit technique under test.
- LLM stages are disabled by default and require explicit configuration. LLM calls must be logged, schema-validated, and cost/latency-reported.
- Dense retrieval and GraphSAGE add candidate sources or rerankers; they do not replace current lexical/BM25/graph/GRAG baselines.
- Low-overlap stress remains a separate robustness track and must not be mixed into product-readiness headline metrics.
