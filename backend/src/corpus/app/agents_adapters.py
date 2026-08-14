from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass

from corpus.auth.contracts import AgentOwnerScopeGateway, AgentOwnerScopeUnavailable
from corpus.auth.service import AuthService, SessionUnavailable
from corpus.features.agents.ports import (
    AgentSourceAttachmentUnavailable,
    AgentSourceGateway,
    AttachableSource,
)
from corpus.features.sources.models import SourceState
from corpus.features.sources.repository import SourceNotFound
from corpus.features.sources.service import SourceService


@dataclass(frozen=True)
class AuthAgentOwnerScopeGateway(AgentOwnerScopeGateway):
    auth: AuthService

    async def organization_id_for_route(
        self,
        route_session_id: str,
    ) -> uuid.UUID:
        try:
            return await self.auth.organization_id_for_route(route_session_id)
        except SessionUnavailable as error:
            raise AgentOwnerScopeUnavailable(
                "The authenticated owner Workspace is unavailable."
            ) from error

    async def organization_id_for_access_token(
        self,
        access_token: str,
    ) -> uuid.UUID:
        try:
            principal = await self.auth.resolve_access_token(access_token)
        except SessionUnavailable as error:
            raise AgentOwnerScopeUnavailable(
                "Authentication is required."
            ) from error
        if principal.organization_id is None:
            raise AgentOwnerScopeUnavailable("Authentication is required.")
        return principal.organization_id


@dataclass(frozen=True)
class CorpusAgentSourceGateway(AgentSourceGateway):
    """Read the one owner-scoped Source inventory without copying its state."""

    sources: SourceService

    async def ready_inventory(
        self,
        organization_id: uuid.UUID,
    ) -> tuple[AttachableSource, ...]:
        values = await asyncio.to_thread(
            self.sources.list_sources,
            owner_key=str(organization_id),
        )
        return tuple(
            AttachableSource(
                source_id=source.source_id,
                source_revision_id=source.revision.revision_id,
                display_name=source.display_name,
            )
            for source in values
            if source.revision.state is SourceState.READY
        )

    async def ready_current(
        self,
        organization_id: uuid.UUID,
        source_id: str,
    ) -> AttachableSource:
        source = await self._get(organization_id, source_id)
        if source.revision.state is not SourceState.READY:
            raise AgentSourceAttachmentUnavailable(
                "Only a ready Source revision can be attached to an Agent."
            )
        return AttachableSource(
            source_id=source.source_id,
            source_revision_id=source.revision.revision_id,
            display_name=source.display_name,
        )

    async def exact_revision(
        self,
        organization_id: uuid.UUID,
        source_id: str,
        source_revision_id: str,
    ) -> AttachableSource:
        try:
            source = await asyncio.to_thread(
                self.sources.repository.get_revision,
                owner_key=str(organization_id),
                source_id=source_id,
                revision_id=source_revision_id,
            )
        except SourceNotFound as error:
            raise AgentSourceAttachmentUnavailable(
                "The attached Source revision is unavailable. The attachment was not changed."
            ) from error
        if source.revision.state is not SourceState.READY:
            raise AgentSourceAttachmentUnavailable(
                "The attached Source revision is not ready to open."
            )
        return AttachableSource(
            source_id=source.source_id,
            source_revision_id=source.revision.revision_id,
            display_name=source.display_name,
        )

    async def _get(self, organization_id: uuid.UUID, source_id: str):
        try:
            return await asyncio.to_thread(
                self.sources.get_source,
                owner_key=str(organization_id),
                source_id=source_id,
            )
        except SourceNotFound as error:
            raise AgentSourceAttachmentUnavailable(
                "The selected Source is unavailable in this Workspace."
            ) from error

__all__ = ["AuthAgentOwnerScopeGateway", "CorpusAgentSourceGateway"]
