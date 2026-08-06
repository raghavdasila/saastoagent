from routedeck_core.app import (
    BoundApplication,
    CompiledApplication,
    FeatureBindings,
    bind_app,
)

from .app.agents_adapters import AuthAgentOwnerScopeGateway
from .app.lounge_adapters import (
    AuthLoungeAccountGateway,
    AuthLoungeCredentialTransition,
    AuthLoungeMailDelivery,
    AuthLoungeRateLimiter,
)
from .auth.routedeck import OWNER_CONTEXT_PROVIDER, OwnerContextProvider
from .features.agents.bindings import create_agents_bindings
from .features.agents.service import AgentService
from .features.lounge.bindings import create_lounge_bindings
from .features.lounge.private_forms import EncryptedLoungePrivateFormReader
from .features.workspace.bindings import create_workspace_bindings
from .features.workspace.service import WorkspaceService
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
    agent_service: AgentService,
    workspace_service: WorkspaceService,
) -> BoundApplication:
    lounge = create_lounge_bindings(
        account=AuthLoungeAccountGateway(auth_service),
        limiter=AuthLoungeRateLimiter(auth_limiter),
        mail=AuthLoungeMailDelivery(auth_mail),
        public_frontend_url=str(auth_settings.public_frontend_url),
        private_forms=EncryptedLoungePrivateFormReader(
            private_form_store,
            private_form_codec,
        ),
        credential_transition=AuthLoungeCredentialTransition(
            credential_transition
        ),
    )
    workspace = create_workspace_bindings(workspace_service)
    agents = create_agents_bindings(
        agent_service,
        AuthAgentOwnerScopeGateway(auth_service),
    )
    sources = create_sources_bindings()
    return bind_app(
        app,
        FeatureBindings(
            handlers={
                **lounge.handlers,
                **workspace.handlers,
                **agents.handlers,
                **sources.handlers,
            },
            providers={
                OWNER_CONTEXT_PROVIDER.ref: OwnerContextProvider(
                    owner_context_resolver
                ),
                **workspace.providers,
                **agents.providers,
                **sources.providers,
            },
            guards={
                **workspace.guards,
                **agents.guards,
                **sources.guards,
            },
        ),
    )


__all__ = ["bind_corpus_app"]
