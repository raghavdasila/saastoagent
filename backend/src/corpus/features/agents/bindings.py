from routedeck_core.app import FeatureBindings

from .declarations import (
    AGENT_ENTITY_PROVIDER,
    ARCHIVE_AGENT,
    ARCHIVE_CURRENT_GUARD,
    ATTACH_CREATED_SOURCE,
    ATTACH_SOURCE,
    CANCEL_CREATE,
    CREATE_AGENT,
    DELETE_AGENT,
    DELETE_DEPENDENCIES_GUARD,
    OPEN_ATTACHED_SOURCE,
    OPEN_AGENT_BUILDS,
    OPEN_AGENT_CHANNELS,
    OPEN_AGENT_DESIGNER,
    OPEN_AGENT_EVALUATION,
    OPEN_AGENT_OPERATIONS,
    OPEN_AGENT_SANDBOX,
    OPEN_BUILD_SOURCE_REVISION,
    OPEN_CREATE,
    OPEN_SOURCE_CREATION,
    RETURN_FROM_SOURCE,
    RETURN_TO_AGENT_HUB,
    RETURN_TO_WORKSPACE,
    SAVE_AGENT_CHANGES,
    SELECT_AGENT,
)
from .operations import (
    AgentNavigationHandler,
    AgentLifecycleHandler,
    AttachSourceHandler,
    CreateAgentHandler,
    OpenAttachedSourceHandler,
    OpenAgentAreaHandler,
    OpenBuildSourceRevisionHandler,
    OpenSourceCreationHandler,
    ReturnFromSourceHandler,
    SaveAgentChangesHandler,
    SelectAgentHandler,
)
from .guards import ArchiveCurrentGuard, DeleteDependenciesGuard
from .ports import AgentOwnerScopeGateway
from .service import AgentService
from .providers import SelectedAgentProvider


def create_agents_bindings(
    service: AgentService,
    owner_scope: AgentOwnerScopeGateway,
) -> FeatureBindings:
    return FeatureBindings(
        handlers={
            OPEN_CREATE.ref: AgentNavigationHandler(OPEN_CREATE.id),
            RETURN_TO_WORKSPACE.ref: AgentNavigationHandler(RETURN_TO_WORKSPACE.id),
            RETURN_TO_AGENT_HUB.ref: OpenAgentAreaHandler(service, owner_scope, RETURN_TO_AGENT_HUB.id, "hub"),
            CANCEL_CREATE.ref: AgentNavigationHandler(CANCEL_CREATE.id),
            CREATE_AGENT.ref: CreateAgentHandler(service, owner_scope),
            SAVE_AGENT_CHANGES.ref: SaveAgentChangesHandler(service, owner_scope),
            SELECT_AGENT.ref: SelectAgentHandler(service, owner_scope),
            ARCHIVE_AGENT.ref: AgentLifecycleHandler(service, owner_scope, ARCHIVE_AGENT.id),
            DELETE_AGENT.ref: AgentLifecycleHandler(service, owner_scope, DELETE_AGENT.id),
            ATTACH_SOURCE.ref: AttachSourceHandler(service, owner_scope, ATTACH_SOURCE.id),
            ATTACH_CREATED_SOURCE.ref: AttachSourceHandler(service, owner_scope, ATTACH_CREATED_SOURCE.id),
            OPEN_SOURCE_CREATION.ref: OpenSourceCreationHandler(service, owner_scope),
            OPEN_ATTACHED_SOURCE.ref: OpenAttachedSourceHandler(service, owner_scope),
            OPEN_AGENT_OPERATIONS.ref: OpenAgentAreaHandler(service, owner_scope, OPEN_AGENT_OPERATIONS.id, "operations"),
            OPEN_AGENT_DESIGNER.ref: OpenAgentAreaHandler(service, owner_scope, OPEN_AGENT_DESIGNER.id, "designer"),
            OPEN_AGENT_BUILDS.ref: OpenAgentAreaHandler(service, owner_scope, OPEN_AGENT_BUILDS.id, "builds"),
            OPEN_AGENT_SANDBOX.ref: OpenAgentAreaHandler(service, owner_scope, OPEN_AGENT_SANDBOX.id, "sandbox"),
            OPEN_AGENT_EVALUATION.ref: OpenAgentAreaHandler(service, owner_scope, OPEN_AGENT_EVALUATION.id, "evaluation"),
            OPEN_AGENT_CHANNELS.ref: OpenAgentAreaHandler(service, owner_scope, OPEN_AGENT_CHANNELS.id, "channels"),
            OPEN_BUILD_SOURCE_REVISION.ref: OpenBuildSourceRevisionHandler(service, owner_scope),
            RETURN_FROM_SOURCE.ref: ReturnFromSourceHandler(service, owner_scope),
        },
        providers={AGENT_ENTITY_PROVIDER.ref: SelectedAgentProvider()},
        guards={
            ARCHIVE_CURRENT_GUARD.ref: ArchiveCurrentGuard(service, owner_scope),
            DELETE_DEPENDENCIES_GUARD.ref: DeleteDependenciesGuard(service, owner_scope),
        },
    )


__all__ = ["create_agents_bindings"]
