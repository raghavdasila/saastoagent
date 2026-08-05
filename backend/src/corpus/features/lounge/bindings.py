from __future__ import annotations

from routedeck_core.app import FeatureBindings

from corpus.auth.config import AuthSettings
from corpus.auth.credential_transition import CredentialTransition
from corpus.auth.mail import OwnerMailDelivery
from corpus.auth.rate_limits import AuthRateLimiter
from corpus.auth.service import AuthService

from .declarations import (
    ARRIVAL_OPEN_REGISTRATION,
    ARRIVAL_OPEN_SIGN_IN,
    AUTHENTICATE_OWNER,
    CHANGE_OWNER_PASSWORD,
    CHANGE_PASSWORD_RETURN_TO_LOUNGE,
    CONFIRM_EMAIL_RETURN_TO_LOUNGE,
    CONFIRM_OWNER_EMAIL,
    CREATE_OWNER_ACCOUNT,
    HELP_OPEN_REGISTRATION,
    HELP_OPEN_SIGN_IN,
    HELP_RETURN_TO_LOUNGE,
    OPEN_PRODUCT_HELP,
    REGISTER_FORM_ID,
    REGISTRATION_CONTINUE_TO_WORKSPACE,
    REGISTRATION_RETURN_TO_LOUNGE,
    REQUEST_PASSWORD_RESET,
    REQUEST_RESET_RETURN_TO_LOUNGE,
    REQUEST_VERIFICATION_DELIVERY,
    RESET_CONFIRM_FORM_ID,
    RESET_REQUEST_FORM_ID,
    SIGN_IN_CONTINUE_TO_WORKSPACE,
    SIGN_IN_FORM_ID,
    SIGN_IN_OPEN_PASSWORD_RECOVERY,
    SIGN_IN_RETURN_TO_LOUNGE,
    VERIFICATION_RETURN_TO_WORKSPACE,
    VERIFY_EMAIL_FORM_ID,
)
from .operations import (
    AuthenticateOwnerHandler,
    ChangeOwnerPasswordHandler,
    ConfirmOwnerEmailHandler,
    CreateOwnerAccountHandler,
    LoungeNavigationHandler,
    RequestPasswordResetHandler,
    RequestVerificationDeliveryHandler,
)
from .private_forms import EncryptedLoungePrivateFormReader


def create_lounge_bindings(
    *,
    service: AuthService,
    limiter: AuthRateLimiter,
    mail: OwnerMailDelivery,
    settings: AuthSettings,
    private_forms: EncryptedLoungePrivateFormReader,
    credential_transition: CredentialTransition,
) -> FeatureBindings:
    navigation = (
        OPEN_PRODUCT_HELP,
        ARRIVAL_OPEN_REGISTRATION,
        ARRIVAL_OPEN_SIGN_IN,
        HELP_RETURN_TO_LOUNGE,
        HELP_OPEN_REGISTRATION,
        HELP_OPEN_SIGN_IN,
        REGISTRATION_CONTINUE_TO_WORKSPACE,
        SIGN_IN_CONTINUE_TO_WORKSPACE,
        SIGN_IN_OPEN_PASSWORD_RECOVERY,
        VERIFICATION_RETURN_TO_WORKSPACE,
    )
    handlers = {
        operation.ref: LoungeNavigationHandler(operation.id)
        for operation in navigation
    }
    handlers.update(
        {
            REGISTRATION_RETURN_TO_LOUNGE.ref: LoungeNavigationHandler(
                REGISTRATION_RETURN_TO_LOUNGE.id,
                private_forms,
                REGISTER_FORM_ID,
            ),
            SIGN_IN_RETURN_TO_LOUNGE.ref: LoungeNavigationHandler(
                SIGN_IN_RETURN_TO_LOUNGE.id,
                private_forms,
                SIGN_IN_FORM_ID,
            ),
            REQUEST_RESET_RETURN_TO_LOUNGE.ref: LoungeNavigationHandler(
                REQUEST_RESET_RETURN_TO_LOUNGE.id,
                private_forms,
                RESET_REQUEST_FORM_ID,
            ),
            CHANGE_PASSWORD_RETURN_TO_LOUNGE.ref: LoungeNavigationHandler(
                CHANGE_PASSWORD_RETURN_TO_LOUNGE.id,
                private_forms,
                RESET_CONFIRM_FORM_ID,
            ),
            CONFIRM_EMAIL_RETURN_TO_LOUNGE.ref: LoungeNavigationHandler(
                CONFIRM_EMAIL_RETURN_TO_LOUNGE.id,
                private_forms,
                VERIFY_EMAIL_FORM_ID,
            ),
            CREATE_OWNER_ACCOUNT.ref: CreateOwnerAccountHandler(
                service, limiter, private_forms, credential_transition
            ),
            AUTHENTICATE_OWNER.ref: AuthenticateOwnerHandler(
                service, limiter, private_forms, credential_transition
            ),
            REQUEST_PASSWORD_RESET.ref: RequestPasswordResetHandler(
                service, limiter, mail, settings, private_forms, credential_transition
            ),
            CHANGE_OWNER_PASSWORD.ref: ChangeOwnerPasswordHandler(
                service, private_forms, credential_transition
            ),
            REQUEST_VERIFICATION_DELIVERY.ref: RequestVerificationDeliveryHandler(
                service, limiter, mail, settings, credential_transition
            ),
            CONFIRM_OWNER_EMAIL.ref: ConfirmOwnerEmailHandler(
                service, private_forms, credential_transition
            ),
        }
    )
    return FeatureBindings(handlers=handlers, providers={}, guards={})


__all__ = ["create_lounge_bindings"]
