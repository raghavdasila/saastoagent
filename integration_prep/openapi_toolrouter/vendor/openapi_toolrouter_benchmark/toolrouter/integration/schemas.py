from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


DecisionType = Literal["ROUTE", "SHOW_TOPK", "ASK_PARAM", "ASK_DISAMBIGUATE", "ASK_POLICY", "BLOCK_UNSAFE"]
GuardrailMode = Literal["observe", "suggest", "dry_run", "auto_read", "confirm_write", "block_write"]
MissingParamPolicy = Literal["ask_user", "ask_agent", "block"]
WriteRisk = Literal["read", "write", "destructive"]
FeedbackSource = Literal["user", "agent", "validator", "executor", "benchmark"]
LabelQuality = Literal["explicit", "implicit", "synthetic"]


class ChatRouteInput(BaseModel):
    router_query: str
    provided_params: dict[str, Any] = Field(default_factory=dict)
    confirmed: bool = False
    policy_text: str = ""


class ToolRouteCandidate(BaseModel):
    endpoint_id: str
    method: str
    path: str
    summary: str = ""
    confidence: float = 0.0
    reasons: list[str] = Field(default_factory=list)
    required_params: list[str] = Field(default_factory=list)
    missing_params: list[str] = Field(default_factory=list)
    write_risk: WriteRisk = "read"


class GuardrailDecision(BaseModel):
    mode: GuardrailMode = "observe"
    requires_confirmation: bool = False
    reason: str = ""


class ValidationResult(BaseModel):
    required_params_covered: bool = False
    request_body_schema_pass: bool = False
    validation_pass: bool = False
    errors: list[str] = Field(default_factory=list)


class ToolRouteDecision(BaseModel):
    decision_type: DecisionType
    selected_endpoint: str | None = None
    selected_method: str | None = None
    selected_path: str | None = None
    top_candidates: list[ToolRouteCandidate] = Field(default_factory=list)
    confidence: float = 0.0
    missing_params: list[str] = Field(default_factory=list)
    follow_up_question: str | None = None
    guardrail_decision: GuardrailDecision = Field(default_factory=GuardrailDecision)
    validation: ValidationResult = Field(default_factory=ValidationResult)
    feedback_event_id: str | None = None


class StandardFeedbackEvent(BaseModel):
    event_id: str
    tenant_id: str
    integration_id: str
    timestamp: str
    query: str
    conversation_context_hash: str
    decision_type: str
    top_candidates: list[dict[str, Any]] = Field(default_factory=list)
    selected_endpoint: str | None = None
    user_selected_endpoint: str | None = None
    corrected_endpoint: str | None = None
    rejected_endpoints: list[str] = Field(default_factory=list)
    missing_params: list[str] = Field(default_factory=list)
    provided_params: dict[str, Any] = Field(default_factory=dict)
    follow_up_question: str | None = None
    guardrail_mode: str = ""
    validation_result: dict[str, Any] = Field(default_factory=dict)
    execution_result: dict[str, Any] | None = None
    feedback_source: FeedbackSource = "agent"
    label_quality: LabelQuality = "implicit"
