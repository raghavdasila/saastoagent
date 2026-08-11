from routedeck_core.app import FeatureBindings

from .declarations import DEPLOY_AGENT, RETRY_DEPLOYMENT, ROLLBACK_DEPLOYMENT
from .operations import DeployHandler, RetryDeploymentHandler, RollbackHandler


def create_deployment_bindings(service, owner_scope):
    return FeatureBindings(handlers={
        DEPLOY_AGENT.ref: DeployHandler(service, owner_scope),
        RETRY_DEPLOYMENT.ref: RetryDeploymentHandler(service, owner_scope),
        ROLLBACK_DEPLOYMENT.ref: RollbackHandler(service, owner_scope),
    }, providers={}, guards={})


__all__ = ["create_deployment_bindings"]
