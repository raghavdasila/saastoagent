from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, ValidationError
from routedeck_core.ports import RouteDeckSessionStore


class PrivateFormCodec(Protocol):
    def decrypt(self, value: bytes) -> bytes: ...


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


class LoungePrivateFormError(RuntimeError):
    def __init__(self, code: str, public_message: str) -> None:
        super().__init__(code)
        self.code = code
        self.public_message = public_message


FormT = TypeVar("FormT", bound=LoungePrivateForm)


@dataclass(frozen=True)
class EncryptedLoungePrivateFormReader:
    store: RouteDeckSessionStore
    codec: PrivateFormCodec

    async def load(
        self,
        session_id: str,
        form_id: str,
        model: type[FormT],
    ) -> FormT:
        try:
            snapshot = await self.store.load(session_id)
        except Exception:
            raise LoungePrivateFormError(
                "private_form_unavailable",
                "The private form could not be loaded.",
            ) from None
        drafts = tuple(
            draft
            for draft in snapshot.state.private_state.drafts
            if draft.form_id == form_id
        )
        if len(drafts) != 1:
            raise LoungePrivateFormError(
                "private_form_required",
                "Complete the private form before continuing.",
            )
        draft = drafts[0]
        if not draft.complete:
            raise LoungePrivateFormError(
                "private_form_incomplete",
                "Complete every required field before continuing.",
            )
        try:
            encrypted = await self.store.load_private_blob(session_id, form_id)
        except Exception:
            raise LoungePrivateFormError(
                "private_form_unavailable",
                "The private form could not be loaded.",
            ) from None
        if encrypted is None:
            raise LoungePrivateFormError(
                "private_form_state_mismatch",
                "The private form could not be loaded.",
            )
        try:
            value = json.loads(self.codec.decrypt(encrypted))
        except Exception:
            raise LoungePrivateFormError(
                "private_form_unavailable",
                "The private form could not be loaded.",
            ) from None
        if not isinstance(value, dict) or tuple(sorted(value)) != draft.field_names:
            raise LoungePrivateFormError(
                "private_form_state_mismatch",
                "The private form could not be loaded.",
            )
        try:
            return model.model_validate(value)
        except ValidationError:
            raise LoungePrivateFormError(
                "private_form_invalid",
                "Review the private form fields before continuing.",
            ) from None

    async def has_draft(self, session_id: str, form_id: str) -> bool:
        snapshot = await self.store.load(session_id)
        return any(
            draft.form_id == form_id
            for draft in snapshot.state.private_state.drafts
        )


__all__ = [
    "EncryptedLoungePrivateFormReader",
    "LoungePrivateFormError",
    "PasswordResetConfirmPrivateForm",
    "PasswordResetRequestPrivateForm",
    "RegisterPrivateForm",
    "SignInPrivateForm",
    "VerifyEmailPrivateForm",
]
