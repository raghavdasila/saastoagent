from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from corpus.shared.private_forms import EncryptedPrivateFormReader, PrivateFormError


class LoungePrivateForm(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegisterPrivateForm(LoungePrivateForm):
    email: EmailStr
    password: str = Field(min_length=1)
    display_name: str | None = Field(default=None, max_length=128)


class SignInPrivateForm(LoungePrivateForm):
    email: EmailStr
    password: str = Field(min_length=1)


class PasswordResetRequestPrivateForm(LoungePrivateForm):
    email: EmailStr


class PasswordResetConfirmPrivateForm(LoungePrivateForm):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=1)


class VerifyEmailPrivateForm(LoungePrivateForm):
    token: str = Field(min_length=1)


EncryptedLoungePrivateFormReader = EncryptedPrivateFormReader
LoungePrivateFormError = PrivateFormError


__all__ = [
    "EncryptedLoungePrivateFormReader",
    "LoungePrivateFormError",
    "PasswordResetConfirmPrivateForm",
    "PasswordResetRequestPrivateForm",
    "RegisterPrivateForm",
    "SignInPrivateForm",
    "VerifyEmailPrivateForm",
]
