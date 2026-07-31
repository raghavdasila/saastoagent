from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from urllib.parse import quote

from routedeck_core.contracts.effects import SessionEffects
from routedeck_core.contracts.failures import (
    FailureKind,
    FailureSafeDetails,
    RouteDeckFailure,
)
from routedeck_core.contracts.operations import (
    DeliveryPhase,
    OperationOutcome,
    OperationSource,
)
from routedeck_core.ports.executor import ExecutionContext

from corpus.auth.config import AuthSettings
from corpus.auth.credential_transition import CredentialTransition
from corpus.auth.mail import MailDeliveryUnavailable, OwnerMailDelivery
from corpus.auth.rate_limits import AuthRateLimiter, RateLimitExceeded
from corpus.auth.service import (
    AuthConflict,
    AuthService,
    ConversationUnavailable,
    InvalidAuthToken,
    InvalidCredentials,
    SessionUnavailable,
)

from .declarations import (
    AUTHENTICATE_OWNER,
    CHANGE_OWNER_PASSWORD,
    CONFIRM_OWNER_EMAIL,
    CREATE_OWNER_ACCOUNT,
    REGISTER_FORM_ID,
    REQUEST_PASSWORD_RESET,
    REQUEST_VERIFICATION_DELIVERY,
    RESET_CONFIRM_FORM_ID,
    RESET_REQUEST_FORM_ID,
    SIGN_IN_FORM_ID,
    VERIFY_EMAIL_FORM_ID,
)
from .private_forms import (
    EncryptedLoungePrivateFormReader,
    LoungePrivateFormError,
    PasswordResetConfirmPrivateForm,
    PasswordResetRequestPrivateForm,
    RegisterPrivateForm,
    SignInPrivateForm,
    VerifyEmailPrivateForm,
)


logger = logging.getLogger(__name__)


def _require_surface(
    arguments: Mapping[str, Any],
    context: ExecutionContext,
    operation_id: str,
    credential_transition: CredentialTransition,
) -> OperationOutcome | None:
    if arguments:
        return _failure(
            context,
            operation_id,
            code="invalid_arguments",
            message="This operation does not accept public arguments.",
            kind=FailureKind.CONTRACT,
            phase="argument_validation",
        )
    if context.source is not OperationSource.SURFACE:
        return _failure(
            context,
            operation_id,
            code="private_surface_required",
            message="Complete this action through its private product surface.",
            kind=FailureKind.CONTRACT,
            phase="source_validation",
        )
    if credential_transition.current_request() is None:
        return _failure(
            context,
            operation_id,
            code="http_request_context_required",
            message="The account action is unavailable outside the browser request.",
            kind=FailureKind.TRANSPORT,
            phase="request_context",
        )
    return None


@dataclass(frozen=True)
class CreateOwnerAccountHandler:
    service: AuthService
    limiter: AuthRateLimiter
    private_forms: EncryptedLoungePrivateFormReader
    credential_transition: CredentialTransition

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        denied = _require_surface(
            arguments, context, CREATE_OWNER_ACCOUNT.id, self.credential_transition
        )
        if denied is not None:
            return denied
        request = self.credential_transition.current_request()
        assert request is not None
        if (
            request.current_access_token is None
            or request.selected_conversation_id is None
        ):
            return _failure(
                context,
                CREATE_OWNER_ACCOUNT.id,
                code="authentication_required",
                message="Anonymous bearer credentials and a selected conversation are required.",
                kind=FailureKind.TRANSPORT,
                phase="request_context",
                http_status=401,
            )
        limited = await _limit(
            self.limiter,
            context,
            CREATE_OWNER_ACCOUNT.id,
            scope="registration-ip",
            subject=request.client_ip,
            limit=5,
            window=timedelta(hours=1),
        )
        if limited is not None:
            return limited
        try:
            form = await self.private_forms.load(
                context.session_id,
                REGISTER_FORM_ID,
                RegisterPrivateForm,
            )
            issued = await self.service.register(
                email=str(form.email),
                password=form.password,
                display_name=form.display_name,
                anonymous_access_token=request.current_access_token,
                conversation_id=request.selected_conversation_id,
                route_session_id=context.session_id,
            )
        except LoungePrivateFormError as error:
            return _private_form_failure(context, CREATE_OWNER_ACCOUNT.id, error)
        except AuthConflict:
            return _failure(
                context,
                CREATE_OWNER_ACCOUNT.id,
                code="email_already_registered",
                message="An owner with that email already exists.",
                kind=FailureKind.BUSINESS,
                phase="account_creation",
                delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
                http_status=409,
            )
        except (ConversationUnavailable, SessionUnavailable):
            return _failure(
                context,
                CREATE_OWNER_ACCOUNT.id,
                code="conversation_unavailable",
                message="The selected anonymous conversation is unavailable.",
                kind=FailureKind.STATE_CONFLICT,
                phase="account_creation",
                delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
                http_status=409,
            )
        except ValueError as error:
            return _failure(
                context,
                CREATE_OWNER_ACCOUNT.id,
                code="invalid_password",
                message=str(error),
                kind=FailureKind.BUSINESS,
                phase="account_creation",
                delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
                http_status=400,
            )
        self.credential_transition.publish_issued_tokens(issued.tokens)
        return _success("created", REGISTER_FORM_ID)


@dataclass(frozen=True)
class AuthenticateOwnerHandler:
    service: AuthService
    limiter: AuthRateLimiter
    private_forms: EncryptedLoungePrivateFormReader
    credential_transition: CredentialTransition

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        denied = _require_surface(
            arguments, context, AUTHENTICATE_OWNER.id, self.credential_transition
        )
        if denied is not None:
            return denied
        request = self.credential_transition.current_request()
        assert request is not None
        if (
            request.current_access_token is None
            or request.selected_conversation_id is None
        ):
            return _failure(
                context,
                AUTHENTICATE_OWNER.id,
                code="authentication_required",
                message="Anonymous bearer credentials and a selected conversation are required.",
                kind=FailureKind.TRANSPORT,
                phase="request_context",
                http_status=401,
            )
        try:
            form = await self.private_forms.load(
                context.session_id,
                SIGN_IN_FORM_ID,
                SignInPrivateForm,
            )
        except LoungePrivateFormError as error:
            return _private_form_failure(context, AUTHENTICATE_OWNER.id, error)
        for scope, subject, limit in (
            ("sign-in-ip", request.client_ip, 20),
            ("sign-in-email", str(form.email).lower(), 5),
        ):
            limited = await _limit(
                self.limiter,
                context,
                AUTHENTICATE_OWNER.id,
                scope=scope,
                subject=subject,
                limit=limit,
                window=timedelta(minutes=15),
            )
            if limited is not None:
                return limited
        try:
            issued = await self.service.sign_in(
                email=str(form.email),
                password=form.password,
                anonymous_access_token=request.current_access_token,
                conversation_id=request.selected_conversation_id,
                route_session_id=context.session_id,
            )
        except InvalidCredentials:
            return _failure(
                context,
                AUTHENTICATE_OWNER.id,
                code="invalid_credentials",
                message="Invalid email or password.",
                kind=FailureKind.BUSINESS,
                phase="authentication",
                delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
                http_status=401,
            )
        except (ConversationUnavailable, SessionUnavailable):
            return _failure(
                context,
                AUTHENTICATE_OWNER.id,
                code="conversation_unavailable",
                message="The selected anonymous conversation is unavailable.",
                kind=FailureKind.STATE_CONFLICT,
                phase="authentication",
                delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
                http_status=409,
            )
        self.credential_transition.publish_issued_tokens(issued.tokens)
        return _success("authenticated", SIGN_IN_FORM_ID)


@dataclass(frozen=True)
class RequestPasswordResetHandler:
    service: AuthService
    limiter: AuthRateLimiter
    mail: OwnerMailDelivery
    settings: AuthSettings
    private_forms: EncryptedLoungePrivateFormReader
    credential_transition: CredentialTransition

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        denied = _require_surface(
            arguments,
            context,
            REQUEST_PASSWORD_RESET.id,
            self.credential_transition,
        )
        if denied is not None:
            return denied
        request = self.credential_transition.current_request()
        assert request is not None
        try:
            form = await self.private_forms.load(
                context.session_id,
                RESET_REQUEST_FORM_ID,
                PasswordResetRequestPrivateForm,
            )
        except LoungePrivateFormError as error:
            return _private_form_failure(context, REQUEST_PASSWORD_RESET.id, error)
        email = str(form.email).lower()
        for scope, subject, limit in (
            ("password-reset-email", email, 3),
            ("password-reset-ip", request.client_ip, 20),
        ):
            limited = await _limit(
                self.limiter,
                context,
                REQUEST_PASSWORD_RESET.id,
                scope=scope,
                subject=subject,
                limit=limit,
                window=timedelta(hours=1),
            )
            if limited is not None:
                return limited
        token = await self.service.request_password_reset(email)
        if token is not None:
            link = (
                f"{str(self.settings.public_frontend_url).rstrip('/')}"
                f"/reset-password#token={quote(token.token)}"
            )
            try:
                await self.mail.send_password_reset(token.recipient, link)
            except MailDeliveryUnavailable:
                logger.exception("Password reset email delivery failed")
        return _success("requested", RESET_REQUEST_FORM_ID)


@dataclass(frozen=True)
class ChangeOwnerPasswordHandler:
    service: AuthService
    private_forms: EncryptedLoungePrivateFormReader
    credential_transition: CredentialTransition

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        denied = _require_surface(
            arguments, context, CHANGE_OWNER_PASSWORD.id, self.credential_transition
        )
        if denied is not None:
            return denied
        try:
            form = await self.private_forms.load(
                context.session_id,
                RESET_CONFIRM_FORM_ID,
                PasswordResetConfirmPrivateForm,
            )
            await self.service.confirm_password_reset(form.token, form.new_password)
        except LoungePrivateFormError as error:
            return _private_form_failure(context, CHANGE_OWNER_PASSWORD.id, error)
        except InvalidAuthToken:
            return _failure(
                context,
                CHANGE_OWNER_PASSWORD.id,
                code="invalid_reset_token",
                message="The reset token is invalid or expired.",
                kind=FailureKind.BUSINESS,
                phase="password_reset",
                delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
                http_status=400,
            )
        except ValueError as error:
            return _failure(
                context,
                CHANGE_OWNER_PASSWORD.id,
                code="invalid_password",
                message=str(error),
                kind=FailureKind.BUSINESS,
                phase="password_reset",
                delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
                http_status=400,
            )
        self.credential_transition.publish_revocation()
        return _success("changed", RESET_CONFIRM_FORM_ID)


@dataclass(frozen=True)
class RequestVerificationDeliveryHandler:
    service: AuthService
    limiter: AuthRateLimiter
    mail: OwnerMailDelivery
    settings: AuthSettings
    credential_transition: CredentialTransition

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        if arguments:
            return _failure(
                context,
                REQUEST_VERIFICATION_DELIVERY.id,
                code="invalid_arguments",
                message="This operation does not accept public arguments.",
                kind=FailureKind.CONTRACT,
                phase="argument_validation",
            )
        request = self.credential_transition.current_request()
        if request is None:
            return _failure(
                context,
                REQUEST_VERIFICATION_DELIVERY.id,
                code="http_request_context_required",
                message="Verification delivery is unavailable outside the browser request.",
                kind=FailureKind.TRANSPORT,
                phase="request_context",
            )
        try:
            token = await self.service.request_verification_for_route(
                context.session_id
            )
        except SessionUnavailable:
            return _failure(
                context,
                REQUEST_VERIFICATION_DELIVERY.id,
                code="authentication_required",
                message="Authentication is required.",
                kind=FailureKind.STATE_CONFLICT,
                phase="owner_context",
                delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
                http_status=401,
            )
        if token is None:
            return _success("requested")
        for scope, subject, limit in (
            ("verification-email", token.recipient, 3),
            ("verification-ip", request.client_ip, 20),
        ):
            limited = await _limit(
                self.limiter,
                context,
                REQUEST_VERIFICATION_DELIVERY.id,
                scope=scope,
                subject=subject,
                limit=limit,
                window=timedelta(hours=1),
            )
            if limited is not None:
                return limited
        link = (
            f"{str(self.settings.public_frontend_url).rstrip('/')}"
            f"/verify#token={quote(token.token)}"
        )
        try:
            await self.mail.send_verification(token.recipient, link)
        except MailDeliveryUnavailable:
            return _failure(
                context,
                REQUEST_VERIFICATION_DELIVERY.id,
                code="verification_delivery_unavailable",
                message="Verification email delivery is unavailable.",
                kind=FailureKind.TRANSPORT,
                phase="verification_delivery",
                delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
                http_status=503,
            )
        return _success("requested")


@dataclass(frozen=True)
class ConfirmOwnerEmailHandler:
    service: AuthService
    private_forms: EncryptedLoungePrivateFormReader
    credential_transition: CredentialTransition

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        denied = _require_surface(
            arguments, context, CONFIRM_OWNER_EMAIL.id, self.credential_transition
        )
        if denied is not None:
            return denied
        try:
            form = await self.private_forms.load(
                context.session_id,
                VERIFY_EMAIL_FORM_ID,
                VerifyEmailPrivateForm,
            )
            await self.service.verify(form.token)
        except LoungePrivateFormError as error:
            return _private_form_failure(context, CONFIRM_OWNER_EMAIL.id, error)
        except InvalidAuthToken:
            return _failure(
                context,
                CONFIRM_OWNER_EMAIL.id,
                code="invalid_verification_token",
                message="The verification token is invalid or expired.",
                kind=FailureKind.BUSINESS,
                phase="email_verification",
                delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
                http_status=400,
            )
        return _success("confirmed", VERIFY_EMAIL_FORM_ID)


@dataclass(frozen=True)
class LoungeNavigationHandler:
    operation_id: str
    private_forms: EncryptedLoungePrivateFormReader | None = None
    remove_form_id: str | None = None

    async def __call__(
        self,
        arguments: Mapping[str, Any],
        context: ExecutionContext,
    ) -> OperationOutcome:
        if arguments:
            return _failure(
                context,
                self.operation_id,
                code="invalid_arguments",
                message="This operation does not accept public arguments.",
                kind=FailureKind.CONTRACT,
                phase="argument_validation",
            )
        remove = ()
        if self.remove_form_id is not None:
            if self.private_forms is None:
                raise RuntimeError("Private-form cleanup requires a reader")
            if await self.private_forms.has_draft(
                context.session_id, self.remove_form_id
            ):
                remove = (self.remove_form_id,)
        return OperationOutcome(
            outcome="opened",
            delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
            effects=SessionEffects(remove_private_form_ids=remove),
        )


async def _limit(
    limiter,
    context,
    operation_id,
    **values,
) -> OperationOutcome | None:
    try:
        await limiter.consume(**values)
    except RateLimitExceeded:
        return _failure(
            context,
            operation_id,
            code="rate_limit_exceeded",
            message="Too many authentication attempts. Try again later.",
            kind=FailureKind.BUSINESS,
            phase="rate_limit",
            http_status=429,
        )
    return None


def _success(outcome: str, remove_form_id: str | None = None) -> OperationOutcome:
    return OperationOutcome(
        outcome=outcome,
        delivery_phase=DeliveryPhase.RESPONSE_RECEIVED,
        effects=SessionEffects(
            remove_private_form_ids=(remove_form_id,) if remove_form_id else ()
        ),
    )


def _private_form_failure(context, operation_id, error):
    return _failure(
        context,
        operation_id,
        code=error.code,
        message=error.public_message,
        kind=FailureKind.CONTRACT,
        phase="private_form_validation",
    )


def _failure(
    context,
    operation_id,
    *,
    code,
    message,
    kind,
    phase,
    delivery_phase=DeliveryPhase.NOT_SENT,
    http_status=None,
):
    return OperationOutcome(
        delivery_phase=delivery_phase,
        failure=RouteDeckFailure(
            kind=kind,
            code=code,
            phase=phase,
            correlation_id=context.attempt_id,
            operation_id=operation_id,
            request_id=context.request_id,
            public_message=message,
            safe_details=FailureSafeDetails(
                http_status=http_status,
                delivery_phase=delivery_phase.value,
            ),
        ),
    )


__all__ = [
    "AuthenticateOwnerHandler",
    "ChangeOwnerPasswordHandler",
    "ConfirmOwnerEmailHandler",
    "CreateOwnerAccountHandler",
    "LoungeNavigationHandler",
    "RequestPasswordResetHandler",
    "RequestVerificationDeliveryHandler",
]
