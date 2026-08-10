from __future__ import annotations

import asyncio

from corpus.integrations.agent_delivery import NeutralAgentDeliveryAdapter

from .ports import ChannelUnavailable


class ChannelService:
    def __init__(self, repository, delivery: NeutralAgentDeliveryAdapter, agents) -> None:
        self.repository = repository
        self.delivery = delivery
        self.agents = agents

    async def create(self, organization_id, agent_id, *, name: str, slug: str):
        await self.agents.get(organization_id, agent_id)
        clean_name = name.strip()
        clean_slug = slug.strip().lower()
        if not clean_name:
            raise ChannelUnavailable("A channel name is required.")
        record = await self.repository.reserve(
            organization_id, agent_id, name=clean_name, slug=clean_slug
        )
        try:
            runtime = await asyncio.to_thread(self.delivery.create_channel, clean_name, clean_slug)
            return await self.repository.complete(
                organization_id, record.id, runtime_channel_id=runtime.channel_id
            )
        except Exception as error:
            await self.repository.fail(
                organization_id, record.id,
                code=type(error).__name__, message="The hosted Web channel could not be created.",
            )
            raise ChannelUnavailable("The hosted Web channel could not be created.") from error

    async def list(self, organization_id, agent_id):
        await self.agents.get(organization_id, agent_id)
        return await self.repository.list(organization_id, agent_id)

    async def set_enabled(self, organization_id, agent_id, channel_id, *, enabled: bool):
        await self.agents.get(organization_id, agent_id)
        channel = await self.repository.get(organization_id, agent_id, channel_id)
        if channel.status != "ready" or not channel.runtime_channel_id:
            raise ChannelUnavailable("The selected channel is unavailable.")
        try:
            runtime = await asyncio.to_thread(
                self.delivery.set_channel_enabled, channel.runtime_channel_id, enabled
            )
        except Exception as error:
            raise ChannelUnavailable("The hosted Web availability could not be changed.") from error
        if runtime.channel_id != channel.runtime_channel_id or runtime.enabled is not enabled:
            raise ChannelUnavailable("The hosted Web availability could not be confirmed.")
        return await self.repository.set_enabled(
            organization_id, agent_id, channel_id, enabled=enabled
        )

    async def set_current_enabled(
        self,
        organization_id,
        agent_id,
        *,
        enabled: bool,
    ):
        ready = tuple(
            channel
            for channel in await self.list(organization_id, agent_id)
            if channel.status == "ready"
        )
        if len(ready) != 1:
            raise ChannelUnavailable(
                "Select one exact ready hosted Web channel before changing availability."
            )
        return await self.set_enabled(
            organization_id,
            agent_id,
            ready[0].id,
            enabled=enabled,
        )

    async def get_public(self, slug: str):
        return await self.repository.get_public(slug.strip().lower())


__all__ = ["ChannelService"]
