from routedeck_core.app import FeatureBindings

from .declarations import CREATE_CHANNEL, SET_CHANNEL_ENABLED
from .operations import CreateChannelHandler, SetChannelEnabledHandler


def create_channel_bindings(service, owner_scope):
    return FeatureBindings(handlers={
        CREATE_CHANNEL.ref: CreateChannelHandler(service, owner_scope),
        SET_CHANNEL_ENABLED.ref: SetChannelEnabledHandler(service, owner_scope),
    }, providers={}, guards={})


__all__ = ["create_channel_bindings"]
