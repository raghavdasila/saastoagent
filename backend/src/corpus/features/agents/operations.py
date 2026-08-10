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

from .declarations import (
    ATTACH_CREATED_SOURCE,
    ATTACH_SOURCE,
    ARCHIVE_AGENT,
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
    OPEN_SOURCE_CREATION,
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
    AgentOwnerScopeGateway,
    AgentOwnerScopeUnavailable,
    AgentSourceAttachmentConflict,
    AgentSourceAttachmentUnavailable,
    AgentVersionConflict,
)
from .schemas import (
    AgentLifecycleArguments,
    AttachSourceArguments,
    CreateAgentArguments,
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
            effects=_agent_surface_effects(handle, str(agent.id)),
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
                            allowed_operation_ids=(
                                ATTACH_SOURCE.id,
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
                            ),
                        ),
                    ),
                ),
            ),
            surface_updates=(
                PublicSurfaceEffect(
                    surface_id="agents.home",
                    values=(PublicValue(name="selected_agent_ref", value=FrozenJson(handle)),),
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
            payload = AttachSourceArguments.model_validate(dict(arguments))
            organization_id = await self.owner_scope.organization_id_for_route(context.session_id)
            agent_id = uuid.UUID(context.private_entity_id("agent_ref"))
            await self.service.get(organization_id, agent_id)
            source_id = payload.source_id
            if source_id is None:
                source_id = (
                    await self.service.one_unattached_ready_source(
                        organization_id,
                        agent_id,
                    )
                ).source_id
            await self.service.attach_source(organization_id, agent_id, source_id)
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
        effects = SessionEffects()
        if self.operation_id == ATTACH_CREATED_SOURCE.id:
            effects = _agent_surface_effects(
                payload.agent_ref,
                context.private_entity_id("agent_ref"),
            )
        return _success("attached", effects=effects)


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
                allowed_operation_ids=(RETURN_FROM_SOURCE.id,),
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
        except (ValueError, KeyError) as error:
            return _failure(context, RETURN_FROM_SOURCE.id, "invalid_agent_selection", str(error), FailureKind.CONTRACT)
        except AgentNotFound as error:
            return _failure(context, RETURN_FROM_SOURCE.id, "agent_unavailable", str(error), FailureKind.BUSINESS)
        except AgentOwnerScopeUnavailable as error:
            return _failure(context, RETURN_FROM_SOURCE.id, "authentication_required", str(error), FailureKind.STATE_CONFLICT)
        return _success(
            "opened",
            effects=_agent_surface_effects(
                agent_ref,
                context.private_entity_id("agent_ref"),
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
                "builds": ("builder.home", ("builder.assemble",)),
                "sandbox": ("sandbox.home", ("sandbox.start", "sandbox.resume")),
                "evaluation": ("evaluation.home", ("evaluation.create_case", "evaluation.run_case")),
                "channels": (
                    "channels.home",
                    ("channels.create", "channels.set_enabled", "deployment.deploy", "deployment.rollback"),
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
) -> SessionEffects:
    shared_values = [
        PublicValue(name="return_agent_ref", value=FrozenJson(agent_ref)),
        PublicValue(name="agent_handoff_mode", value=FrozenJson(mode)),
    ]
    if source_id is not None:
        shared_values.append(PublicValue(name="selected_source_id", value=FrozenJson(source_id)))
    if source_revision_id is not None:
        shared_values.append(PublicValue(name="selected_source_revision_id", value=FrozenJson(source_revision_id)))
    return SessionEffects(
        replace_entities=(
            _agent_binding_effect(agent_ref, private_agent_id, allowed_operation_ids),
        ),
        surface_updates=(
            PublicSurfaceEffect(
                surface_id="sources.api",
                values=tuple([
                    *shared_values,
                    PublicValue(name="form_handle", value=FrozenJson(API_CONNECTION_FORM_ID)),
                    PublicValue(name="mode", value=FrozenJson(mode)),
                ]),
            ),
        )
    )


def _agent_surface_effects(
    agent_ref: str,
    private_agent_id: str,
    *,
    area: str = "hub",
) -> SessionEffects:
    return SessionEffects(
        replace_entities=(
            _agent_binding_effect(
                agent_ref,
                private_agent_id,
                (
                    ATTACH_SOURCE.id,
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
                ),
            ),
        ),
        surface_updates=(
            PublicSurfaceEffect(
                surface_id="agents.home",
                values=(
                    PublicValue(name="selected_agent_ref", value=FrozenJson(agent_ref)),
                    PublicValue(name="selected_agent_area", value=FrozenJson(area)),
                ),
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
                    "designer.customize",
                    "designer.approve",
                    "designer.request_build",
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
) -> EntityKindEffects:
    return EntityKindEffects(
        entity_kind="agent",
        bindings=(
            EntityBindingEffect(
                public=PublicEntityHandle(entity_kind="agent", handle=agent_ref),
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
    "CreateAgentHandler",
    "OpenAttachedSourceHandler",
    "OpenAgentAreaHandler",
    "OpenBuildSourceRevisionHandler",
    "OpenSourceCreationHandler",
    "ReturnFromSourceHandler",
    "SaveAgentChangesHandler",
    "SelectAgentHandler",
]
