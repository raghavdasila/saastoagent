from __future__ import annotations

from pathlib import Path
from typing import Any

from ..decision_router import missing_required_params, route_product_query
from ..feedback import feedback_adjustments
from ..graphgen import read_graph
from ..openapi_loader import NormalizedBundle, NormalizedEndpoint, read_normalized_bundle
from ..raggen import read_rag_corpus
from ..retrieval_indices import build_retrieval_indices
from ..validation import build_validation_context
from .chat import normalize_chat_request
from .feedback import feedback_event_from_decision, write_standard_feedback_event
from .guardrails import apply_guardrails, decision_config_from_guardrails, endpoint_write_risk, parse_guardrail_config
from .schemas import GuardrailDecision, ToolRouteCandidate, ToolRouteDecision, ValidationResult


def _endpoint_or_none(bundle: NormalizedBundle, endpoint_id: str | None) -> NormalizedEndpoint | None:
    if not endpoint_id:
        return None
    try:
        return bundle.endpoint_by_id(endpoint_id)
    except KeyError:
        return None


def _candidate_records(bundle: NormalizedBundle, product_decision: Any, provided_params: dict[str, Any]) -> list[ToolRouteCandidate]:
    candidates: list[ToolRouteCandidate] = []
    for row in product_decision.top_candidates:
        endpoint = _endpoint_or_none(bundle, row.get("endpoint_id"))
        if endpoint is None:
            continue
        missing = missing_required_params(endpoint, bundle, product_decision.query, provided_params)
        candidates.append(
            ToolRouteCandidate(
                endpoint_id=endpoint.id,
                method=endpoint.method,
                path=endpoint.path,
                summary=endpoint.summary,
                confidence=float(row.get("confidence", row.get("score", 0.0))),
                reasons=[str(row.get("reason") or "")],
                required_params=list(endpoint.required_params),
                missing_params=missing,
                write_risk=endpoint_write_risk(endpoint),  # type: ignore[arg-type]
            )
        )
    return candidates


def _validation_result(artifacts_path: Path, bundle: NormalizedBundle, endpoint: NormalizedEndpoint | None, missing_params: list[str]) -> ValidationResult:
    if endpoint is None:
        return ValidationResult(required_params_covered=not missing_params, errors=["no_selected_endpoint"])
    try:
        validation_context = build_validation_context(artifacts_path, bundle)
        raw = validation_context.validate_endpoint_request(endpoint)
    except Exception as exc:
        return ValidationResult(
            required_params_covered=not missing_params,
            request_body_schema_pass=False,
            validation_pass=False,
            errors=[f"{exc.__class__.__name__}: {exc}"],
        )
    errors: list[str] = []
    if raw.get("validation_status") not in {"passed", None}:
        errors.append(str(raw.get("validation_status")))
    if raw.get("request_body_status") not in {"passed", "not_applicable", None}:
        errors.append(str(raw.get("request_body_status")))
    return ValidationResult(
        required_params_covered=not missing_params,
        request_body_schema_pass=bool(float(raw.get("request_body_schema_pass", 0.0))),
        validation_pass=bool(float(raw.get("validation_pass", 0.0))),
        errors=errors,
    )


def _promote_clear_short_goal(product_decision: Any, bundle: NormalizedBundle, provided_params: dict[str, Any], threshold: float) -> None:
    if product_decision.decision_type != "ASK_DISAMBIGUATE":
        return
    if product_decision.decision_reason != "vague_query_disambiguation":
        return
    if len(str(product_decision.query or "").split()) < 2:
        return
    if product_decision.confidence < threshold:
        return
    if not product_decision.candidate_endpoint_ids:
        return
    endpoint = _endpoint_or_none(bundle, product_decision.candidate_endpoint_ids[0])
    if endpoint is None:
        return
    missing = missing_required_params(endpoint, bundle, product_decision.query, provided_params)
    if missing:
        product_decision.decision_type = "ASK_PARAM"
        product_decision.selected_endpoint = endpoint.id
        product_decision.missing_params = missing
        product_decision.follow_up_question = f"I can use {endpoint.method} {endpoint.path}, but I need {', '.join(missing)} before preparing the call."
        product_decision.decision_reason = "missing_required_inputs"
        return
    product_decision.decision_type = "ROUTE"
    product_decision.selected_endpoint = endpoint.id
    product_decision.decision_reason = "clear_short_goal_route"
    product_decision.follow_up_question = ""


def route_tool_request(
    tenant_id: str,
    integration_id: str,
    user_query: str,
    conversation_context: list[dict] | None,
    artifacts_path: str,
    guardrail_config: dict,
    feedback_log_path: str | None,
    feedback_model_path: str | None,
) -> ToolRouteDecision:
    artifacts = Path(artifacts_path)
    guardrails = parse_guardrail_config(guardrail_config)
    normalized = normalize_chat_request(
        user_query=user_query,
        conversation_context=conversation_context,
        model=str((guardrail_config or {}).get("openai_router_model") or "gpt-5-nano"),
        use_model=bool((guardrail_config or {}).get("use_model_normalization", False)),
    )
    bundle = read_normalized_bundle(artifacts)
    corpus = read_rag_corpus(artifacts)
    graph = read_graph(artifacts)
    indices = build_retrieval_indices(bundle, corpus, graph)
    feedback_log = Path(feedback_log_path) if feedback_log_path else None
    feedback_model = Path(feedback_model_path) if feedback_model_path else None
    if feedback_model is not None and not feedback_model.exists():
        feedback_model = None
    product_decision = route_product_query(
        normalized.router_query,
        bundle,
        indices,
        provided_params=normalized.provided_params,
        confirmed=normalized.confirmed,
        feedback_stats=feedback_adjustments(feedback_log),
        feedback_log=feedback_log,
        feedback_model=feedback_model,
        config=decision_config_from_guardrails(guardrails),
    )
    _promote_clear_short_goal(product_decision, bundle, normalized.provided_params, guardrails.auto_route_confidence_threshold)
    decision_type, selected_id, guardrail_decision = apply_guardrails(product_decision, bundle, guardrails, confirmed=normalized.confirmed)
    selected_endpoint = _endpoint_or_none(bundle, selected_id)
    missing_params = list(product_decision.missing_params)
    candidates = _candidate_records(bundle, product_decision, normalized.provided_params)
    validation = _validation_result(artifacts, bundle, selected_endpoint, missing_params)
    follow_up_question = product_decision.follow_up_question or None
    if decision_type == "ROUTE":
        follow_up_question = None
    elif decision_type == "BLOCK_UNSAFE" and not follow_up_question:
        follow_up_question = guardrail_decision.reason
    decision = ToolRouteDecision(
        decision_type=decision_type,  # type: ignore[arg-type]
        selected_endpoint=selected_endpoint.id if selected_endpoint else None,
        selected_method=selected_endpoint.method if selected_endpoint else None,
        selected_path=selected_endpoint.path if selected_endpoint else None,
        top_candidates=candidates,
        confidence=float(product_decision.confidence),
        missing_params=missing_params,
        follow_up_question=follow_up_question,
        guardrail_decision=guardrail_decision if isinstance(guardrail_decision, GuardrailDecision) else GuardrailDecision(),
        validation=validation,
    )
    if feedback_log is not None:
        event = feedback_event_from_decision(
            tenant_id=tenant_id,
            integration_id=integration_id,
            query=user_query,
            conversation_context=conversation_context,
            decision=decision,
            provided_params=normalized.provided_params,
        )
        record = write_standard_feedback_event(feedback_log, event)
        decision.feedback_event_id = str(record["event_id"])
    return decision
