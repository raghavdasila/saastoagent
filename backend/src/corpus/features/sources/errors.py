class SourceIntegrationError(RuntimeError):
    """A registered source connector failed its explicit contract."""


class SourceInputError(SourceIntegrationError):
    pass


class SourceDependencyError(SourceIntegrationError):
    pass


class SourceArtifactError(SourceIntegrationError):
    pass


__all__ = [
    "SourceArtifactError",
    "SourceDependencyError",
    "SourceInputError",
    "SourceIntegrationError",
]
