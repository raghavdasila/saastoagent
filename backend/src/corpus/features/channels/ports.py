class ChannelUnavailable(RuntimeError):
    pass


class ChannelConflict(RuntimeError):
    pass


__all__ = ["ChannelConflict", "ChannelUnavailable"]
