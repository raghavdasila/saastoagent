from __future__ import annotations

from typing import Protocol

from corpus.shared.agent_delivery import ChannelProjection


class ChannelUnavailable(RuntimeError):
    pass


class ChannelConflict(RuntimeError):
    pass


class ChannelDeliveryPort(Protocol):
    def create_channel(self, name: str, slug: str) -> ChannelProjection: ...

    def set_channel_enabled(
        self, channel_id: str, enabled: bool
    ) -> ChannelProjection: ...


__all__ = ["ChannelConflict", "ChannelDeliveryPort", "ChannelUnavailable"]
