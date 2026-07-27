from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from routedeck_core.app import FeatureBindings
from routedeck_core.contracts.operations import DeliveryPhase, OperationOutcome
from routedeck_core.ports.executor import ExecutionContext

from .declarations import RETURN_TO_HOME


class SourcesNavigationHandler:
    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        del context
        if arguments:
            raise ValueError(f"{RETURN_TO_HOME.id} accepts no arguments")
        return OperationOutcome(
            outcome="opened",
            delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
        )


def create_sources_bindings() -> FeatureBindings:
    return FeatureBindings(
        handlers={RETURN_TO_HOME.ref: SourcesNavigationHandler()},
        providers={},
        guards={},
    )


__all__ = ["create_sources_bindings"]
