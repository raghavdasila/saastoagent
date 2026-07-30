from __future__ import annotations

from routedeck_core.app import FeatureBindings

from corpus.features.workspace.bindings import NavigationHandler

from .declarations import (
    AUTHENTICATION_COMPLETED,
    OPEN_FORGOT_PASSWORD,
    OPEN_REGISTRATION,
    OPEN_RESET_PASSWORD,
    OPEN_SIGN_IN,
    OPEN_VERIFY_EMAIL,
    RETURN_TO_LOUNGE,
    RETURN_TO_WORKSPACE,
)


def create_lounge_bindings() -> FeatureBindings:
    operations = (
        OPEN_SIGN_IN,
        OPEN_REGISTRATION,
        OPEN_FORGOT_PASSWORD,
        OPEN_RESET_PASSWORD,
        OPEN_VERIFY_EMAIL,
        RETURN_TO_LOUNGE,
        RETURN_TO_WORKSPACE,
        AUTHENTICATION_COMPLETED,
    )
    return FeatureBindings(
        handlers={
            operation.ref: NavigationHandler(operation.id) for operation in operations
        },
        providers={},
        guards={},
    )


__all__ = ["create_lounge_bindings"]
