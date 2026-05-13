from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

QAVerdict = Literal["pass", "fail", "continue", "error"]


class QAMilestoneAction(BaseModel):
    action: str
    params: dict[str, Any] = Field(default_factory=dict)


class QAEvidenceGate(BaseModel):
    gate: str
    required: bool = True
    params: dict[str, Any] = Field(default_factory=dict)


class QAMilestone(BaseModel):
    id: str
    capability: str
    goal: str
    actions: list[QAMilestoneAction] = Field(default_factory=list)
    evidence_gates: list[QAEvidenceGate] = Field(default_factory=list)


class QAScenario(BaseModel):
    id: str
    name: str
    persona: str
    opening_message: str = ""
    context: str = ""
    pass_criteria: str = ""
    max_turns: int = 8
    milestones: list[QAMilestone] = Field(default_factory=list)


class QAScenarioListResponse(BaseModel):
    scenarios: list[QAScenario]


class QADomainModelResponse(BaseModel):
    domain: dict[str, Any]


class QAResetResponse(BaseModel):
    qa_run_id: str
    signup_email: str
    signup_password: str
    seeded_email: str
    seeded_password: str
    seeded_workspace_id: str | None = None
    seeded_workspace_name: str | None = None


class QAEvalRequest(BaseModel):
    scenario_id: str | None = None
    milestone_id: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)
    evidence_gates: list[QAEvidenceGate] = Field(default_factory=list)


class QAEvalResponse(BaseModel):
    qa_run_id: str
    verdict: QAVerdict
    confidence: float = 1.0
    reasoning: str
    gates: dict[str, bool] = Field(default_factory=dict)
    failures: list[str] = Field(default_factory=list)
