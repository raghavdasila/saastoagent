from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..decision_router import DecisionConfig, ProductDecision
from ..openapi_loader import NormalizedBundle, NormalizedEndpoint, normalize_text
from .schemas import GuardrailDecision


READ_METHODS = {"GET", "HEAD", "OPTIONS"}
WRITE_METHODS = {"POST", "PATCH", "PUT"}
DESTRUCTIVE_METHODS = {"DELETE"}
DESTRUCTIVE_EVIDENCE_TERMS = ("delete", "remove", "revoke", "cancel")
ALLOWED_MODES = {"observe", "suggest", "dry_run", "auto_read", "confirm_write", "block_write"}


@dataclass
class GuardrailConfig:
    mode: str = "observe"
    endpoint_allowlist: set[str] = field(default_factory=set)
    endpoint_denylist: set[str] = field(default_factory=set)
    tag_allowlist: set[str] = field(default_factory=set)
    tag_denylist: set[str] = field(default_factory=set)
    auth_scope_allowlist: set[str] = field(default_factory=set)
    auth_scope_denylist: set[str] = field(default_factory=set)
    missing_param_policy: str = "ask_user"
    auto_route_confidence_threshold: float = 0.42
    show_topk_min_confidence: float = 0.24
    route_margin_threshold: float = 0.06
    unsafe_write_threshold: float = 0.35
    method_policies: dict[str, str] = field(default_factory=dict)
    allow_auto_read_methods: bool = True


def parse_guardrail_config(raw: dict[str, Any] | None) -> GuardrailConfig:
    raw = raw or {}
    mode = str(raw.get("mode") or "observe")
    if mode not in ALLOWED_MODES:
        mode = "observe"
    return GuardrailConfig(
        mode=mode,
        endpoint_allowlist=set(str(item) for item in raw.get("endpoint_allowlist", []) or []),
        endpoint_denylist=set(str(item) for item in raw.get("endpoint_denylist", []) or []),
        tag_allowlist=set(normalize_text(item) for item in raw.get("tag_allowlist", []) or []),
        tag_denylist=set(normalize_text(item) for item in raw.get("tag_denylist", []) or []),
        auth_scope_allowlist=set(str(item) for item in raw.get("auth_scope_allowlist", []) or []),
        auth_scope_denylist=set(str(item) for item in raw.get("auth_scope_denylist", []) or []),
        missing_param_policy=str(raw.get("missing_param_policy") or "ask_user"),
        auto_route_confidence_threshold=float(raw.get("auto_route_confidence_threshold", raw.get("route_confidence_threshold", 0.42))),
        show_topk_min_confidence=float(raw.get("show_topk_min_confidence", raw.get("show_topk_confidence_threshold", 0.24))),
        route_margin_threshold=float(raw.get("route_margin_threshold", 0.06)),
        unsafe_write_threshold=float(raw.get("unsafe_write_threshold", 0.35)),
        method_policies={str(k).upper(): str(v) for k, v in (raw.get("method_policies", {}) or {}).items()},
        allow_auto_read_methods=bool(raw.get("allow_auto_read_methods", True)),
    )


def decision_config_from_guardrails(config: GuardrailConfig) -> DecisionConfig:
    return DecisionConfig(
        route_confidence_threshold=config.auto_route_confidence_threshold,
        route_margin_threshold=config.route_margin_threshold,
        param_confidence_threshold=0.0,
        show_topk_confidence_threshold=config.show_topk_min_confidence,
        unsafe_write_threshold=config.unsafe_write_threshold,
    )


def endpoint_write_risk(endpoint: NormalizedEndpoint | None) -> str:
    if endpoint is None:
        return "read"
    method = endpoint.method.upper()
    evidence = normalize_text(" ".join([endpoint.operation_class, endpoint.path, endpoint.summary, endpoint.description]))
    if method in DESTRUCTIVE_METHODS or endpoint.operation_class == "delete":
        return "destructive"
    if method in WRITE_METHODS:
        if any(term in evidence for term in DESTRUCTIVE_EVIDENCE_TERMS):
            return "destructive"
        return "write"
    return "read"


def endpoint_denial_reason(endpoint: NormalizedEndpoint, config: GuardrailConfig) -> str | None:
    if endpoint.id in config.endpoint_denylist:
        return f"{endpoint.id} is denied by endpoint policy."
    if config.endpoint_allowlist and endpoint.id not in config.endpoint_allowlist:
        return f"{endpoint.id} is not in the endpoint allowlist."
    tags = {normalize_text(tag) for tag in endpoint.tags}
    if tags & config.tag_denylist:
        return f"{endpoint.id} has a denied OpenAPI tag."
    if config.tag_allowlist and not (tags & config.tag_allowlist):
        return f"{endpoint.id} does not match the tag allowlist."
    auth_scopes = set(endpoint.security)
    if auth_scopes & config.auth_scope_denylist:
        return f"{endpoint.id} uses a denied auth scope."
    if config.auth_scope_allowlist and not (auth_scopes & config.auth_scope_allowlist):
        return f"{endpoint.id} does not match the auth scope allowlist."
    return None


def apply_guardrails(
    decision: ProductDecision,
    bundle: NormalizedBundle,
    config: GuardrailConfig,
    *,
    confirmed: bool,
) -> tuple[str, str | None, GuardrailDecision]:
    selected_id = decision.selected_endpoint
    endpoint = bundle.endpoint_by_id(selected_id) if selected_id else None
    if endpoint is None and decision.candidate_endpoint_ids:
        try:
            endpoint = bundle.endpoint_by_id(decision.candidate_endpoint_ids[0])
        except KeyError:
            endpoint = None
    risk = endpoint_write_risk(endpoint)
    mode = config.mode

    if decision.decision_type == "ASK_PARAM":
        if config.missing_param_policy == "block":
            return "BLOCK_UNSAFE", None, GuardrailDecision(mode=mode, requires_confirmation=True, reason="Missing parameter policy blocks incomplete calls.")
        return decision.decision_type, selected_id, GuardrailDecision(mode=mode, requires_confirmation=False, reason="Required OpenAPI parameters are missing.")

    if endpoint is not None:
        denied = endpoint_denial_reason(endpoint, config)
        if denied:
            return "BLOCK_UNSAFE", None, GuardrailDecision(mode=mode, requires_confirmation=True, reason=denied)

    if decision.decision_type == "BLOCK_UNSAFE":
        if endpoint is not None:
            return "BLOCK_UNSAFE", None, GuardrailDecision(mode=mode, requires_confirmation=True, reason=f"{endpoint.method} {endpoint.path} is {risk} and requires explicit confirmation.")
        return decision.decision_type, selected_id, GuardrailDecision(mode=mode, requires_confirmation=True, reason=decision.decision_reason)

    if decision.decision_type in {"ASK_POLICY", "ASK_DISAMBIGUATE", "SHOW_TOPK"}:
        if mode == "suggest" and decision.decision_type == "ASK_DISAMBIGUATE":
            return "SHOW_TOPK", None, GuardrailDecision(mode=mode, requires_confirmation=False, reason="Suggest mode keeps routing as user-visible candidates.")
        return decision.decision_type, selected_id, GuardrailDecision(mode=mode, requires_confirmation=decision.decision_type == "BLOCK_UNSAFE", reason=decision.decision_reason)

    if mode == "suggest":
        return "SHOW_TOPK", None, GuardrailDecision(mode=mode, requires_confirmation=False, reason="Suggest mode keeps routing as user-visible candidates.")

    if endpoint is None:
        return decision.decision_type, selected_id, GuardrailDecision(mode=mode, requires_confirmation=False, reason="No endpoint selected.")

    method_policy = config.method_policies.get(endpoint.method.upper())
    if method_policy == "block":
        return "BLOCK_UNSAFE", None, GuardrailDecision(mode=mode, requires_confirmation=True, reason=f"{endpoint.method} {endpoint.path} is blocked by method policy.")
    if method_policy == "confirm" and not confirmed:
        return "BLOCK_UNSAFE", None, GuardrailDecision(mode=mode, requires_confirmation=True, reason=f"{endpoint.method} {endpoint.path} requires explicit confirmation by method policy.")

    if risk == "read":
        if mode == "auto_read" and endpoint.method.upper() not in READ_METHODS:
            return "BLOCK_UNSAFE", None, GuardrailDecision(mode=mode, requires_confirmation=True, reason=f"{endpoint.method} is not configured for auto-read.")
        return decision.decision_type, selected_id, GuardrailDecision(mode=mode, requires_confirmation=False, reason="Read endpoint allowed by guardrails.")

    if mode == "block_write":
        return "BLOCK_UNSAFE", None, GuardrailDecision(mode=mode, requires_confirmation=True, reason=f"{endpoint.method} {endpoint.path} is {risk} and block_write is enabled.")
    if mode == "confirm_write" and not confirmed:
        return "BLOCK_UNSAFE", None, GuardrailDecision(mode=mode, requires_confirmation=True, reason=f"{endpoint.method} {endpoint.path} is {risk} and requires explicit confirmation.")
    if mode == "auto_read":
        return "BLOCK_UNSAFE", None, GuardrailDecision(mode=mode, requires_confirmation=True, reason=f"{endpoint.method} {endpoint.path} is {risk}; auto_read permits reads only.")
    if mode == "dry_run":
        return decision.decision_type, selected_id, GuardrailDecision(mode=mode, requires_confirmation=False, reason=f"{endpoint.method} {endpoint.path} allowed as dry-run route only.")
    if mode == "confirm_write" and confirmed:
        return decision.decision_type, selected_id, GuardrailDecision(mode=mode, requires_confirmation=False, reason=f"{endpoint.method} {endpoint.path} confirmed; adapter still returns dry-run routing only.")
    return decision.decision_type, selected_id, GuardrailDecision(mode=mode, requires_confirmation=False, reason="Observe mode records the decision without relaxing execution guardrails.")
