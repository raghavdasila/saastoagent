from routedeck_core.app import (
    BoundApplication,
    CompiledApplication,
    FeatureBindings,
    bind_app,
)

from .features.workspace.bindings import create_workspace_bindings
from .features.sources.bindings import create_sources_bindings


def bind_corpus_app(app: CompiledApplication, owner_context_resolver) -> BoundApplication:
    workspace = create_workspace_bindings(owner_context_resolver)
    sources = create_sources_bindings()
    return bind_app(
        app,
        FeatureBindings(
            handlers={**workspace.handlers, **sources.handlers},
            providers={**workspace.providers, **sources.providers},
            guards={**workspace.guards, **sources.guards},
        ),
    )


__all__ = ["bind_corpus_app"]
