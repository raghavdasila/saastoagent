class ToolRouterIntegrationError(RuntimeError):
    """Base error for the replaceable Corpus ToolRouter boundary."""


class ToolRouterInputError(ToolRouterIntegrationError):
    """The supplied API collection cannot produce valid ToolRouter artifacts."""


class ToolRouterDependencyError(ToolRouterIntegrationError):
    """A required local parser, embedding model, or model service is unavailable."""


class ToolRouterArtifactError(ToolRouterIntegrationError):
    """Persisted ToolRouter artifacts are missing, corrupt, or incompatible."""


__all__ = [
    "ToolRouterArtifactError",
    "ToolRouterDependencyError",
    "ToolRouterInputError",
    "ToolRouterIntegrationError",
]

