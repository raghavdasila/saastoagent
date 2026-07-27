from __future__ import annotations

import uuid

from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.exceptions import InvalidPasswordException

from .models import User
from .security import PasswordPolicyError, normalize_email, validate_password


class CorpusUserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret: str
    verification_token_secret: str
    reset_password_token_lifetime_seconds = 3600
    verification_token_lifetime_seconds = 86400

    def __init__(self, user_db) -> None:
        super().__init__(user_db)
        self.generated_verification_token: str | None = None
        self.generated_reset_token: str | None = None

    async def validate_password(self, password: str, user) -> None:
        try:
            validate_password(password, normalize_email(str(user.email)))
        except (PasswordPolicyError, ValueError) as error:
            raise InvalidPasswordException(reason=str(error)) from error

    async def on_after_request_verify(self, user, token: str, request=None) -> None:
        self.generated_verification_token = token

    async def on_after_forgot_password(self, user, token: str, request=None) -> None:
        self.generated_reset_token = token


__all__ = ["CorpusUserManager"]
