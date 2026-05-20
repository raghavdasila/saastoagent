from __future__ import annotations

import json
from pathlib import Path
from urllib.request import Request, urlopen

import typer

from .decision_router import evaluate_product_readiness, route_product_query
from .evaluator import evaluate_rankings, read_results, write_results
from .feedback import FeedbackEvent, feedback_manifest_path, read_feedback_events, train_feedback_ranker, write_feedback_event
from .graphgen import build_schema_graph, read_graph, write_graph
from .leakage_audit import attach_leakage_to_tasks, write_leakage_audit
from .medusa_smoke import run_medusa_smoke
from .openapi_loader import load_openapi_specs, read_normalized_bundle, write_normalized_bundle
from .raggen import build_rag_corpus, read_rag_corpus, write_rag_corpus
from .reports import write_reports
from .retrieval_indices import build_retrieval_indices
from .router_baselines import rank_tasks
from .splits import build_task_splits, primary_split_by_task, read_task_splits, split_task_ids_for_evaluation, write_task_splits
from .task_audit import write_task_audit
from .tasks import (
    generate_low_overlap_tasks,
    generate_natural_tasks,
    generate_recovery_tasks,
    generate_tasks,
    read_coverage_terms,
    read_tasks,
    write_tasks,
)
from .validation import build_validation_context
from .integration.feedback import read_standard_feedback_events, write_standard_feedback_event
from .integration.schemas import StandardFeedbackEvent
from .integration.saastoagent_adapter import route_tool_request


app = typer.Typer(help="OpenAPI tool-routing benchmark CLI.")

MEDUSA_SPECS = {
    "medusa_admin.yaml": "https://docs.medusajs.com/api/download/admin",
    "medusa_store.yaml": "https://docs.medusajs.com/api/download/store",
}


@app.command("fetch-medusa-specs")
def fetch_medusa_specs(out: Path = typer.Option(..., "--out")) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, url in MEDUSA_SPECS.items():
        request = Request(url, headers={"User-Agent": "toolrouter-benchmark/0.1"})
        with urlopen(request, timeout=90) as response:
            data = response.read()
        (out / name).write_bytes(data)
        typer.echo(f"wrote {out / name} ({len(data)} bytes)")


@app.command("ingest")
def ingest(openapi: list[Path] = typer.Option(..., "--openapi"), out: Path = typer.Option(..., "--out")) -> None:
    bundle = load_openapi_specs(openapi)
    graph = build_schema_graph(bundle)
    corpus = build_rag_corpus(bundle)
    write_normalized_bundle(bundle, out)
    write_graph(graph, out)
    write_rag_corpus(corpus, out)
    typer.echo(json.dumps(bundle.manifest, indent=2))


@app.command("tasks")
def make_tasks(
    artifacts: Path = typer.Option(..., "--artifacts"),
    out: Path = typer.Option(..., "--out"),
    min_count: int = typer.Option(100, "--min-count"),
    coverage: Path | None = typer.Option(None, "--coverage"),
    task_prefix: str = typer.Option("task", "--task-prefix"),
) -> None:
    bundle = read_normalized_bundle(artifacts)
    tasks = generate_tasks(
        bundle,
        min_count=min_count,
        coverage_terms=read_coverage_terms(coverage),
        task_prefix=task_prefix,
    )
    write_tasks(tasks, out)
    typer.echo(f"wrote {len(tasks)} tasks to {out}")


@app.command("low-overlap-tasks")
def make_low_overlap_tasks(
    artifacts: Path = typer.Option(..., "--artifacts"),
    out: Path = typer.Option(..., "--out"),
    min_routing: int = typer.Option(100, "--min-routing"),
    min_ambiguous: int = typer.Option(50, "--min-ambiguous"),
    min_policy: int = typer.Option(50, "--min-policy"),
    coverage: Path | None = typer.Option(None, "--coverage"),
    task_prefix: str = typer.Option("low", "--task-prefix"),
) -> None:
    bundle = read_normalized_bundle(artifacts)
    tasks = generate_low_overlap_tasks(
        bundle,
        min_routing=min_routing,
        min_ambiguous=min_ambiguous,
        min_policy=min_policy,
        coverage_terms=read_coverage_terms(coverage),
        task_prefix=task_prefix,
    )
    write_tasks(tasks, out)
    typer.echo(f"wrote {len(tasks)} low-overlap tasks to {out}")


@app.command("natural-tasks")
def make_natural_tasks(
    artifacts: Path = typer.Option(..., "--artifacts"),
    out: Path = typer.Option(..., "--out"),
    min_count: int = typer.Option(100, "--min-count"),
    coverage: Path | None = typer.Option(None, "--coverage"),
    task_prefix: str = typer.Option("natural", "--task-prefix"),
) -> None:
    bundle = read_normalized_bundle(artifacts)
    tasks = generate_natural_tasks(
        bundle,
        min_count=min_count,
        coverage_terms=read_coverage_terms(coverage),
        task_prefix=task_prefix,
    )
    write_tasks(tasks, out)
    typer.echo(f"wrote {len(tasks)} natural routing tasks to {out}")


@app.command("recovery-tasks")
def make_recovery_tasks(
    artifacts: Path = typer.Option(..., "--artifacts"),
    out: Path = typer.Option(..., "--out"),
    min_missing_param: int = typer.Option(25, "--min-missing-param"),
    min_ambiguous: int = typer.Option(25, "--min-ambiguous"),
    min_policy: int = typer.Option(25, "--min-policy"),
    min_unsafe: int = typer.Option(10, "--min-unsafe"),
    coverage: Path | None = typer.Option(None, "--coverage"),
    task_prefix: str = typer.Option("recovery", "--task-prefix"),
) -> None:
    bundle = read_normalized_bundle(artifacts)
    tasks = generate_recovery_tasks(
        bundle,
        min_missing_param=min_missing_param,
        min_ambiguous=min_ambiguous,
        min_policy=min_policy,
        min_unsafe=min_unsafe,
        coverage_terms=read_coverage_terms(coverage),
        task_prefix=task_prefix,
    )
    write_tasks(tasks, out)
    typer.echo(f"wrote {len(tasks)} recovery follow-up tasks to {out}")


@app.command("benchmark")
def benchmark(
    tasks: list[Path] = typer.Option(..., "--tasks"),
    artifacts: Path = typer.Option(..., "--artifacts"),
    out: Path = typer.Option(..., "--out"),
    splits: Path | None = typer.Option(None, "--splits"),
    mode: str = typer.Option("research", "--mode"),
    feedback_log: Path | None = typer.Option(None, "--feedback-log"),
    feedback_model: Path | None = typer.Option(None, "--feedback-model"),
    write_feedback_log: Path | None = typer.Option(None, "--write-feedback-log"),
    synthetic_feedback: bool = typer.Option(False, "--synthetic-feedback"),
    synthetic_feedback_out: Path = typer.Option(Path("data/synthetic_feedback_events.jsonl"), "--synthetic-feedback-out"),
    synthetic_feedback_model: Path = typer.Option(Path("artifacts/synthetic_feedback_ranker.joblib"), "--synthetic-feedback-model"),
) -> None:
    bundle = read_normalized_bundle(artifacts)
    corpus = read_rag_corpus(artifacts)
    graph = read_graph(artifacts)
    task_rows = [task for task_path in tasks for task in read_tasks(task_path)]
    if mode == "product_readiness":
        indices = build_retrieval_indices(bundle, corpus, graph)
        split_rows = read_task_splits(splits)
        results = evaluate_product_readiness(
            task_rows,
            bundle,
            indices,
            feedback_log=feedback_log,
            feedback_model=feedback_model,
            write_feedback_log=write_feedback_log,
            splits=split_rows,
            synthetic_feedback_out=synthetic_feedback_out if synthetic_feedback else None,
            synthetic_feedback_model=synthetic_feedback_model if synthetic_feedback else None,
        )
        write_results(results, out)
        typer.echo(f"wrote product readiness results to {out}")
        return
    if mode != "research":
        raise typer.BadParameter("mode must be research or product_readiness")
    task_rows = attach_leakage_to_tasks(task_rows, bundle)
    split_rows = read_task_splits(splits)
    rankings, diagnostics = rank_tasks(task_rows, bundle, corpus, graph, splits=split_rows, include_diagnostics=True)
    validation_context = build_validation_context(artifacts, bundle)
    results = evaluate_rankings(
        task_rows,
        rankings,
        split_task_ids=split_task_ids_for_evaluation(task_rows, split_rows),
        validation_context=validation_context,
    )
    results.update(diagnostics)
    write_results(results, out)
    typer.echo(f"wrote results to {out}")


@app.command("train-feedback")
def train_feedback(
    feedback: Path = typer.Option(..., "--feedback"),
    artifacts: Path = typer.Option(..., "--artifacts"),
    out: Path = typer.Option(..., "--out"),
    tenant_id: str | None = typer.Option(None, "--tenant-id"),
    integration_id: str | None = typer.Option(None, "--integration-id"),
    global_model: bool = typer.Option(False, "--global-model"),
    allow_synthetic: bool = typer.Option(False, "--allow-synthetic"),
) -> None:
    import tempfile

    bundle = read_normalized_bundle(artifacts)
    source_events = read_feedback_events(feedback)
    filtered_events = []
    for event in source_events:
        if tenant_id and event.get("tenant_id") != tenant_id:
            continue
        if integration_id and event.get("integration_id") != integration_id:
            continue
        if global_model and event.get("label_quality") != "explicit":
            continue
        if not allow_synthetic and event.get("label_quality") == "synthetic":
            continue
        filtered_events.append(event)
    training_path = feedback
    temp_name = None
    if filtered_events != source_events:
        handle = tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", suffix=".jsonl")
        temp_name = handle.name
        with handle:
            for event in filtered_events:
                handle.write(json.dumps(event, sort_keys=True) + "\n")
        training_path = Path(temp_name)
    manifest = train_feedback_ranker(training_path, bundle, out)
    manifest.update(
        {
            "source_event_count": len(source_events),
            "filtered_event_count": len(filtered_events),
            "tenant_id": tenant_id,
            "integration_id": integration_id,
            "training_scope": "global_explicit_only" if global_model else "tenant_or_integration_first",
            "synthetic_allowed": allow_synthetic,
            "promotion_status": "not_promoted_shadow_evaluation_required",
        }
    )
    feedback_manifest_path(out).write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if temp_name:
        Path(temp_name).unlink(missing_ok=True)
    typer.echo(json.dumps(manifest, indent=2))


@app.command("route")
def route(
    query: str = typer.Option(..., "--query"),
    artifacts: Path = typer.Option(..., "--artifacts"),
    provided_params: str = typer.Option("{}", "--provided-params"),
    confirmed: bool = typer.Option(False, "--confirmed"),
    feedback_log: Path | None = typer.Option(None, "--feedback-log"),
    feedback_model: Path | None = typer.Option(None, "--feedback-model"),
) -> None:
    bundle = read_normalized_bundle(artifacts)
    corpus = read_rag_corpus(artifacts)
    graph = read_graph(artifacts)
    indices = build_retrieval_indices(bundle, corpus, graph)
    parsed_params = json.loads(provided_params)
    if not isinstance(parsed_params, dict):
        raise typer.BadParameter("--provided-params must be a JSON object")
    decision = route_product_query(
        query,
        bundle,
        indices,
        provided_params=parsed_params,
        confirmed=confirmed,
        feedback_log=feedback_log,
        feedback_model=feedback_model,
    )
    record = decision.to_record()
    if feedback_log is not None:
        write_feedback_event(
            feedback_log,
            FeedbackEvent(
                query=query,
                decision_type=decision.decision_type,
                top_candidates=decision.top_candidates,
                selected_endpoint=decision.selected_endpoint,
                confidence=decision.confidence,
                missing_params=decision.missing_params,
                follow_up_question=decision.follow_up_question,
                validation_result={"status": "not_validated"},
                execution_result={"status": "dry_run"},
                source="runtime",
            ),
        )
    typer.echo(json.dumps(record, indent=2))


@app.command("chat-route")
def chat_route(
    query: str = typer.Option(..., "--query"),
    artifacts: Path = typer.Option(..., "--artifacts"),
    tenant_id: str = typer.Option("sandbox-tenant", "--tenant-id"),
    integration_id: str = typer.Option("sandbox-integration", "--integration-id"),
    guardrails: str = typer.Option("{}", "--guardrails"),
    conversation_context: str = typer.Option("[]", "--conversation-context"),
    feedback_log: Path | None = typer.Option(None, "--feedback-log"),
    feedback_model: Path | None = typer.Option(None, "--feedback-model"),
    use_model: bool = typer.Option(False, "--use-model"),
) -> None:
    parsed_guardrails = json.loads(guardrails)
    if not isinstance(parsed_guardrails, dict):
        raise typer.BadParameter("--guardrails must be a JSON object")
    parsed_guardrails["use_model_normalization"] = use_model
    parsed_context = json.loads(conversation_context)
    if not isinstance(parsed_context, list):
        raise typer.BadParameter("--conversation-context must be a JSON array")
    decision = route_tool_request(
        tenant_id=tenant_id,
        integration_id=integration_id,
        user_query=query,
        conversation_context=parsed_context,
        artifacts_path=str(artifacts),
        guardrail_config=parsed_guardrails,
        feedback_log_path=str(feedback_log) if feedback_log else None,
        feedback_model_path=str(feedback_model) if feedback_model else None,
    )
    typer.echo(json.dumps(decision.model_dump(mode="json"), indent=2))


@app.command("feedback-log")
def feedback_log_command(
    out: Path = typer.Option(..., "--out"),
    tenant_id: str = typer.Option(..., "--tenant-id"),
    integration_id: str = typer.Option(..., "--integration-id"),
    query: str = typer.Option(..., "--query"),
    decision_type: str = typer.Option(..., "--decision-type"),
    selected_endpoint: str | None = typer.Option(None, "--selected-endpoint"),
    user_selected_endpoint: str | None = typer.Option(None, "--user-selected-endpoint"),
    corrected_endpoint: str | None = typer.Option(None, "--corrected-endpoint"),
    rejected_endpoint: list[str] = typer.Option([], "--rejected-endpoint"),
    feedback_source: str = typer.Option("user", "--feedback-source"),
    label_quality: str = typer.Option("explicit", "--label-quality"),
) -> None:
    from datetime import datetime, timezone
    import uuid

    event = StandardFeedbackEvent(
        event_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        integration_id=integration_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
        query=query,
        conversation_context_hash="manual",
        decision_type=decision_type,
        selected_endpoint=selected_endpoint,
        user_selected_endpoint=user_selected_endpoint,
        corrected_endpoint=corrected_endpoint,
        rejected_endpoints=list(rejected_endpoint),
        feedback_source=feedback_source,  # type: ignore[arg-type]
        label_quality=label_quality,  # type: ignore[arg-type]
    )
    record = write_standard_feedback_event(out, event)
    typer.echo(json.dumps(record, indent=2))


@app.command("evaluate-feedback")
def evaluate_feedback(
    feedback: Path = typer.Option(..., "--feedback"),
    artifacts: Path = typer.Option(..., "--artifacts"),
    out: Path = typer.Option(..., "--out"),
    tasks: list[Path] = typer.Option([], "--tasks"),
    feedback_model: Path | None = typer.Option(None, "--feedback-model"),
) -> None:
    bundle = read_normalized_bundle(artifacts)
    corpus = read_rag_corpus(artifacts)
    graph = read_graph(artifacts)
    indices = build_retrieval_indices(bundle, corpus, graph)
    events = read_standard_feedback_events(feedback)
    result: dict[str, object] = {
        "feedback_path": str(feedback),
        "event_count": len(events),
        "explicit_count": sum(1 for event in events if event.get("label_quality") == "explicit"),
        "synthetic_count": sum(1 for event in events if event.get("label_quality") == "synthetic"),
        "model_status": "loaded" if feedback_model and feedback_model.exists() else "not_loaded",
        "promotion": "shadow_evaluation_required",
    }
    if tasks:
        task_rows = [task for task_path in tasks for task in read_tasks(task_path)]
        result["shadow_evaluation"] = evaluate_product_readiness(
            task_rows,
            bundle,
            indices,
            feedback_log=feedback,
            feedback_model=feedback_model if feedback_model and feedback_model.exists() else None,
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    write_results(result, out)
    typer.echo(f"wrote feedback evaluation to {out}")


@app.command("sandbox")
def sandbox(
    artifacts: Path = typer.Option(Path("artifacts"), "--artifacts"),
    feedback_log: Path = typer.Option(Path("data/sandbox_feedback_events.jsonl"), "--feedback-log"),
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8765, "--port"),
    guardrails: str = typer.Option('{"mode":"suggest"}', "--guardrails"),
) -> None:
    from sandbox.server import run_sandbox

    parsed_guardrails = json.loads(guardrails)
    if not isinstance(parsed_guardrails, dict):
        raise typer.BadParameter("--guardrails must be a JSON object")
    run_sandbox(host=host, port=port, artifacts=artifacts, feedback_log=feedback_log, guardrails=parsed_guardrails)


@app.command("split-tasks")
def split_tasks(tasks: list[Path] = typer.Option(..., "--tasks"), out: Path = typer.Option(..., "--out")) -> None:
    task_rows = [task for task_path in tasks for task in read_tasks(task_path)]
    splits = build_task_splits(task_rows)
    write_task_splits(splits, out)
    typer.echo(f"wrote task splits to {out}")


@app.command("task-audit")
def task_audit(
    tasks: Path = typer.Option(..., "--tasks"),
    artifacts: Path = typer.Option(..., "--artifacts"),
    out: Path = typer.Option(..., "--out"),
    splits: Path | None = typer.Option(None, "--splits"),
) -> None:
    task_rows = read_tasks(tasks)
    bundle = read_normalized_bundle(artifacts)
    split_rows = read_task_splits(splits)
    write_task_audit(task_rows, bundle, out, split_by_task=primary_split_by_task(split_rows))
    typer.echo(f"wrote task audit to {out}")


@app.command("leakage-audit")
def leakage_audit(
    tasks: Path = typer.Option(..., "--tasks"),
    artifacts: Path = typer.Option(..., "--artifacts"),
    out: Path = typer.Option(..., "--out"),
) -> None:
    task_rows = read_tasks(tasks)
    bundle = read_normalized_bundle(artifacts)
    rows = write_leakage_audit(task_rows, bundle, out)
    typer.echo(f"wrote {len(rows)} leakage audit rows to {out}")


@app.command("report")
def report(results: Path = typer.Option(..., "--results"), out: Path = typer.Option(..., "--out")) -> None:
    write_reports(read_results(results), out)
    typer.echo(f"wrote reports to {out}")


@app.command("medusa-smoke")
def medusa_smoke(creds: Path = typer.Option(..., "--creds"), base_url: str | None = typer.Option(None, "--base-url"), out: Path = typer.Option(Path("medusa_smoke_result.json"), "--out")) -> None:
    result = run_medusa_smoke(creds, base_url)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    typer.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    app()
