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
from .app.source_adapters import AuthSourceOwnerScopeGateway
from .auth.routedeck import OWNER_CONTEXT_PROVIDER, OwnerContextProvider
from .features.agents.bindings import create_agents_bindings
from .features.agents.operations import OpenAgentAreaHandler
from .features.agents.service import AgentService
from .features.agents.overview import AgentProductOverviewService
from .features.designer.bindings import create_designer_bindings
from .features.designer.declarations import RETURN_TO_AGENT
from .features.designer.service import DesignerService
from .features.builder.bindings import create_builder_bindings
from .features.builder.service import BuilderService
from .features.sandbox.bindings import create_sandbox_bindings
from .features.sandbox.service import SandboxService
from .features.evaluation.bindings import create_evaluation_bindings
from .features.evaluation.service import EvaluationService
from .features.channels.bindings import create_channel_bindings
from .features.channels.service import ChannelService
from .features.deployment.bindings import create_deployment_bindings
from .features.deployment.service import DeploymentService
from .features.operations.bindings import create_operations_bindings
from .features.operations.service import OperationsService
from .features.lounge.bindings import create_lounge_bindings
from .features.lounge.private_forms import EncryptedLoungePrivateFormReader
from .features.workspace.bindings import create_workspace_bindings
from .features.workspace.service import WorkspaceService
from .features.sources.bindings import create_sources_bindings
from .shared.private_forms import EncryptedPrivateFormReader


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
    designer_service: DesignerService,
    builder_service: BuilderService,
    sandbox_service: SandboxService,
    evaluation_service: EvaluationService,
    channel_service: ChannelService,
    deployment_service: DeploymentService,
    operations_service: OperationsService,
    workspace_service: WorkspaceService,
    source_service,
    source_graph_presenter,
    source_connection_service,
    source_contract_revision_service,
    source_connection_check_service,
    source_operation_curation_service,
    agent_overview_service: AgentProductOverviewService | None = None,
    source_routed_execution_service=None,
    source_staged_attachment_service=None,
    source_staged_description_service=None,
    source_lifecycle_service=None,
    source_route_plan_service=None,
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
        agent_overview_service,
    )
    designer_owner_scope = AuthAgentOwnerScopeGateway(auth_service)
    designer = create_designer_bindings(
        designer_service,
        designer_owner_scope,
        OpenAgentAreaHandler(
            agent_service,
            designer_owner_scope,
            RETURN_TO_AGENT.id,
            "hub",
        ),
    )
    builder = create_builder_bindings(builder_service, AuthAgentOwnerScopeGateway(auth_service))
    sandbox = create_sandbox_bindings(sandbox_service, AuthAgentOwnerScopeGateway(auth_service))
    evaluation = create_evaluation_bindings(evaluation_service, AuthAgentOwnerScopeGateway(auth_service))
    channels = create_channel_bindings(channel_service, AuthAgentOwnerScopeGateway(auth_service))
    deployments = create_deployment_bindings(deployment_service, AuthAgentOwnerScopeGateway(auth_service))
    operations = create_operations_bindings(operations_service, AuthAgentOwnerScopeGateway(auth_service))
    sources = create_sources_bindings(
        source_service,
        AuthSourceOwnerScopeGateway(auth_service),
        source_graph_presenter,
        source_connection_service,
        EncryptedPrivateFormReader(private_form_store, private_form_codec),
        source_contract_revision_service,
        source_connection_check_service,
        source_operation_curation_service,
        source_routed_execution_service,
        source_staged_attachment_service,
        source_staged_description_service,
        source_lifecycle_service,
        source_route_plan_service,
    )
    return bind_app(
        app,
        FeatureBindings(
            handlers={
                **lounge.handlers,
                **workspace.handlers,
                **agents.handlers,
                **designer.handlers,
                **builder.handlers,
                **sandbox.handlers,
                **evaluation.handlers,
                **channels.handlers,
                **deployments.handlers,
                **operations.handlers,
                **sources.handlers,
            },
            providers={
                OWNER_CONTEXT_PROVIDER.ref: OwnerContextProvider(
                    owner_context_resolver
                ),
                **workspace.providers,
                **agents.providers,
                **designer.providers,
                **builder.providers,
                **sandbox.providers,
                **evaluation.providers,
                **channels.providers,
                **deployments.providers,
                **operations.providers,
                **sources.providers,
            },
            guards={
                **workspace.guards,
                **agents.guards,
                **designer.guards,
                **builder.guards,
                **sandbox.guards,
                **evaluation.guards,
                **channels.guards,
                **deployments.guards,
                **operations.guards,
                **sources.guards,
            },
        ),
    )


__all__ = ["bind_corpus_app"]
