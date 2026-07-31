from routedeck_core.app import (
    BoundApplication,
    CompiledApplication,
    FeatureBindings,
    bind_app,
)

from .features.lounge.bindings import create_lounge_bindings
from .features.lounge.private_forms import EncryptedLoungePrivateFormReader
from .features.workspace.bindings import create_workspace_bindings
from .features.sources.bindings import create_sources_bindings


def bind_corpus_app(
    app: CompiledApplication,
    owner_context_resolver,
    *,
    auth_service,
    auth_limiter,
    auth_mail,
    auth_settings,
    private_form_store,
    private_form_codec,
    credential_transition,
) -> BoundApplication:
    lounge = create_lounge_bindings(
        service=auth_service,
        limiter=auth_limiter,
        mail=auth_mail,
        settings=auth_settings,
        private_forms=EncryptedLoungePrivateFormReader(
            private_form_store,
            private_form_codec,
        ),
        credential_transition=credential_transition,
    )
    workspace = create_workspace_bindings(owner_context_resolver)
    sources = create_sources_bindings()
    return bind_app(
        app,
        FeatureBindings(
            handlers={**lounge.handlers, **workspace.handlers, **sources.handlers},
            providers={**workspace.providers, **sources.providers},
            guards={**workspace.guards, **sources.guards},
        ),
    )


__all__ = ["bind_corpus_app"]
