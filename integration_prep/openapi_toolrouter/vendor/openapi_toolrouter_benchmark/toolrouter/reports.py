from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def mean_metric(rows: list[dict[str, Any]], metric: str) -> float:
    if not rows:
        return 0.0
    return sum(float(row.get(metric, 0.0)) for row in rows) / len(rows)


def summary_lookup(results: dict[str, Any], baseline: str, split: str, k: int) -> dict[str, Any]:
    for row in results.get("summary", []):
        if row.get("baseline") == baseline and row.get("split") == split and int(row.get("k", 0)) == k:
            return row
    return {}


def resource_comparison_rows(results: dict[str, Any]) -> list[dict[str, Any]]:
    details = results.get("details", [])
    rows: list[dict[str, Any]] = []
    for comparator in ["rag_all_max", "bm25_all_max"]:
        split_resource_pairs = sorted(
            {
                (str(row.get("split", "all")), str(row.get("resource", "unknown")))
                for row in details
                if row.get("baseline") in {"graph_sparse", comparator}
            }
        )
        for split, resource in split_resource_pairs:
            graph_k1 = [
                row
                for row in details
                if row.get("baseline") == "graph_sparse"
                and row.get("split") == split
                and str(row.get("resource", "unknown")) == resource
                and int(row.get("k", 0)) == 1
            ]
            comp_k1 = [
                row
                for row in details
                if row.get("baseline") == comparator
                and row.get("split") == split
                and str(row.get("resource", "unknown")) == resource
                and int(row.get("k", 0)) == 1
            ]
            graph_k10 = [
                row
                for row in details
                if row.get("baseline") == "graph_sparse"
                and row.get("split") == split
                and str(row.get("resource", "unknown")) == resource
                and int(row.get("k", 0)) == 10
            ]
            comp_k10 = [
                row
                for row in details
                if row.get("baseline") == comparator
                and row.get("split") == split
                and str(row.get("resource", "unknown")) == resource
                and int(row.get("k", 0)) == 10
            ]
            if not graph_k1 or not comp_k1:
                continue
            deltas = {
                "complete_at_1_delta": mean_metric(graph_k1, "complete_plan_recall_at_k") - mean_metric(comp_k1, "complete_plan_recall_at_k"),
                "complete_at_10_delta": mean_metric(graph_k10, "complete_plan_recall_at_k") - mean_metric(comp_k10, "complete_plan_recall_at_k"),
                "first_step_at_1_delta": mean_metric(graph_k1, "first_step_top1_accuracy") - mean_metric(comp_k1, "first_step_top1_accuracy"),
                "validation_pass_delta": mean_metric(graph_k1, "validation_pass") - mean_metric(comp_k1, "validation_pass"),
            }
            score = sum(deltas.values())
            outcome = "win" if score > 0 else "loss" if score < 0 else "tie"
            rows.append(
                {
                    "split": split,
                    "resource": resource,
                    "comparator": comparator,
                    "outcome": outcome,
                    **deltas,
                }
            )
    return rows


def ordered_summary_rows(rows: list[dict[str, Any]], baselines: list[str]) -> list[dict[str, Any]]:
    baseline_rank = {baseline: idx for idx, baseline in enumerate(baselines)}
    return sorted(
        [row for row in rows if row.get("baseline") in baseline_rank],
        key=lambda row: (str(row.get("split", "all")), baseline_rank[str(row.get("baseline"))], int(row.get("k", 0))),
    )


def summary_table_lines(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Split | Baseline | k | Complete | Routing@1 | Routing@10 | Ambiguous Abstain | Policy Abstain | Macro Track | Required Params | Validation | Latency ms |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {split} | {baseline} | {k} | {complete} | {routing1} | {routing10} | {ambiguous} | {policy} | {macro} | {required} | {validation} | {latency:.2f} |".format(
                split=str(row.get("split", "all")),
                baseline=str(row["baseline"]).upper(),
                k=int(row.get("k", 0)),
                complete=pct(row.get("complete_plan_recall_at_k", 0.0)),
                routing1=pct(row.get("routing_only_complete_at_1", 0.0)),
                routing10=pct(row.get("routing_only_complete_at_10", 0.0)),
                ambiguous=pct(row.get("ambiguous_abstention_accuracy", 0.0)),
                policy=pct(row.get("policy_abstention_accuracy", 0.0)),
                macro=pct(row.get("macro_average_by_track", 0.0)),
                required=pct(row.get("required_params_covered", row.get("param_coverage", 0.0))),
                validation=pct(row.get("validation_pass", row.get("schema_validation_pass_rate", 0.0))),
                latency=float(row.get("latency_ms_mean", 0.0)),
            )
        )
    return lines


def write_reports(results: dict[str, Any], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if results.get("product_summary"):
        write_product_reports(results, out_dir)
        return
    grag_baselines = ["grag_expand", "grag_rerank", "grag_constrained"]
    required_ablations = ["rag_all_max", "bm25_all_max", "graph_sparse"]
    known_grouped = set(grag_baselines + required_ablations)
    other_baselines = sorted({str(row.get("baseline")) for row in results.get("summary", [])} - known_grouped)
    summary_lines = [
        "# OpenAPI Routing Results",
        "",
        "## Graph-Enriched RAG Baselines",
        "",
    ]
    summary_rows = results.get("summary", [])
    summary_lines.extend(summary_table_lines(ordered_summary_rows(summary_rows, grag_baselines)))
    summary_lines.extend(["", "## Required Ablations", ""])
    summary_lines.extend(summary_table_lines(ordered_summary_rows(summary_rows, required_ablations)))
    if other_baselines:
        summary_lines.extend(["", "## Other Baselines", ""])
        summary_lines.extend(summary_table_lines(ordered_summary_rows(summary_rows, other_baselines)))
    if results.get("leakage_summary"):
        summary_lines.extend(
            [
                "",
                "## Metrics By Leakage Bucket",
                "",
                "| Split | Bucket | Baseline | k | Tasks | Complete | Routing@1 | Routing@10 | Ambiguous Abstain | Policy Abstain | Macro Track | Required Params | Validation |",
                "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for row in results["leakage_summary"]:
            summary_lines.append(
                "| {split} | {bucket} | {baseline} | {k} | {tasks} | {complete} | {routing1} | {routing10} | {ambiguous} | {policy} | {macro} | {required} | {validation} |".format(
                    split=str(row.get("split", "all")),
                    bucket=str(row.get("leakage_bucket", "unknown")),
                    baseline=str(row["baseline"]).upper(),
                    k=row["k"],
                    tasks=row.get("task_count", 0),
                    complete=pct(row["complete_plan_recall_at_k"]),
                    routing1=pct(row.get("routing_only_complete_at_1", 0.0)),
                    routing10=pct(row.get("routing_only_complete_at_10", 0.0)),
                    ambiguous=pct(row.get("ambiguous_abstention_accuracy", 0.0)),
                    policy=pct(row.get("policy_abstention_accuracy", 0.0)),
                    macro=pct(row.get("macro_average_by_track", 0.0)),
                    required=pct(row.get("required_params_covered", 0.0)),
                    validation=pct(row.get("validation_pass", 0.0)),
                )
            )
    summary_lines.extend(
        [
            "",
            "The benchmark uses official OpenAPI specs as the routing source of truth. Write operations are evaluated as dry-run schema/plan candidates only.",
        ]
    )
    (out_dir / "medusa_routing_results.md").write_text("\n".join(summary_lines), encoding="utf-8")

    by_baseline = defaultdict(Counter)
    examples = defaultdict(list)
    for detail in results.get("details", []):
        category = detail.get("failure_category", "unknown")
        key = (detail.get("split", "all"), detail.get("baseline", "unknown"))
        by_baseline[key][category] += 1
        if category != "none" and len(examples[category]) < 5:
            examples[category].append(detail)
    failure_lines = ["# Failure Analysis", ""]
    for (split, baseline), counts in sorted(by_baseline.items()):
        failure_lines.append(f"## {split} / {str(baseline).upper()}")
        for category, count in sorted(counts.items()):
            failure_lines.append(f"- {category}: {count}")
        failure_lines.append("")
    failure_lines.append("## Examples")
    for category, rows in sorted(examples.items()):
        failure_lines.append(f"### {category}")
        for row in rows:
            failure_lines.append(f"- `{row['task_id']}` {row['query']}")
        failure_lines.append("")
    (out_dir / "failure_analysis.md").write_text("\n".join(failure_lines), encoding="utf-8")

    ablation_rows = results.get("graph_sparse_ablation", [])
    ablation_lines = [
        "# Graph Sparse Ablation",
        "",
        "| Split | Config | Selected | Dev tasks | Complete@1 | Complete@10 | First-step@1 | Seed top n | Steps | Damping | Directed | High-degree | Endpoint prior |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|",
    ]
    for row in ablation_rows:
        ablation_lines.append(
            "| {split} | {name} | {selected} | {count} | {c1} | {c10} | {first} | {seed} | {steps} | {damping:.2f} | {directed} | {high_degree} | {prior:.2f} |".format(
                split=row.get("split", "all"),
                name=row.get("name", ""),
                selected="yes" if row.get("selected") else "no",
                count=row.get("dev_task_count", 0),
                c1=pct(row.get("complete_plan_at_1", 0.0)),
                c10=pct(row.get("complete_plan_at_10", 0.0)),
                first=pct(row.get("first_step_top1", 0.0)),
                seed=row.get("seed_top_n", 0),
                steps=row.get("steps", 0),
                damping=float(row.get("damping", 0.0)),
                directed=str(bool(row.get("directed", False))).lower(),
                high_degree=str(bool(row.get("high_degree_downweight", False))).lower(),
                prior=float(row.get("endpoint_prior_weight", 0.0)),
            )
        )
    (out_dir / "graph_sparse_ablation.md").write_text("\n".join(ablation_lines), encoding="utf-8")

    with (out_dir / "graph_sparse_diagnostics.jsonl").open("w", encoding="utf-8") as fh:
        for row in results.get("graph_sparse_diagnostics", []):
            fh.write(json.dumps(row, sort_keys=True) + "\n")

    stability = results.get("graph_sparse_stability", {})
    stability_lines = [
        "# Graph Sparse Stability",
        "",
        "Graph sparse configuration selection is performed from the active dev rows only for each evaluation scope.",
        "",
        "## Selected Config Frequency",
        "",
        "| Config | Count |",
        "|---|---:|",
    ]
    for name, count in sorted((stability.get("selected_config_frequency") or {}).items()):
        stability_lines.append(f"| {name} | {count} |")
    stability_lines.extend(
        [
            "",
            "## Selected Config By Scope",
            "",
            "| Scope | Config | Seed top n | Steps | Damping | Directed | High-degree | Endpoint prior | Dev Complete@1 | Dev Complete@10 | Held-out Complete@1 | Held-out Complete@10 |",
            "|---|---|---:|---:|---:|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    selected_dev = {
        row.get("split"): row
        for row in results.get("graph_sparse_ablation", [])
        if row.get("selected")
    }
    for scope, config in sorted((stability.get("selected_by_scope") or {}).items()):
        dev_row = selected_dev.get(scope, {})
        held_1 = summary_lookup(results, "graph_sparse", scope, 1)
        held_10 = summary_lookup(results, "graph_sparse", scope, 10)
        stability_lines.append(
            "| {scope} | {name} | {seed} | {steps} | {damping:.2f} | {directed} | {high_degree} | {prior:.2f} | {dev1} | {dev10} | {held1} | {held10} |".format(
                scope=scope,
                name=config.get("name", ""),
                seed=config.get("seed_top_n", 0),
                steps=config.get("steps", 0),
                damping=float(config.get("damping", 0.0)),
                directed=str(bool(config.get("directed", False))).lower(),
                high_degree=str(bool(config.get("high_degree_downweight", False))).lower(),
                prior=float(config.get("endpoint_prior_weight", 0.0)),
                dev1=pct(dev_row.get("complete_plan_at_1", 0.0)),
                dev10=pct(dev_row.get("complete_plan_at_10", 0.0)),
                held1=pct(held_1.get("complete_plan_recall_at_k", 0.0)),
                held10=pct(held_10.get("complete_plan_recall_at_k", 0.0)),
            )
        )
    stability_lines.extend(
        [
            "",
            "## Resource-Wise Graph Sparse Comparison",
            "",
            "| Split | Resource | Comparator | Outcome | Complete@1 Delta | Complete@10 Delta | First-step@1 Delta | Validation Delta |",
            "|---|---|---|---|---:|---:|---:|---:|",
        ]
    )
    comparison_rows = resource_comparison_rows(results)
    for row in comparison_rows:
        stability_lines.append(
            "| {split} | {resource} | {comparator} | {outcome} | {c1:+.3f} | {c10:+.3f} | {first:+.3f} | {validation:+.3f} |".format(
                split=row["split"],
                resource=row["resource"],
                comparator=row["comparator"],
                outcome=row["outcome"],
                c1=row["complete_at_1_delta"],
                c10=row["complete_at_10_delta"],
                first=row["first_step_at_1_delta"],
                validation=row["validation_pass_delta"],
            )
        )
    (out_dir / "graph_sparse_stability.md").write_text("\n".join(stability_lines), encoding="utf-8")
    (out_dir / "graph_sparse_stability.json").write_text(
        json.dumps(
            {
                "graph_sparse_stability": stability,
                "resource_wise_comparison": comparison_rows,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    hybrid_lines = [
        "# Hybrid Weight Selection",
        "",
        "The reported hybrid baseline uses weights selected on the active dev rows only.",
        "",
        "| Scope | Lexical | BM25 | Graph sparse | Param/schema | Dev Complete@1 | Dev Complete@10 | Held-out Complete@1 | Held-out Complete@10 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scope, row in sorted((results.get("hybrid_weight_selection") or {}).items()):
        weights = row.get("selected_weights", {})
        dev = row.get("dev_metrics", {})
        held = row.get("held_out_metrics", {})
        hybrid_lines.append(
            "| {scope} | {lexical:.2f} | {bm25:.2f} | {graph:.2f} | {schema:.2f} | {dev1} | {dev10} | {held1} | {held10} |".format(
                scope=scope,
                lexical=float(weights.get("lexical", 0.0)),
                bm25=float(weights.get("bm25", 0.0)),
                graph=float(weights.get("graph", 0.0)),
                schema=float(weights.get("schema_param", 0.0)),
                dev1=pct(dev.get("complete_plan_at_1", 0.0)),
                dev10=pct(dev.get("complete_plan_at_10", 0.0)),
                held1=pct(held.get("complete_plan_at_1", 0.0)),
                held10=pct(held.get("complete_plan_at_10", 0.0)),
            )
        )
    hybrid_lines.extend(
        [
            "",
            "## Selected Grid Rows",
            "",
            "| Scope | Config | Threshold | Selected | Dev tasks | Complete@1 | Complete@10 | First-step@1 |",
            "|---|---|---:|---|---:|---:|---:|---:|",
        ]
    )
    for row in results.get("hybrid_weight_ablation", []):
        if not row.get("selected"):
            continue
        hybrid_lines.append(
            "| {split} | {name} | {threshold:.4f} | yes | {count} | {c1} | {c10} | {first} |".format(
                split=row.get("split", "all"),
                name=row.get("name", ""),
                threshold=float(row.get("threshold", 0.0)),
                count=row.get("dev_task_count", 0),
                c1=pct(row.get("complete_plan_at_1", 0.0)),
                c10=pct(row.get("complete_plan_at_10", 0.0)),
                first=pct(row.get("first_step_top1", 0.0)),
            )
        )
    (out_dir / "hybrid_weight_selection.md").write_text("\n".join(hybrid_lines), encoding="utf-8")

    learned_baselines = [
        "learned_lexical",
        "learned_bm25",
        "learned_graph",
        "learned_schema_param",
        "learned_lexical_graph",
        "learned_all",
        "learned",
    ]
    learned_lines = [
        "# Learned Ranker Ablations",
        "",
        "| Split | Baseline | Complete@1 | Complete@10 | First-step@1 | Required Params | Validation | Abstention |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for split in sorted({row.get("split", "all") for row in results.get("summary", [])}):
        for baseline in learned_baselines:
            k1 = summary_lookup(results, baseline, split, 1)
            k10 = summary_lookup(results, baseline, split, 10)
            if not k1:
                continue
            learned_lines.append(
                "| {split} | {baseline} | {c1} | {c10} | {first} | {required} | {validation} | {abstain} |".format(
                    split=split,
                    baseline=baseline,
                    c1=pct(k1.get("complete_plan_recall_at_k", 0.0)),
                    c10=pct(k10.get("complete_plan_recall_at_k", 0.0)),
                    first=pct(k1.get("first_step_top1_accuracy", 0.0)),
                    required=pct(k1.get("required_params_covered", 0.0)),
                    validation=pct(k1.get("validation_pass", 0.0)),
                    abstain=pct(k1.get("abstention_accuracy", 0.0)),
                )
            )
    learned_lines.extend(["", "## Feature Masks", "", "| Baseline | Features |", "|---|---|"])
    for baseline, meta in sorted((results.get("learned_ablations") or {}).items()):
        learned_lines.append(f"| {baseline} | {', '.join(meta.get('features', []))} |")
    (out_dir / "learned_ablations.md").write_text("\n".join(learned_lines), encoding="utf-8")


def product_summary_table(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "| Split | Track | Tasks | Routing tasks | Follow-up tasks | Top1 route | Top3 recover | Top10 recall | Decision type | Follow-up type | Param questions | Policy gaps | False execution | False overclarification | Validation | Latency ms |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {split} | {track} | {tasks} | {routing} | {followup} | {top1} | {top3} | {top10} | {decision} | {followup_type} | {params} | {policy} | {false_exec} | {false_clarify} | {validation} | {latency:.2f} |".format(
                split=row.get("split", "all"),
                track=row.get("track", "unknown"),
                tasks=row.get("task_count", 0),
                routing=row.get("routing_task_count", 0),
                followup=row.get("followup_task_count", 0),
                top1=pct(row.get("natural_top1_route_accuracy", 0.0)),
                top3=pct(row.get("natural_top3_recoverability", 0.0)),
                top10=pct(row.get("natural_top10_candidate_recall", 0.0)),
                decision=pct(row.get("correct_decision_type", 0.0)),
                followup_type=pct(row.get("correct_followup_type", 0.0)),
                params=pct(row.get("required_param_question_accuracy", 0.0)),
                policy=pct(row.get("policy_gap_detection_accuracy", 0.0)),
                false_exec=pct(row.get("false_execution_rate", 0.0)),
                false_clarify=pct(row.get("false_overclarification_rate", 0.0)),
                validation=pct(row.get("validation_pass_rate", 0.0)),
                latency=float(row.get("latency_ms", 0.0)),
            )
        )
    return lines


def write_product_reports(results: dict[str, Any], out_dir: Path) -> None:
    summary = results.get("product_summary", [])
    details = results.get("product_details", [])
    lines = [
        "# Product Readiness",
        "",
        "This report keeps routing accuracy separate from follow-up accuracy. Low-overlap remains a research stress track, not the product headline.",
        "",
    ]
    selected_config = results.get("selected_decision_config", {})
    if selected_config:
        lines.extend(
            [
                "## Selected Decision Config",
                "",
                f"- Selected from: `{selected_config.get('selected_from', 'unknown')}`",
                f"- Route confidence: `{selected_config.get('route_confidence_threshold', 0.0)}`",
                f"- Route margin: `{selected_config.get('route_margin_threshold', 0.0)}`",
                f"- Param confidence: `{selected_config.get('param_confidence_threshold', 0.0)}`",
                f"- Top-k confidence: `{selected_config.get('show_topk_confidence_threshold', 0.0)}`",
                f"- Unsafe write threshold: `{selected_config.get('unsafe_write_threshold', 0.0)}`",
                "",
            ]
        )
    lines.extend(product_summary_table(summary))
    lines.extend(
        [
            "",
            "## Decision Types",
            "",
            "- `ROUTE`: high-confidence endpoint selection.",
            "- `SHOW_TOPK`: medium-confidence top candidate set.",
            "- `ASK_PARAM`: endpoint is clear, but OpenAPI-required inputs are missing.",
            "- `ASK_DISAMBIGUATE`: multiple endpoint families are plausible.",
            "- `ASK_POLICY`: OpenAPI lacks the business policy source.",
            "- `BLOCK_UNSAFE`: destructive write needs confirmation; benchmark remains dry-run.",
        ]
    )
    (out_dir / "product_readiness.md").write_text("\n".join(lines), encoding="utf-8")

    natural_lines = [
        "# Natural Routing",
        "",
        "Realistic phrasing tasks are evaluated with routing-only metrics.",
        "",
    ]
    natural_lines.extend(product_summary_table([row for row in summary if row.get("track") == "natural_routing"]))
    natural_lines.extend(["", "## Examples", ""])
    for row in [item for item in details if item.get("track") == "natural_routing"][:20]:
        natural_lines.append(
            "- `{task}` {query} -> {decision} / {endpoint} / top3={top3}".format(
                task=row.get("task_id"),
                query=row.get("query"),
                decision=row.get("decision_type"),
                endpoint=row.get("selected_endpoint"),
                top3=", ".join(row.get("top_candidate_ids", [])[:3]),
            )
        )
    (out_dir / "natural_routing.md").write_text("\n".join(natural_lines), encoding="utf-8")

    recovery_lines = [
        "# Recovery Follow-Up",
        "",
        "Ambiguous, missing-param, policy, and unsafe-write tasks are evaluated as follow-up decisions, not endpoint-routing accuracy.",
        "",
    ]
    recovery_lines.extend(product_summary_table([row for row in summary if row.get("track") == "recovery_followup"]))
    recovery_lines.extend(["", "## Examples", ""])
    for row in [item for item in details if item.get("track") == "recovery_followup"][:30]:
        recovery_lines.append(
            "- `{task}` expected={expected} actual={actual} question={question}".format(
                task=row.get("task_id"),
                expected=row.get("expected_decision_type"),
                actual=row.get("decision_type"),
                question=row.get("follow_up_question", ""),
            )
        )
    (out_dir / "recovery_followup.md").write_text("\n".join(recovery_lines), encoding="utf-8")

    feedback = results.get("feedback_learning", {})
    feedback_lines = [
        "# Feedback Learning",
        "",
        f"Feedback events observed: `{feedback.get('feedback_event_count', 0)}`",
        f"Feedback model status: `{feedback.get('model_status', 'unknown')}`",
        "",
        "The feedback-aware ranker can use selected/corrected endpoints as positives and rejected endpoints as negatives.",
        "",
    ]
    synthetic = results.get("synthetic_feedback_experiment") or feedback.get("synthetic_feedback_experiment")
    if synthetic:
        feedback_lines.extend(
            [
                "## Synthetic Offline Experiment",
                "",
                "These rows are generated from benchmark corrections. They are not real runtime feedback claims.",
                "",
                f"- Synthetic feedback events: `{synthetic.get('event_count', 0)}`",
                f"- Model status: `{synthetic.get('model_status', 'unknown')}`",
                f"- Feedback file: `{synthetic.get('feedback_path', '')}`",
                f"- Model file: `{synthetic.get('model_path', '')}`",
                "",
                "### Before",
                "",
            ]
        )
        feedback_lines.extend(product_summary_table(synthetic.get("before", [])))
        feedback_lines.extend(["", "### After", ""])
        feedback_lines.extend(product_summary_table(synthetic.get("after", [])))
        feedback_lines.append("")
    feedback_lines.extend(["## Feature Surface", ""])
    for name in feedback.get("feature_names", []):
        feedback_lines.append(f"- `{name}`")
    (out_dir / "feedback_learning.md").write_text("\n".join(feedback_lines), encoding="utf-8")

    calibration_lines = [
        "# Decision Calibration",
        "",
        "Decision calibration is evaluated after endpoint candidates are ranked. Retrieval scores are not changed in this slice.",
        "",
    ]
    if selected_config:
        calibration_lines.extend(
            [
                "## Selected Config",
                "",
                "| Field | Value |",
                "|---|---:|",
            ]
        )
        for key in [
            "name",
            "selected_from",
            "route_confidence_threshold",
            "route_margin_threshold",
            "param_confidence_threshold",
            "show_topk_confidence_threshold",
            "unsafe_write_threshold",
        ]:
            calibration_lines.append(f"| {key} | {selected_config.get(key, '')} |")
        calibration_lines.append("")
    calibration_lines.extend(
        [
            "## Confusion Matrix",
            "",
            "| Expected | Actual | Count | Highlight |",
            "|---|---|---:|---|",
        ]
    )
    for row in results.get("decision_confusion", []):
        calibration_lines.append(
            f"| {row.get('expected_decision_type')} | {row.get('decision_type')} | {row.get('count', 0)} | {'yes' if row.get('highlight_pair') else ''} |"
        )
    calibration_lines.extend(
        [
            "",
            "## Per-Task Diagnostics",
            "",
            "| Task | Split | Track | Expected | Actual | Expected endpoint | Selected endpoint | Confidence | Margin | Missing params | Unsafe | Reason | Top3 | Query |",
            "|---|---|---|---|---|---|---|---:|---:|---|---|---|---|---|",
        ]
    )
    for row in results.get("decision_calibration", []):
        query = str(row.get("query", "")).replace("|", "\\|")
        top3 = ", ".join(row.get("top3_candidates", []) or [])
        missing = ", ".join(row.get("missing_params", []) or [])
        calibration_lines.append(
            "| {task} | {split} | {track} | {expected} | {actual} | {expected_endpoint} | {selected} | {confidence:.3f} | {margin:.3f} | {missing} | {unsafe} | {reason} | {top3} | {query} |".format(
                task=row.get("task_id"),
                split=row.get("split", "all"),
                track=row.get("track", ""),
                expected=row.get("expected_decision_type", ""),
                actual=row.get("decision_type", ""),
                expected_endpoint=row.get("expected_endpoint", ""),
                selected=row.get("selected_endpoint", ""),
                confidence=float(row.get("confidence", 0.0)),
                margin=float(row.get("margin", 0.0)),
                missing=missing,
                unsafe=str(bool(row.get("unsafe_flag", False))).lower(),
                reason=row.get("decision_reason", ""),
                top3=top3,
                query=query,
            )
        )
    (out_dir / "decision_calibration.md").write_text("\n".join(calibration_lines), encoding="utf-8")
