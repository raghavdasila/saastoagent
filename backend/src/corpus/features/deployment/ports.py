from __future__ import annotations

from typing import Protocol

from corpus.shared.agent_delivery import (
    ActivationProjection,
    DeployableBundleSpec,
    DeploymentProjection,
)


class DeploymentUnavailable(RuntimeError):
    pass


class DeploymentConflict(RuntimeError):
    pass


class DeploymentDeliveryPort(Protocol):
    def request_deployment(
        self, channel_id: str, spec: DeployableBundleSpec
    ) -> DeploymentProjection: ...

    def rollback(
        self, channel_id: str, deployment_id: str
    ) -> ActivationProjection: ...


__all__ = [
    "DeploymentConflict",
    "DeploymentDeliveryPort",
    "DeploymentUnavailable",
]
