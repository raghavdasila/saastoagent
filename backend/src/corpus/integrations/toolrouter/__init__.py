"""Corpus-facing ToolRouter integration.

Feature code imports the public adapter contracts from this package. The
vendored engine remains private to the integration boundary.
"""

from .adapter import ToolRouterAdapter
from .contracts import (
    EvalsetRequest,
    EvalsetResult,
    IngestRequest,
    IngestResult,
    ManagedParameter,
    RankedEndpoint,
    RetrievalRequest,
    RetrievalResult,
    RetrievalStep,
    TraceMode,
)
from .errors import (
    ToolRouterArtifactError,
    ToolRouterDependencyError,
    ToolRouterInputError,
    ToolRouterIntegrationError,
)
from .settings import ToolRouterSettings

__all__ = [
    "EvalsetRequest",
    "EvalsetResult",
    "IngestRequest",
    "IngestResult",
    "ManagedParameter",
    "RankedEndpoint",
    "RetrievalRequest",
    "RetrievalResult",
    "RetrievalStep",
    "ToolRouterAdapter",
    "ToolRouterArtifactError",
    "ToolRouterDependencyError",
    "ToolRouterInputError",
    "ToolRouterIntegrationError",
    "ToolRouterSettings",
    "TraceMode",
]
