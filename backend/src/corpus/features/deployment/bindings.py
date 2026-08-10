from routedeck_core.app import FeatureBindings

from .declarations import DEPLOY_AGENT, ROLLBACK_DEPLOYMENT
from .operations import DeployHandler, RollbackHandler


def create_deployment_bindings(service, owner_scope):
    return FeatureBindings(handlers={
        DEPLOY_AGENT.ref: DeployHandler(service, owner_scope),
        ROLLBACK_DEPLOYMENT.ref: RollbackHandler(service, owner_scope),
    }, providers={}, guards={})


__all__ = ["create_deployment_bindings"]
