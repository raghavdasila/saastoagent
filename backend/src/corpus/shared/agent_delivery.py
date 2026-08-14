from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class DeployableBundleSpec:
    bundle_id: str
    name: str
    version: str
    content_hash: str
    routedeck_app_hash: str
    surface_contract_hash: str
    eligibility_hash: str
    runtime_kind: str
    runtime_config: Mapping[str, Any]


@dataclass(frozen=True)
class ChannelProjection:
    channel_id: str
    name: str
    slug: str
    enabled: bool


@dataclass(frozen=True)
class DeploymentProjection:
    deployment_id: str
    channel_id: str
    bundle_id: str
    bundle_hash: str
    status: str
    failure_code: str | None
    failure_message: str | None


@dataclass(frozen=True)
class ActivationProjection:
    activation_id: str
    channel_id: str
    deployment_id: str
    reason: str


@dataclass(frozen=True)
class PublicSessionProjection:
    session_id: str
    channel_id: str
    activation_id: str
    deployment_id: str


@dataclass(frozen=True)
class PublicAgentProjection:
    revision: int
    messages: tuple[Mapping[str, Any], ...]
    surfaces: tuple[Mapping[str, Any], ...]
    suggested_actions: tuple[Mapping[str, Any], ...]


@dataclass(frozen=True)
class InteractionProjection:
    interaction_id: str
    session_id: str
    deployment_id: str
    input_summary: str
    output_summary: str
    status: str
    trace: Mapping[str, Any]


@dataclass(frozen=True)
class EvaluationCandidateProjection:
    candidate_id: str
    interaction_id: str
    deployment_id: str
    input_summary: str
    output_summary: str
    trace: Mapping[str, Any]
