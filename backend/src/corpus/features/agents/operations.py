from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
import uuid

from pydantic import ValidationError
from pydantic import SecretStr
from routedeck_core.contracts.effects import (
    EntityBindingEffect,
    EntityKindEffects,
    PublicSurfaceEffect,
    SessionEffects,
)
from routedeck_core.contracts.failures import FailureKind, FailureSafeDetails, RouteDeckFailure
from routedeck_core.contracts.operations import DeliveryPhase, OperationOutcome
from routedeck_core.contracts.projection import FrozenJson, PublicEntityHandle, PublicValue
from routedeck_core.ports.executor import ExecutionContext

from corpus.features.sources.contracts import API_CONNECTION_FORM_ID
from corpus.auth.contracts import AgentOwnerScopeGateway, AgentOwnerScopeUnavailable

from .declarations import (
    ATTACH_CREATED_SOURCE,
    ATTACH_SOURCE,
    DETACH_SOURCE,
    ARCHIVE_AGENT,
    CANCEL_CREATE,
    CREATE_AGENT,
    DELETE_AGENT,
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
    OPEN_EXISTING_AGENT_FOR_SOURCE,
    RETURN_FROM_SOURCE,
    RETURN_TO_AGENT_HUB,
    SAVE_AGENT_CHANGES,
    SELECT_AGENT,
)
from .ports import (
    AgentBuildLineageUnavailable,
    AgentNameConflict,
    AgentDependencyConflict,
    AgentLifecycleConflict,
    AgentNotFound,
    AgentSourceAttachmentConflict,
    AgentSourceAttachmentUnavailable,
    AgentVersionConflict,
    AttachableSource,
)
from .schemas import (
    AgentLifecycleArguments,
    attach_source_arguments,
    DetachSourceArguments,
    CreateAgentArguments,
    OpenAgentChoiceForSourceArguments,
    OpenAgentCreationArguments,
    SelectAgentArguments,
    UpdateAgentArguments,
    OpenBuildSourceReferenceArguments,
    OpenAttachedSourceArguments,
)
from .service import AgentService


@dataclass(frozen=True)
class CreateAgentHandler:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        try:
            payload = CreateAgentArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(
                context.session_id
            )
            agent = await self.service.create(organization_id, payload)
        except (ValidationError, ValueError) as error:
            return _failure(context, CREATE_AGENT.id, "invalid_agent", str(error), FailureKind.CONTRACT)
        except AgentNameConflict as error:
            return _failure(context, CREATE_AGENT.id, "agent_name_conflict", str(error), FailureKind.BUSINESS)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, CREATE_AGENT.id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        handle = f"agent-{agent.id.hex[:20]}"
        return _success(
            "created",
            effects=_agent_surface_effects(
                handle,
                str(agent.id),
                pending_source=_pending_source(context),
            ),
)


_SELECTED_AGENT_OPERATION_IDS = (
    ATTACH_SOURCE.id,
    DETACH_SOURCE.id,
    ARCHIVE_AGENT.id,
    DELETE_AGENT.id,
    OPEN_SOURCE_CREATION.id,
    OPEN_ATTACHED_SOURCE.id,
    OPEN_AGENT_OPERATIONS.id,
    OPEN_AGENT_DESIGNER.id,
    OPEN_AGENT_BUILDS.id,
    OPEN_AGENT_SANDBOX.id,
    OPEN_AGENT_EVALUATION.id,
    OPEN_AGENT_CHANNELS.id,
    OPEN_BUILD_SOURCE_REVISION.id,
)


@dataclass(frozen=True)
class SaveAgentChangesHandler:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        try:
            payload = UpdateAgentArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(
                context.session_id
            )
            await self.service.update(organization_id, payload)
        except (ValidationError, ValueError) as error:
            return _failure(context, SAVE_AGENT_CHANGES.id, "invalid_agent", str(error), FailureKind.CONTRACT)
        except AgentNotFound as error:
            return _failure(context, SAVE_AGENT_CHANGES.id, "agent_unavailable", str(error), FailureKind.BUSINESS)
        except AgentNameConflict as error:
            return _failure(context, SAVE_AGENT_CHANGES.id, "agent_name_conflict", str(error), FailureKind.BUSINESS)
        except AgentVersionConflict as error:
            return _failure(context, SAVE_AGENT_CHANGES.id, "agent_version_conflict", str(error), FailureKind.STATE_CONFLICT)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, SAVE_AGENT_CHANGES.id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        return _success("saved")


@dataclass(frozen=True)
class SelectAgentHandler:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments: Mapping[str, Any], context: ExecutionContext) -> OperationOutcome:
        try:
            payload = SelectAgentArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            agent = await self.service.get(organization_id, payload.agent_id)
        except ValidationError as error:
            return _failure(context, SELECT_AGENT.id, "invalid_agent_selection", str(error), FailureKind.CONTRACT)
        except AgentNotFound as error:
            return _failure(context, SELECT_AGENT.id, "agent_unavailable", str(error), FailureKind.BUSINESS)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, SELECT_AGENT.id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        handle = f"agent-{agent.id.hex[:20]}"
        pending_source = _pending_source(context)
        surface_values = [PublicValue(name="selected_agent_ref", value=FrozenJson(handle))]
        surface_values.extend(_pending_source_values(pending_source))
        effects = SessionEffects(
            replace_entities=(
                EntityKindEffects(
                    entity_kind="agent",
                    bindings=(
                        EntityBindingEffect(
                            public=PublicEntityHandle(
                                entity_kind="agent",
                                handle=handle,
                                values=(
                                    PublicValue(name="name", value=FrozenJson(agent.name)),
                                    PublicValue(name="current_version", value=FrozenJson(agent.current_version)),
                                ),
                            ),
                            private_id=SecretStr(str(agent.id)),
                            allowed_operation_ids=_SELECTED_AGENT_OPERATION_IDS,
                        ),
                    ),
                ),
            ),
            surface_updates=(
                PublicSurfaceEffect(
                    surface_id="agents.home",
                    values=tuple(surface_values),
                ),
            ),
        )
        return _success("selected", effects=effects)


@dataclass(frozen=True)
class AgentLifecycleHandler:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway
    operation_id: str

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        try:
            AgentLifecycleArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(
                context.session_id
            )
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            if self.operation_id == ARCHIVE_AGENT.id:
                await self.service.archive(organization_id, agent_id)
                outcome = "archived"
            elif self.operation_id == DELETE_AGENT.id:
                await self.service.delete(organization_id, agent_id)
                outcome = "deleted"
            else:
                raise ValueError("Unsupported Agent lifecycle operation.")
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, self.operation_id, "invalid_agent_selection", str(error), FailureKind.CONTRACT)
        except AgentNotFound as error:
            return _failure(context, self.operation_id, "agent_unavailable", str(error), FailureKind.BUSINESS)
        except AgentLifecycleConflict as error:
            return _failure(context, self.operation_id, "agent_lifecycle_conflict", str(error), FailureKind.STATE_CONFLICT)
        except AgentDependencyConflict as error:
            return _failure(context, self.operation_id, "agent_dependency_conflict", str(error), FailureKind.STATE_CONFLICT)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, self.operation_id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        return _success(
            outcome,
            effects=SessionEffects(
                replace_entities=(EntityKindEffects(entity_kind="agent"),),
                surface_updates=(PublicSurfaceEffect(surface_id="agents.home"),),
            ),
        )


@dataclass(frozen=True)
class AttachSourceHandler:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway
    operation_id: str

    async def __call__(self, arguments: Mapping[str, Any], context: ExecutionContext) -> OperationOutcome:
        try:
            payload = attach_source_arguments(arguments, context.source)
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            await self.service.get(organization_id, agent_id)
            pending_source = _pending_source(context)
            source_id = payload.source_id
            source_revision_id = payload.source_revision_id
            if pending_source is not None:
                pending_id, pending_revision_id, _ = pending_source
                if source_id is not None and source_id != pending_id:
                    raise ValueError("The pending Source cannot be substituted.")
                if source_revision_id is not None and source_revision_id != pending_revision_id:
                    raise ValueError("The pending API version cannot be substituted.")
                source_id = pending_id
                source_revision_id = pending_revision_id
            if source_id is None:
                attachable = await self.service.one_attachable_ready_source(
                    organization_id,
                    agent_id,
                )
                source_id = attachable.source_id
                source_revision_id = attachable.source_revision_id
            await self.service.attach_source(
                organization_id,
                agent_id,
                source_id,
                source_revision_id,
            )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, self.operation_id, "invalid_source_attachment", str(error), FailureKind.CONTRACT)
        except AgentNotFound as error:
            return _failure(context, self.operation_id, "agent_unavailable", str(error), FailureKind.BUSINESS)
        except AgentSourceAttachmentConflict as error:
            return _failure(context, self.operation_id, "source_attachment_conflict", str(error), FailureKind.STATE_CONFLICT)
        except AgentSourceAttachmentUnavailable as error:
            return _failure(context, self.operation_id, "source_attachment_unavailable", str(error), FailureKind.BUSINESS)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, self.operation_id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        effects = _agent_surface_effects(
            payload.agent_ref,
            context.private_entity_id("agent_ref"),
        )
        return _success("attached", effects=effects)


@dataclass(frozen=True)
class DetachSourceHandler:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments: Mapping[str, Any], context: ExecutionContext) -> OperationOutcome:
        try:
            payload = DetachSourceArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            await self.service.detach_source(
                organization_id,
                agent_id,
                payload.source_id,
            )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, DETACH_SOURCE.id, "invalid_source_detachment", str(error), FailureKind.CONTRACT)
        except AgentNotFound as error:
            return _failure(context, DETACH_SOURCE.id, "agent_unavailable", str(error), FailureKind.BUSINESS)
        except AgentSourceAttachmentUnavailable as error:
            return _failure(context, DETACH_SOURCE.id, "source_attachment_unavailable", str(error), FailureKind.BUSINESS)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, DETACH_SOURCE.id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        return _success(
            "detached",
            effects=_agent_surface_effects(
                payload.agent_ref,
                context.private_entity_id("agent_ref"),
            ),
        )


@dataclass(frozen=True)
class OpenExistingAgentForSourceHandler:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments: Mapping[str, Any], context: ExecutionContext) -> OperationOutcome:
        try:
            payload = OpenAgentChoiceForSourceArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            source = await self.service.exact_ready_source(
                organization_id,
                payload.source_id,
                payload.source_revision_id,
            )
            selected_agent = await self.service.one_agent_attached_to_source(
                organization_id,
                source.source_id,
            )
        except (ValidationError, ValueError) as error:
            return _failure(context, OPEN_EXISTING_AGENT_FOR_SOURCE.id, "invalid_source_choice", str(error), FailureKind.CONTRACT)
        except AgentSourceAttachmentUnavailable as error:
            return _failure(context, OPEN_EXISTING_AGENT_FOR_SOURCE.id, "source_unavailable", str(error), FailureKind.BUSINESS)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, OPEN_EXISTING_AGENT_FOR_SOURCE.id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        if selected_agent is None:
            effects = _pending_source_open_effects("agents.home", source)
        else:
            effects = _agent_surface_effects(
                f"agent-{selected_agent.id.hex[:20]}",
                str(selected_agent.id),
                pending_source=(
                    source.source_id,
                    source.source_revision_id,
                    source.display_name,
                ),
            )
        return _success("opened", effects=effects)


@dataclass(frozen=True)
class OpenAgentCreationHandler:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments: Mapping[str, Any], context: ExecutionContext) -> OperationOutcome:
        try:
            payload = OpenAgentCreationArguments.model_validate(dict(arguments))
            if payload.source_id is None or payload.source_revision_id is None:
                return _success("opened")
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            source = await self.service.exact_ready_source(
                organization_id,
                payload.source_id,
                payload.source_revision_id,
            )
        except (ValidationError, ValueError) as error:
            return _failure(context, OPEN_CREATE.id, "invalid_source_choice", str(error), FailureKind.CONTRACT)
        except AgentSourceAttachmentUnavailable as error:
            return _failure(context, OPEN_CREATE.id, "source_unavailable", str(error), FailureKind.BUSINESS)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, OPEN_CREATE.id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        return _success(
            "opened",
            effects=_pending_source_open_effects("agents.create", source),
        )


class CancelAgentCreationHandler:
    async def __call__(self, arguments: Mapping[str, Any], context: ExecutionContext) -> OperationOutcome:
        if arguments:
            raise ValueError(f"{CANCEL_CREATE.id} accepts no arguments")
        pending_source = _pending_source(context)
        if pending_source is None:
            return _success("opened")
        return _success(
            "opened",
            effects=_pending_source_transition_effects("agents.home", pending_source),
        )


@dataclass(frozen=True)
class OpenSourceCreationHandler:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments: Mapping[str, Any], context: ExecutionContext) -> OperationOutcome:
        try:
            agent_ref = str(arguments["agent_ref"])
            if set(arguments) != {"agent_ref"} or not agent_ref:
                raise ValueError("An exact selected Agent is required.")
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            await self.service.get(organization_id, agent_id)
        except (ValueError, KeyError) as error:
            return _failure(context, OPEN_SOURCE_CREATION.id, "invalid_agent_selection", str(error), FailureKind.CONTRACT)
        except AgentNotFound as error:
            return _failure(context, OPEN_SOURCE_CREATION.id, "agent_unavailable", str(error), FailureKind.BUSINESS)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, OPEN_SOURCE_CREATION.id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        return _success(
            "opened",
            effects=_source_surface_effects(
                agent_ref,
                context.private_entity_id("agent_ref"),
                mode="create",
                allowed_operation_ids=(ATTACH_CREATED_SOURCE.id, RETURN_FROM_SOURCE.id),
            ),
        )


@dataclass(frozen=True)
class OpenAttachedSourceHandler:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments: Mapping[str, Any], context: ExecutionContext) -> OperationOutcome:
        try:
            payload = OpenAttachedSourceArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            await self.service.get(organization_id, agent_id)
            source_id = payload.source_id
            if source_id is None:
                attachments = (
                    await self.service.list_source_attachments(
                        organization_id, agent_id
                    )
                ).attachments
                if len(attachments) != 1:
                    raise AgentSourceAttachmentUnavailable(
                        "Opening Source context requires one exact attached Source; select one in the Agent surface."
                    )
                source_id = attachments[0].source_id
            attachment = await self.service.open_attached_source(
                organization_id,
                agent_id,
                source_id,
            )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, OPEN_ATTACHED_SOURCE.id, "invalid_attached_source", str(error), FailureKind.CONTRACT)
        except AgentNotFound as error:
            return _failure(context, OPEN_ATTACHED_SOURCE.id, "agent_unavailable", str(error), FailureKind.BUSINESS)
        except AgentSourceAttachmentUnavailable as error:
            return _failure(context, OPEN_ATTACHED_SOURCE.id, "attached_source_unavailable", str(error), FailureKind.BUSINESS)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, OPEN_ATTACHED_SOURCE.id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        return _success(
            "opened",
            effects=_source_surface_effects(
                payload.agent_ref,
                context.private_entity_id("agent_ref"),
                mode="inspect",
                source_id=source_id,
                source_revision_id=attachment.source_revision_id,
                allowed_operation_ids=(
                    (OPEN_AGENT_BUILDS.id,)
                    if payload.return_to == "builder"
                    else (RETURN_FROM_SOURCE.id,)
                ),
                return_context=payload.return_to,
                initial_workspace=payload.target_stage,
            ),
        )


@dataclass(frozen=True)
class ReturnFromSourceHandler:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments: Mapping[str, Any], context: ExecutionContext) -> OperationOutcome:
        try:
            agent_ref = str(arguments["agent_ref"])
            if set(arguments) != {"agent_ref"} or not agent_ref:
                raise ValueError("An exact selected Agent is required.")
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            await self.service.get(organization_id, uuid.UUID(context.private_entity_id("agent_ref")))
            pending_source = await _selected_source_update_pending(
                self.service,
                organization_id,
                context,
            )
        except (ValueError, KeyError) as error:
            return _failure(context, RETURN_FROM_SOURCE.id, "invalid_agent_selection", str(error), FailureKind.CONTRACT)
        except AgentNotFound as error:
            return _failure(context, RETURN_FROM_SOURCE.id, "agent_unavailable", str(error), FailureKind.BUSINESS)
        except AgentSourceAttachmentUnavailable as error:
            return _failure(context, RETURN_FROM_SOURCE.id, "source_unavailable", str(error), FailureKind.BUSINESS)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, RETURN_FROM_SOURCE.id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        return _success(
            "opened",
            effects=_agent_surface_effects(
                agent_ref,
                context.private_entity_id("agent_ref"),
                pending_source=pending_source,
            ),
        )


class AgentNavigationHandler:
    def __init__(self, operation_id: str) -> None:
        self.operation_id = operation_id

    async def __call__(self, arguments, context) -> OperationOutcome:
        del context
        if arguments:
            raise ValueError(f"{self.operation_id} accepts no arguments")
        return _success("opened")


@dataclass(frozen=True)
class OpenAgentAreaHandler:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway
    operation_id: str
    area: str

    async def __call__(self, arguments, context) -> OperationOutcome:
        try:
            payload = AgentLifecycleArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            await self.service.get(organization_id, agent_id)
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, self.operation_id, "invalid_agent_selection", str(error), FailureKind.CONTRACT)
        except AgentNotFound as error:
            return _failure(context, self.operation_id, "agent_unavailable", str(error), FailureKind.BUSINESS)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, self.operation_id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        if self.area == "hub":
            effects = _agent_surface_effects(
                payload.agent_ref,
                context.private_entity_id("agent_ref"),
            )
        elif self.area == "designer":
            effects = _designer_surface_effects(
                    payload.agent_ref,
                    context.private_entity_id("agent_ref"),
                )
        else:
            surface_id, operation_ids = {
                "builds": (
                    "builder.home",
                    (
                        "builder.assemble",
                        "builder.run",
                        "builder.pause",
                        "builder.stop",
                        "builder.delete",
                        OPEN_ATTACHED_SOURCE.id,
                        OPEN_AGENT_SANDBOX.id,
                    ),
                ),
                "sandbox": ("sandbox.home", ("sandbox.start", "sandbox.resume", OPEN_AGENT_EVALUATION.id)),
                "evaluation": (
                    "evaluation.home",
                    (
                        "evaluation.create_case",
                        "evaluation.generate_set",
                        "evaluation.retry_generation",
                        "evaluation.edit_case",
                        "evaluation.delete_case",
                        "evaluation.run_case",
                        "evaluation.retry_case_run",
                        OPEN_AGENT_BUILDS.id,
                        OPEN_AGENT_CHANNELS.id,
                    ),
                ),
                "channels": (
                    "channels.home",
                    (
                        "channels.create",
                        "channels.set_enabled",
                        "deployment.deploy",
                        "deployment.rollback",
                        OPEN_AGENT_EVALUATION.id,
                        OPEN_AGENT_OPERATIONS.id,
                    ),
                ),
                "operations": ("operations.home", ("operations.promote_evaluation_case",)),
            }[self.area]
            effects = _external_agent_surface_effects(
                    payload.agent_ref,
                    context.private_entity_id("agent_ref"),
                    surface_id=surface_id,
                    operation_ids=operation_ids,
                )
        return _success("opened", effects=effects)


@dataclass(frozen=True)
class OpenBuildSourceRevisionHandler:
    service: AgentService
    owner_scope: AgentOwnerScopeGateway

    async def __call__(self, arguments, context) -> OperationOutcome:
        try:
            payload = OpenBuildSourceReferenceArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            await self.service.require_build_source_reference(
                organization_id,
                agent_id,
                build_id=payload.build_id,
                source_id=payload.source_id,
                source_revision_id=payload.source_revision_id,
            )
        except (ValidationError, ValueError, KeyError) as error:
            return _failure(context, OPEN_BUILD_SOURCE_REVISION.id, "invalid_build_source_reference", str(error), FailureKind.CONTRACT)
        except (AgentNotFound, AgentBuildLineageUnavailable) as error:
            return _failure(context, OPEN_BUILD_SOURCE_REVISION.id, "build_source_reference_unavailable", str(error), FailureKind.BUSINESS)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, OPEN_BUILD_SOURCE_REVISION.id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        return _success(
            "opened",
            effects=_source_surface_effects(
                payload.agent_ref,
                context.private_entity_id("agent_ref"),
                mode="inspect",
                source_id=payload.source_id,
                source_revision_id=payload.source_revision_id,
                allowed_operation_ids=(RETURN_FROM_SOURCE.id,),
            ),
        )


def _source_surface_effects(
    agent_ref: str,
    private_agent_id: str,
    *,
    mode: str,
    allowed_operation_ids: tuple[str, ...],
    source_id: str | None = None,
    source_revision_id: str | None = None,
    return_context: str = "agent",
    initial_workspace: str = "graph",
) -> SessionEffects:
    shared_values = [
        PublicValue(name="return_agent_ref", value=FrozenJson(agent_ref)),
        PublicValue(name="agent_handoff_mode", value=FrozenJson(mode)),
    ]
    if source_id is not None:
        shared_values.append(PublicValue(name="selected_source_id", value=FrozenJson(source_id)))
    if source_revision_id is not None:
        shared_values.append(PublicValue(name="selected_source_revision_id", value=FrozenJson(source_revision_id)))
        if mode == "inspect":
            shared_values.append(
                PublicValue(
                    name="attached_source_revision_id",
                    value=FrozenJson(source_revision_id),
                )
            )
    surface_id = "sources.api_intake" if mode == "create" else "sources.api"
    surface_values = [
        *shared_values,
        PublicValue(name="mode", value=FrozenJson(mode)),
    ]
    if mode == "inspect":
        surface_values.extend((
            PublicValue(name="return_context", value=FrozenJson(return_context)),
            PublicValue(name="initial_workspace", value=FrozenJson(initial_workspace)),
        ))
        surface_values.append(
            PublicValue(name="form_handle", value=FrozenJson(API_CONNECTION_FORM_ID))
        )
    return SessionEffects(
        replace_entities=(
            _agent_binding_effect(
                agent_ref,
                private_agent_id,
                allowed_operation_ids,
                public_values=(
                    (
                        PublicValue(name="attached_source_id", value=FrozenJson(source_id)),
                        PublicValue(
                            name="attached_source_revision_id",
                            value=FrozenJson(source_revision_id),
                        ),
                    )
                    if mode == "inspect"
                    and source_id is not None
                    and source_revision_id is not None
                    else ()
                ),
            ),
        ),
        surface_updates=(
            PublicSurfaceEffect(
                surface_id=surface_id,
                values=tuple(surface_values),
            ),
        )
    )


def _pending_source(context: ExecutionContext) -> tuple[str, str, str] | None:
    provider_values = getattr(context, "provider_values", None)
    if provider_values is None:
        return None
    values = provider_values.to_dict().get("agents.pending_source", {})
    if not isinstance(values, dict):
        return None
    source_id = values.get("source_id")
    revision_id = values.get("source_revision_id")
    display_name = values.get("display_name")
    if (
        not isinstance(source_id, str)
        or len(source_id) != 16
        or not isinstance(revision_id, str)
        or len(revision_id) != 16
    ):
        return None
    if not isinstance(display_name, str) or not display_name:
        display_name = source_id
    return source_id, revision_id, display_name


async def _selected_source_update_pending(
    service: AgentService,
    organization_id: uuid.UUID,
    context: ExecutionContext,
) -> tuple[str, str, str] | None:
    provider_values = getattr(context, "provider_values", None)
    if provider_values is None:
        return None
    values = provider_values.to_dict().get("sources.selected_api_source", {})
    if not isinstance(values, dict) or values.get("attachment_update_available") is not True:
        return None
    source_id = values.get("source_id")
    revision_id = values.get("source_revision_id")
    if (
        not isinstance(source_id, str)
        or len(source_id) != 16
        or not isinstance(revision_id, str)
        or len(revision_id) != 16
    ):
        raise AgentSourceAttachmentUnavailable(
            "The newer ready Source version is unavailable for Agent handoff."
        )
    source = await service.exact_ready_source(
        organization_id,
        source_id,
        revision_id,
    )
    return source.source_id, source.source_revision_id, source.display_name


def _pending_source_values(
    pending_source: tuple[str, str, str] | None,
) -> list[PublicValue]:
    if pending_source is None:
        return []
    source_id, revision_id, display_name = pending_source
    return [
        PublicValue(name="pending_source_id", value=FrozenJson(source_id)),
        PublicValue(name="pending_source_revision_id", value=FrozenJson(revision_id)),
        PublicValue(name="pending_source_display_name", value=FrozenJson(display_name)),
        PublicValue(name="pending_source_ready", value=FrozenJson(True)),
    ]


def _pending_source_open_effects(
    surface_id: str,
    source: AttachableSource,
) -> SessionEffects:
    pending = (
        source.source_id,
        source.source_revision_id,
        source.display_name,
    )
    return _pending_source_transition_effects(surface_id, pending)


def _pending_source_transition_effects(
    surface_id: str,
    pending_source: tuple[str, str, str],
) -> SessionEffects:
    return SessionEffects(
        replace_entities=(EntityKindEffects(entity_kind="agent"),),
        surface_updates=(
            PublicSurfaceEffect(
                surface_id=surface_id,
                values=tuple(_pending_source_values(pending_source)),
            ),
        ),
    )


def _agent_surface_effects(
    agent_ref: str,
    private_agent_id: str,
    *,
    area: str = "hub",
    pending_source: tuple[str, str, str] | None = None,
) -> SessionEffects:
    surface_values = [
        PublicValue(name="selected_agent_ref", value=FrozenJson(agent_ref)),
        PublicValue(name="selected_agent_area", value=FrozenJson(area)),
    ]
    surface_values.extend(_pending_source_values(pending_source))
    return SessionEffects(
        replace_entities=(
            _agent_binding_effect(
                agent_ref,
                private_agent_id,
                _SELECTED_AGENT_OPERATION_IDS,
            ),
        ),
        surface_updates=(
            PublicSurfaceEffect(
                surface_id="agents.home",
                values=tuple(surface_values),
            ),
        )
    )


def _designer_surface_effects(agent_ref: str, private_agent_id: str) -> SessionEffects:
    return SessionEffects(
        replace_entities=(
            _agent_binding_effect(
                agent_ref,
                private_agent_id,
                (
                    "designer.propose",
                    "designer.generate_feature",
                    "designer.customize",
                    "designer.approve",
                    "designer.request_build",
                    OPEN_ATTACHED_SOURCE.id,
                    OPEN_AGENT_BUILDS.id,
                    "designer.return_to_agent",
                ),
            ),
        ),
        surface_updates=(
            PublicSurfaceEffect(
                surface_id="designer.home",
                values=(PublicValue(name="selected_agent_ref", value=FrozenJson(agent_ref)),),
            ),
        ),
    )


def _external_agent_surface_effects(
    agent_ref: str,
    private_agent_id: str,
    *,
    surface_id: str,
    operation_ids: tuple[str, ...],
) -> SessionEffects:
    return SessionEffects(
        replace_entities=(
            _agent_binding_effect(
                agent_ref,
                private_agent_id,
                operation_ids + (RETURN_TO_AGENT_HUB.id,),
            ),
        ),
        surface_updates=(
            PublicSurfaceEffect(
                surface_id=surface_id,
                values=(PublicValue(name="selected_agent_ref", value=FrozenJson(agent_ref)),),
            ),
        ),
    )


def _agent_binding_effect(
    agent_ref: str,
    private_agent_id: str,
    allowed_operation_ids: tuple[str, ...],
    public_values: tuple[PublicValue, ...] = (),
) -> EntityKindEffects:
    return EntityKindEffects(
        entity_kind="agent",
        bindings=(
            EntityBindingEffect(
                public=PublicEntityHandle(
                    entity_kind="agent",
                    handle=agent_ref,
                    values=public_values,
                ),
                private_id=SecretStr(private_agent_id),
                allowed_operation_ids=allowed_operation_ids,
            ),
        ),
    )


def _success(outcome: str, *, effects: SessionEffects | None = None) -> OperationOutcome:
    return OperationOutcome(
        outcome=outcome,
        delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
        effects=effects or SessionEffects(),
    )


def _failure(context, operation_id, code, message, kind) -> OperationOutcome:
    return OperationOutcome(
        delivery_phase=DeliveryPhase.NOT_SENT,
        failure=RouteDeckFailure(
            kind=kind,
            code=code,
            phase="agents_service",
            correlation_id=context.attempt_id,
            operation_id=operation_id,
            request_id=context.request_id,
            public_message=message,
            safe_details=FailureSafeDetails(
                delivery_phase=DeliveryPhase.NOT_SENT.value
            ),
        ),
    )


__all__ = [
    "AgentNavigationHandler",
    "AgentLifecycleHandler",
    "AttachSourceHandler",
    "DetachSourceHandler",
    "CancelAgentCreationHandler",
    "CreateAgentHandler",
    "OpenAttachedSourceHandler",
    "OpenAgentCreationHandler",
    "OpenAgentAreaHandler",
    "OpenBuildSourceRevisionHandler",
    "OpenExistingAgentForSourceHandler",
    "OpenSourceCreationHandler",
    "ReturnFromSourceHandler",
    "SaveAgentChangesHandler",
    "SelectAgentHandler",
]
