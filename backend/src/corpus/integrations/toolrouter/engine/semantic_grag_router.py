from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from .semantic_outcomes import CapabilityAssessor, validate_outcome_payload
from .semantic_graph_retrieval import EndpointReranker, EndpointScore, QueryExpander, SemanticGraphIndex, route_semantic_only


@dataclass(frozen=True)
class RouteStep:
    query: str
    ranked_endpoints: list[EndpointScore]
    trace: dict[str, Any]

    @property
    def top_endpoint_id(self) -> str | None:
        return self.ranked_endpoints[0].endpoint_id if self.ranked_endpoints else None


@dataclass(frozen=True)
class SemanticRoutePlan:
    query: str
    steps: list[RouteStep]
    decomposed: bool
    decision_type: str
    ambiguity: dict[str, Any] | None = None
    decision_reason: str = "legacy_unspecified"
    missing_params: tuple[str, ...] = ()
    decision_evidence: dict[str, Any] = field(default_factory=dict)


class SemanticGRAGRouter:
    def __init__(
        self,
        semantic_index: SemanticGraphIndex,
        *,
        reranker: EndpointReranker | None = None,
        query_expander: QueryExpander | None = None,
        rerank_limit: int = 25,
        ambiguity_margin: float = 0.08,
        card_limit: int = 12,
        max_hops: int = 3,
        decision_score_source: str = "final",
        capability_assessor: CapabilityAssessor | None = None,
        trace_mode: str = "bounded",
    ) -> None:
        if decision_score_source not in {"final", "pre_rerank"}:
            raise ValueError("decision_score_source must be 'final' or 'pre_rerank'.")
        if trace_mode not in {"bounded", "full"}:
            raise ValueError("trace_mode must be 'bounded' or 'full'.")
        self.semantic_index = semantic_index
        self.reranker = reranker
        self.query_expander = query_expander
        self.rerank_limit = rerank_limit
        self.ambiguity_margin = ambiguity_margin
        self.card_limit = card_limit
        self.max_hops = max_hops
        self.decision_score_source = decision_score_source
        self.capability_assessor = capability_assessor
        self.trace_mode = trace_mode

    def route(
        self,
        query: str,
        *,
        top_k: int = 5,
        provided_params: Mapping[str, Any] | None = None,
    ) -> SemanticRoutePlan:
        normalized_query = " ".join(str(query or "").split())
        if not normalized_query:
            return _build_plan(
                query=str(query or ""),
                steps=[],
                decomposed=False,
                decision_type="ABSTAIN",
                decision_reason="empty_query",
                decision_evidence={"capability_status": "unknown"},
            )

        capability_evidence: dict[str, Any] = {"capability_status": "not_assessed"}
        if self.capability_assessor is not None:
            assessment = self.capability_assessor.assess(normalized_query, semantic_index=self.semantic_index)
            capability_evidence = {
                "capability_status": assessment.status,
                "catalog_complete": assessment.catalog_complete,
                "catalog_evidence": [dict(value) for value in assessment.evidence],
            }
            if assessment.status == "not_covered":
                return _build_plan(
                    query=normalized_query,
                    steps=[],
                    decomposed=False,
                    decision_type="NO_TOOL",
                    decision_reason="complete_catalog_has_no_applicable_capability",
                    decision_evidence=capability_evidence,
                )
            if assessment.status == "unknown":
                return _build_plan(
                    query=normalized_query,
                    steps=[],
                    decomposed=False,
                    decision_type="ABSTAIN",
                    decision_reason="capability_assessment_insufficient",
                    decision_evidence=capability_evidence,
                )

        parts = decompose_query(normalized_query)
        steps: list[RouteStep] = []
        for part in parts:
            result = route_semantic_only(
                part,
                self.semantic_index,
                top_k=top_k,
                card_limit=self.card_limit,
                max_hops=self.max_hops,
                reranker=self.reranker,
                rerank_limit=self.rerank_limit,
                query_expander=self.query_expander,
                trace_mode=self.trace_mode,
            )
            steps.append(RouteStep(query=part, ranked_endpoints=result.ranked_endpoints, trace=result.trace))
        candidate_endpoint_ids = _candidate_endpoint_ids(steps)
        if not candidate_endpoint_ids:
            return _build_plan(
                query=normalized_query,
                steps=steps,
                decomposed=len(parts) > 1,
                decision_type="ABSTAIN",
                decision_reason="retrieval_produced_no_endpoint_evidence",
                decision_evidence=capability_evidence,
            )

        repeated_endpoint_conflict = _ambiguity_for_steps(steps)
        if repeated_endpoint_conflict is not None:
            return _build_plan(
                query=normalized_query,
                steps=steps,
                decomposed=len(parts) > 1,
                decision_type="ABSTAIN",
                decision_reason="multi_step_plan_conflict",
                ambiguity=repeated_endpoint_conflict,
                decision_evidence=capability_evidence,
            )

        ambiguity = (
            _single_step_broad_intent_ambiguity(steps)
            or _single_step_score_ambiguity(
                steps,
                self.ambiguity_margin,
                self.semantic_index,
                score_source=self.decision_score_source,
            )
        )
        if ambiguity is not None:
            return _build_plan(
                query=normalized_query,
                steps=steps,
                decomposed=len(parts) > 1,
                decision_type="ASK_DISAMBIGUATE",
                decision_reason=str(ambiguity.get("type") or "multiple_plausible_endpoints"),
                ambiguity=ambiguity,
                decision_evidence=capability_evidence,
            )

        if provided_params is not None:
            provided_names = _provided_input_names(provided_params)
            missing_by_endpoint: dict[str, list[str]] = {}
            for step in steps:
                endpoint_id = step.top_endpoint_id
                if endpoint_id is None:
                    continue
                missing = [
                    str(value["name"])
                    for value in self.semantic_index.required_inputs(endpoint_id)
                    if not _input_is_provided(
                        provided_params,
                        name=str(value["name"]),
                        location=str(value["location"]),
                    )
                ]
                if missing:
                    missing_by_endpoint[endpoint_id] = list(dict.fromkeys(missing))
            if missing_by_endpoint:
                missing_params = tuple(
                    dict.fromkeys(
                        value
                        for values in missing_by_endpoint.values()
                        for value in values
                    )
                )
                return _build_plan(
                    query=normalized_query,
                    steps=steps,
                    decomposed=len(parts) > 1,
                    decision_type="ASK_PARAM",
                    decision_reason="required_openapi_inputs_missing",
                    missing_params=missing_params,
                    decision_evidence={
                        **capability_evidence,
                        "missing_params_by_endpoint": missing_by_endpoint,
                        "provided_param_names": sorted(provided_names),
                    },
                )

        return _build_plan(
            query=normalized_query,
            steps=steps,
            decomposed=len(parts) > 1,
            decision_type="ROUTE",
            decision_reason="endpoint_evidence_sufficient",
            decision_evidence=capability_evidence,
        )


def _candidate_endpoint_ids(steps: list[RouteStep]) -> list[str]:
    return list(
        dict.fromkeys(
            endpoint.endpoint_id
            for step in steps
            for endpoint in step.ranked_endpoints
            if endpoint.endpoint_id
        )
    )


def _provided_input_names(values: Mapping[str, Any]) -> set[str]:
    names: set[str] = set()
    for key, value in values.items():
        key_text = str(key).strip().casefold()
        if isinstance(value, Mapping):
            for nested_key, nested_value in value.items():
                if nested_value is not None and not (isinstance(nested_value, str) and not nested_value.strip()):
                    names.add(str(nested_key).strip().casefold())
            continue
        if value is not None and not (isinstance(value, str) and not value.strip()):
            names.add(key_text)
    return names


def _input_is_provided(values: Mapping[str, Any], *, name: str, location: str) -> bool:
    name_key = name.strip().casefold()
    location_key = location.strip().casefold()
    location_aliases = {
        "header": ("header", "headers"),
        "path": ("path", "path_params"),
        "query": ("query", "query_params"),
        "body": ("body", "json"),
    }.get(location_key, (location_key,))

    def present(value: Any) -> bool:
        return value is not None and not (isinstance(value, str) and not value.strip())

    for outer_key, outer_value in values.items():
        if str(outer_key).strip().casefold() not in location_aliases or not isinstance(outer_value, Mapping):
            continue
        for nested_key, nested_value in outer_value.items():
            if str(nested_key).strip().casefold() == name_key and present(nested_value):
                return True
    for key, value in values.items():
        if str(key).strip().casefold() == name_key and present(value):
            return True
    return False


def _build_plan(
    *,
    query: str,
    steps: list[RouteStep],
    decomposed: bool,
    decision_type: str,
    decision_reason: str,
    ambiguity: dict[str, Any] | None = None,
    missing_params: tuple[str, ...] = (),
    decision_evidence: dict[str, Any] | None = None,
) -> SemanticRoutePlan:
    candidate_endpoint_ids = _candidate_endpoint_ids(steps)
    validate_outcome_payload(
        decision_type,
        reason=decision_reason,
        candidate_endpoint_ids=candidate_endpoint_ids,
        missing_params=missing_params,
        evidence=decision_evidence,
    )
    return SemanticRoutePlan(
        query=query,
        steps=steps,
        decomposed=decomposed,
        decision_type=decision_type,
        ambiguity=ambiguity,
        decision_reason=decision_reason,
        missing_params=missing_params,
        decision_evidence=decision_evidence or {},
    )


def decompose_query(query: str) -> list[str]:
    normalized = " ".join(str(query or "").split())
    if not normalized:
        return []
    split_pattern = re.compile(r"\s+(?:and\s+then|then|after\s+that|afterwards|next)\s+", re.IGNORECASE)
    parts = [part.strip(" ,.") for part in split_pattern.split(normalized) if part.strip(" ,.")]
    if len(parts) <= 1:
        return [normalized]
    return parts


def _ambiguity_for_steps(steps: list[RouteStep]) -> dict[str, Any] | None:
    seen: dict[str, int] = {}
    repeated: list[str] = []
    for index, step in enumerate(steps):
        top = step.top_endpoint_id
        if not top:
            continue
        if top in seen:
            repeated.append(top)
        seen[top] = index
    if not repeated:
        return None
    return {
        "type": "repeated_endpoint",
        "endpoint_ids": sorted(set(repeated)),
        "message": "Multiple decomposed steps selected the same endpoint.",
    }


def _single_step_score_ambiguity(
    steps: list[RouteStep],
    margin_threshold: float,
    semantic_index: SemanticGraphIndex | None = None,
    *,
    score_source: str = "final",
) -> dict[str, Any] | None:
    if len(steps) != 1:
        return None
    ranked = steps[0].ranked_endpoints
    if score_source == "pre_rerank":
        traced_scores = steps[0].trace.get("pre_rerank_endpoint_scores", [])
        if traced_scores:
            ranked = [
                EndpointScore(
                    endpoint_id=str(value["endpoint_id"]),
                    score=float(value["score"]),
                )
                for value in traced_scores
            ]
    elif score_source != "final":
        raise ValueError("score_source must be 'final' or 'pre_rerank'.")
    if len(ranked) < 2:
        return None
    if float(ranked[0].score) >= 0.95:
        return None
    if semantic_index is not None and _same_endpoint_identity(ranked[0].endpoint_id, ranked[1].endpoint_id, semantic_index):
        return None
    margin = float(ranked[0].score) - float(ranked[1].score)
    if margin > margin_threshold:
        return None
    return {
        "type": "low_score_margin",
        "endpoint_ids": [ranked[0].endpoint_id, ranked[1].endpoint_id],
        "margin": margin,
        "message": "Top semantic graph candidates are too close to route without disambiguation.",
    }


def _same_endpoint_identity(left_endpoint_id: str, right_endpoint_id: str, semantic_index: SemanticGraphIndex) -> bool:
    left = semantic_index.endpoint_identity(left_endpoint_id)
    right = semantic_index.endpoint_identity(right_endpoint_id)
    return left is not None and left == right


BROAD_INTENT_CUES = {
    "about",
    "area",
    "around",
    "do",
    "feature",
    "handle",
    "help",
    "manage",
    "related",
    "stuff",
    "task",
    "thing",
    "work",
}

SPECIFIC_ACTION_CUES = {
    "add",
    "archive",
    "cancel",
    "change",
    "close",
    "create",
    "delete",
    "disable",
    "download",
    "edit",
    "enable",
    "fetch",
    "find",
    "get",
    "invite",
    "list",
    "look",
    "mark",
    "make",
    "move",
    "open",
    "read",
    "regenerate",
    "register",
    "remove",
    "rename",
    "retrieve",
    "revoke",
    "save",
    "search",
    "send",
    "set",
    "subscribe",
    "unsubscribe",
    "update",
    "upload",
    "withdraw",
}


def _single_step_broad_intent_ambiguity(steps: list[RouteStep]) -> dict[str, Any] | None:
    if len(steps) != 1:
        return None
    step = steps[0]
    if not _looks_broad_without_action(step.query):
        return None
    fanout = _candidate_fanout(step)
    if len(fanout) < 3:
        return None
    return {
        "type": "broad_intent_candidate_fanout",
        "endpoint_ids": fanout[:8],
        "candidate_count": len(fanout),
        "message": "The query is broad and the semantic graph found several plausible endpoint intents.",
    }


def _looks_broad_without_action(query: str) -> bool:
    tokens = re.findall(r"[a-z0-9]+", query.casefold())
    if not tokens:
        return False
    token_set = set(tokens)
    has_broad_cue = bool(token_set & BROAD_INTENT_CUES)
    has_action_cue = bool(token_set & SPECIFIC_ACTION_CUES)
    return has_broad_cue and not has_action_cue


def _candidate_fanout(step: RouteStep) -> list[str]:
    endpoint_ids: list[str] = []
    for card in step.trace.get("top_seed_cards", []):
        if not isinstance(card, dict):
            continue
        if card.get("node_type") not in {"example_query", "action", "api_operation", "doc_chunk"}:
            continue
        endpoint_id = str(card.get("endpoint_id") or "")
        if endpoint_id and endpoint_id not in endpoint_ids:
            endpoint_ids.append(endpoint_id)
    for endpoint in step.ranked_endpoints:
        if endpoint.endpoint_id not in endpoint_ids:
            endpoint_ids.append(endpoint.endpoint_id)
    return endpoint_ids
