class DeploymentUnavailable(RuntimeError):
    pass


class DeploymentConflict(RuntimeError):
    pass


__all__ = ["DeploymentConflict", "DeploymentUnavailable"]
