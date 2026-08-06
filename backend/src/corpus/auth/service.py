from __future__ import annotations

import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.exceptions import InvalidPasswordException, UserAlreadyExists
from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError

from corpus.persistence import CorpusDatabase

from .contracts import OwnerRouteContext
from .database import TransactionalUserDatabase
from .manager import CorpusUserManager
from .models import (
    AccessToken,
    AuthSession,
    CorpusConversation,
    Membership,
    MembershipRole,
    Organization,
    User,
)
from .schemas import (
    AnonymousPrincipalView,
    MembershipView,
    OrganizationView,
    OwnerPrincipalView,
    OwnerSessionView,
    OwnerUserCreate,
    OwnerView,
    TokenPairView,
)
from .security import hash_opaque_token, issue_opaque_token, normalize_email, validate_password


class AuthServiceError(RuntimeError):
    pass


class AuthConflict(AuthServiceError):
    pass


class InvalidCredentials(AuthServiceError):
    pass


class ConversationUnavailable(AuthServiceError):
    pass


class ConversationLimitReached(AuthServiceError):
    pass


class SessionUnavailable(AuthServiceError):
    pass


class InvalidAuthToken(AuthServiceError):
    pass


@dataclass(frozen=True)
class CurrentPrincipal:
    kind: Literal["anonymous", "owner"]
    auth_session_id: uuid.UUID
    user_id: uuid.UUID | None
    organization_id: uuid.UUID | None
    access_expires_at: datetime
    owner: OwnerPrincipalView | None


@dataclass(frozen=True)
class IssuedOwnerSession:
    view: OwnerSessionView
    tokens: TokenPairView
    conversation_id: str
    route_session_id: str


@dataclass(frozen=True)
class EmailToken:
    recipient: str
    token: str


@dataclass(frozen=True)
class VerificationDeliveryContext:
    recipient: str
    already_verified: bool


class AuthService:
    def __init__(
        self,
        database: CorpusDatabase,
        *,
        reset_secret: str = "test-reset-secret-at-least-32-bytes-long",
        verification_secret: str = "test-verification-secret-at-least-32-bytes-long",
        access_lifetime: timedelta = timedelta(minutes=15),
        idle_lifetime: timedelta = timedelta(days=7),
        absolute_lifetime: timedelta = timedelta(days=30),
        reset_token_lifetime: timedelta = timedelta(hours=1),
        verification_token_lifetime: timedelta = timedelta(hours=24),
    ) -> None:
        self.database = database
        self.reset_secret = reset_secret
        self.verification_secret = verification_secret
        self.access_lifetime = access_lifetime
        self.idle_lifetime = idle_lifetime
        self.absolute_lifetime = absolute_lifetime
        self.reset_token_lifetime = reset_token_lifetime
        self.verification_token_lifetime = verification_token_lifetime

    def _manager(self, user_db: TransactionalUserDatabase) -> CorpusUserManager:
        manager = CorpusUserManager(user_db)
        manager.reset_password_token_secret = self.reset_secret
        manager.verification_token_secret = self.verification_secret
        manager.reset_password_token_lifetime_seconds = int(
            self.reset_token_lifetime.total_seconds()
        )
        manager.verification_token_lifetime_seconds = int(
            self.verification_token_lifetime.total_seconds()
        )
        return manager

    async def issue_anonymous(self) -> TokenPairView:
        now = datetime.now(UTC)
        async with self.database.session() as session:
            async with session.begin():
                return await self._issue_token_pair(session, user_id=None, now=now)

    async def refresh(self, refresh_token: str) -> TokenPairView:
        now = datetime.now(UTC)
        replacement = issue_opaque_token()
        async with self.database.session() as session:
            async with session.begin():
                auth_session = await session.scalar(
                    select(AuthSession).where(
                        AuthSession.refresh_token_hash
                        == hash_opaque_token(refresh_token)
                    )
                )
                if auth_session is None or not _refresh_is_active(
                    auth_session,
                    now=now,
                    idle_timeout=self.idle_lifetime,
                ):
                    if auth_session is not None and auth_session.revoked_at is None:
                        auth_session.revoked_at = now
                    raise SessionUnavailable("The refresh session is unavailable.")
                result = await session.execute(
                    update(AuthSession)
                    .where(
                        AuthSession.id == auth_session.id,
                        AuthSession.refresh_token_hash
                        == hash_opaque_token(refresh_token),
                        AuthSession.revoked_at.is_(None),
                    )
                    .values(
                        refresh_token_hash=replacement.digest,
                        last_seen_at=now,
                    )
                )
                if result.rowcount != 1:
                    raise SessionUnavailable("The refresh session is unavailable.")
                return await self._issue_access_for_session(
                    session,
                    auth_session=auth_session,
                    refresh_token=replacement.raw,
                    now=now,
                )

    async def resolve_access_token(self, access_token: str) -> CurrentPrincipal:
        now = datetime.now(UTC)
        async with self.database.session() as session:
            async with session.begin():
                return await self._resolve_access_in_session(
                    session,
                    access_token,
                    now,
                )

    async def register(
        self,
        *,
        email: str,
        password: str,
        display_name: str | None,
        anonymous_access_token: str,
        conversation_id: str,
        route_session_id: str,
    ) -> IssuedOwnerSession:
        normalized = normalize_email(email)
        validate_password(password, normalized)
        cleaned_name = _clean_display_name(display_name)
        now = datetime.now(UTC)
        try:
            async with self.database.session() as session:
                async with session.begin():
                    anonymous = await self._resolve_access_in_session(
                        session, anonymous_access_token, now
                    )
                    _require_anonymous_principal(anonymous)
                    user_db = TransactionalUserDatabase(session, User)
                    user = await self._manager(user_db).create(
                        OwnerUserCreate(
                            email=normalized,
                            password=password,
                            display_name=cleaned_name,
                        ),
                        safe=True,
                    )
                    organization = Organization(
                        name=_workspace_name(user, cleaned_name),
                        slug=await _available_slug(session, user, cleaned_name),
                        created_at=now,
                    )
                    session.add(organization)
                    await session.flush()
                    membership = Membership(
                        user_id=user.id,
                        organization_id=organization.id,
                        role=MembershipRole.OWNER,
                        created_at=now,
                    )
                    session.add(membership)
                    await session.flush()
                    conversation = await self._claim_anonymous_conversation(
                        session,
                        principal=anonymous,
                        conversation_id=conversation_id,
                        route_session_id=route_session_id,
                        owner_user_id=user.id,
                        now=now,
                    )
                    await self._revoke_auth_session(
                        session, anonymous.auth_session_id, now
                    )
                    tokens = await self._issue_token_pair(
                        session, user_id=user.id, now=now
                    )
                    return IssuedOwnerSession(
                        view=_view(user, organization, membership, "adopted"),
                        tokens=tokens,
                        conversation_id=conversation.public_id,
                        route_session_id=conversation.route_session_id,
                    )
        except (UserAlreadyExists, IntegrityError) as error:
            raise AuthConflict("An owner with that email already exists.") from error
        except InvalidPasswordException as error:
            raise ValueError(error.reason) from error

    async def sign_in(
        self,
        *,
        email: str,
        password: str,
        anonymous_access_token: str,
        conversation_id: str,
        route_session_id: str,
    ) -> IssuedOwnerSession:
        try:
            normalized = normalize_email(email)
        except ValueError as error:
            raise InvalidCredentials("Invalid email or password.") from error
        now = datetime.now(UTC)
        async with self.database.session() as session:
            async with session.begin():
                anonymous = await self._resolve_access_in_session(
                    session, anonymous_access_token, now
                )
                _require_anonymous_principal(anonymous)
                user_db = TransactionalUserDatabase(session, User)
                user = await self._manager(user_db).authenticate(
                    OAuth2PasswordRequestForm(
                        username=normalized,
                        password=password,
                    )
                )
                if user is None or not user.is_active:
                    raise InvalidCredentials("Invalid email or password.")
                membership, organization = await self._personal_membership(
                    session, user.id
                )
                conversation = await self._claim_anonymous_conversation(
                    session,
                    principal=anonymous,
                    conversation_id=conversation_id,
                    route_session_id=route_session_id,
                    owner_user_id=user.id,
                    now=now,
                )
                await self._revoke_auth_session(
                    session, anonymous.auth_session_id, now
                )
                tokens = await self._issue_token_pair(
                    session, user_id=user.id, now=now
                )
                return IssuedOwnerSession(
                    view=_view(user, organization, membership, "adopted"),
                    tokens=tokens,
                    conversation_id=conversation.public_id,
                    route_session_id=conversation.route_session_id,
                )

    async def reserve_conversation(
        self,
        *,
        access_token: str,
        route_session_id: str,
    ) -> CorpusConversation:
        now = datetime.now(UTC)
        public_id = secrets.token_urlsafe(24)
        try:
            async with self.database.session() as session:
                async with session.begin():
                    principal = await self._resolve_access_in_session(
                        session, access_token, now
                    )
                    if principal.kind == "anonymous":
                        existing = await session.scalar(
                            select(CorpusConversation.id).where(
                                CorpusConversation.anonymous_session_id
                                == principal.auth_session_id,
                                CorpusConversation.archived_at.is_(None),
                            )
                        )
                        if existing is not None:
                            raise ConversationLimitReached(
                                "Anonymous callers may have one active conversation."
                            )
                    conversation = CorpusConversation(
                        public_id=public_id,
                        anonymous_session_id=(
                            principal.auth_session_id
                            if principal.kind == "anonymous"
                            else None
                        ),
                        owner_user_id=principal.user_id,
                        route_session_id=route_session_id,
                        created_at=now,
                        updated_at=now,
                        archived_at=None,
                    )
                    session.add(conversation)
                    await session.flush()
                    return conversation
        except IntegrityError as error:
            raise ConversationLimitReached(
                "A conversation could not be reserved for this caller."
            ) from error

    async def release_conversation(self, conversation_id: str) -> None:
        async with self.database.session() as session:
            async with session.begin():
                await session.execute(
                    delete(CorpusConversation).where(
                        CorpusConversation.public_id == conversation_id
                    )
                )

    async def replace_anonymous_conversation(
        self,
        *,
        access_token: str,
        conversation_id: str,
        route_session_id: str,
    ) -> CorpusConversation:
        """Atomically archive an anonymous conversation and bind its replacement."""
        now = datetime.now(UTC)
        public_id = secrets.token_urlsafe(24)
        async with self.database.session() as session:
            async with session.begin():
                principal = await self._resolve_access_in_session(
                    session, access_token, now
                )
                if principal.kind != "anonymous":
                    raise ConversationUnavailable(
                        "Only anonymous conversations may be replaced."
                    )
                archived = await session.execute(
                    update(CorpusConversation)
                    .where(
                        CorpusConversation.public_id == conversation_id,
                        CorpusConversation.anonymous_session_id
                        == principal.auth_session_id,
                        CorpusConversation.archived_at.is_(None),
                    )
                    .values(archived_at=now, updated_at=now)
                )
                if archived.rowcount != 1:
                    raise ConversationUnavailable(
                        "The selected conversation is unavailable."
                    )
                await session.flush()
                conversation = CorpusConversation(
                    public_id=public_id,
                    anonymous_session_id=principal.auth_session_id,
                    owner_user_id=None,
                    route_session_id=route_session_id,
                    created_at=now,
                    updated_at=now,
                    archived_at=None,
                )
                session.add(conversation)
                await session.flush()
                return conversation

    async def list_conversations(
        self, access_token: str
    ) -> tuple[CorpusConversation, ...]:
        now = datetime.now(UTC)
        async with self.database.session() as session:
            async with session.begin():
                principal = await self._resolve_access_in_session(
                    session, access_token, now
                )
                rows = await session.scalars(
                    select(CorpusConversation)
                    .where(
                        *self._conversation_owner_predicate(principal),
                        CorpusConversation.archived_at.is_(None),
                    )
                    .order_by(
                        CorpusConversation.updated_at.desc(),
                        CorpusConversation.created_at.desc(),
                    )
                )
                return tuple(rows)

    async def resolve_conversation(
        self,
        *,
        access_token: str,
        conversation_id: str,
        touch: bool = False,
    ) -> CorpusConversation:
        now = datetime.now(UTC)
        async with self.database.session() as session:
            async with session.begin():
                principal = await self._resolve_access_in_session(
                    session, access_token, now
                )
                conversation = await session.scalar(
                    select(CorpusConversation).where(
                        CorpusConversation.public_id == conversation_id,
                        *self._conversation_owner_predicate(principal),
                    )
                )
                if conversation is None:
                    raise ConversationUnavailable(
                        "The selected conversation is unavailable."
                    )
                if conversation.archived_at is not None:
                    raise ConversationUnavailable(
                        "The selected conversation is archived."
                    )
                if touch:
                    conversation.updated_at = now
                return conversation

    async def owner_context_for_route(
        self,
        route_session_id: str,
    ) -> OwnerRouteContext:
        async with self.database.session() as session:
            conversation = await session.scalar(
                select(CorpusConversation).where(
                    CorpusConversation.route_session_id == route_session_id,
                    CorpusConversation.owner_user_id.is_not(None),
                    CorpusConversation.archived_at.is_(None),
                )
            )
            if conversation is None or conversation.owner_user_id is None:
                raise SessionUnavailable("The owner context is unavailable.")
            user = await session.get(User, conversation.owner_user_id)
            if user is None:
                raise SessionUnavailable("The owner context is unavailable.")
            membership, organization = await self._personal_membership(
                session, user.id
            )
            return OwnerRouteContext(
                display_name=user.display_name,
                organization_name=organization.name,
                organization_slug=organization.slug,
                role=membership.role.value,
                is_verified=user.is_verified,
            )

    async def sign_out(self, access_token: str) -> None:
        now = datetime.now(UTC)
        async with self.database.session() as session:
            async with session.begin():
                current = await self._resolve_access_in_session(
                    session, access_token, now
                )
                await self._revoke_auth_session(
                    session, current.auth_session_id, now
                )

    async def request_verification(self, access_token: str) -> EmailToken | None:
        current = await self.resolve_access_token(access_token)
        if current.user_id is None:
            raise SessionUnavailable("Authentication is required.")
        async with self.database.session() as session:
            async with session.begin():
                user = await session.get(User, current.user_id)
                if user is None or user.is_verified:
                    return None
                manager = self._manager(TransactionalUserDatabase(session, User))
                await manager.request_verify(user)
                if manager.generated_verification_token is None:
                    raise RuntimeError("Verification token generation failed.")
                return EmailToken(user.email, manager.generated_verification_token)

    async def request_verification_for_route(
        self,
        route_session_id: str,
    ) -> EmailToken | None:
        async with self.database.session() as session:
            async with session.begin():
                conversation = await session.scalar(
                    select(CorpusConversation).where(
                        CorpusConversation.route_session_id == route_session_id,
                        CorpusConversation.owner_user_id.is_not(None),
                    )
                )
                if conversation is None or conversation.owner_user_id is None:
                    raise SessionUnavailable("The owner context is unavailable.")
                user = await session.get(User, conversation.owner_user_id)
                if user is None:
                    raise SessionUnavailable("The owner context is unavailable.")
                if user.is_verified:
                    return None
                manager = self._manager(TransactionalUserDatabase(session, User))
                await manager.request_verify(user)
                if manager.generated_verification_token is None:
                    raise RuntimeError("Verification token generation failed.")
                return EmailToken(user.email, manager.generated_verification_token)

    async def verification_delivery_context_for_route(
        self,
        route_session_id: str,
    ) -> VerificationDeliveryContext:
        async with self.database.session() as session:
            conversation = await session.scalar(
                select(CorpusConversation).where(
                    CorpusConversation.route_session_id == route_session_id,
                    CorpusConversation.owner_user_id.is_not(None),
                )
            )
            if conversation is None or conversation.owner_user_id is None:
                raise SessionUnavailable("The owner context is unavailable.")
            user = await session.get(User, conversation.owner_user_id)
            if user is None:
                raise SessionUnavailable("The owner context is unavailable.")
            return VerificationDeliveryContext(
                recipient=user.email,
                already_verified=user.is_verified,
            )

    async def organization_id_for_route(self, route_session_id: str) -> uuid.UUID:
        async with self.database.session() as session:
            conversation = await session.scalar(
                select(CorpusConversation).where(
                    CorpusConversation.route_session_id == route_session_id,
                    CorpusConversation.owner_user_id.is_not(None),
                )
            )
            if conversation is None or conversation.owner_user_id is None:
                raise SessionUnavailable("The owner Workspace is unavailable.")
            _membership, organization = await self._personal_membership(
                session,
                conversation.owner_user_id,
            )
            return organization.id

    async def verify(self, token: str) -> None:
        from fastapi_users.exceptions import InvalidVerifyToken, UserAlreadyVerified

        async with self.database.session() as session:
            try:
                async with session.begin():
                    await self._manager(
                        TransactionalUserDatabase(session, User)
                    ).verify(token)
            except (InvalidVerifyToken, UserAlreadyVerified) as error:
                raise InvalidAuthToken(
                    "The verification token is invalid or expired."
                ) from error

    async def request_password_reset(self, email: str) -> EmailToken | None:
        from fastapi_users.exceptions import UserInactive, UserNotExists

        try:
            normalized = normalize_email(email)
        except ValueError:
            return None
        async with self.database.session() as session:
            async with session.begin():
                manager = self._manager(TransactionalUserDatabase(session, User))
                try:
                    user = await manager.get_by_email(normalized)
                    await manager.forgot_password(user)
                except (UserNotExists, UserInactive):
                    return None
                if manager.generated_reset_token is None:
                    raise RuntimeError("Password reset token generation failed.")
                return EmailToken(user.email, manager.generated_reset_token)

    async def confirm_password_reset(self, token: str, new_password: str) -> None:
        from fastapi_users.exceptions import (
            InvalidPasswordException,
            InvalidResetPasswordToken,
            UserInactive,
        )

        now = datetime.now(UTC)
        async with self.database.session() as session:
            try:
                async with session.begin():
                    manager = self._manager(TransactionalUserDatabase(session, User))
                    user = await manager.reset_password(token, new_password)
                    await session.execute(
                        update(AuthSession)
                        .where(
                            AuthSession.user_id == user.id,
                            AuthSession.revoked_at.is_(None),
                        )
                        .values(revoked_at=now)
                    )
                    session_ids = select(AuthSession.id).where(
                        AuthSession.user_id == user.id
                    )
                    await session.execute(
                        update(AccessToken)
                        .where(
                            AccessToken.auth_session_id.in_(session_ids),
                            AccessToken.revoked_at.is_(None),
                        )
                        .values(revoked_at=now)
                    )
            except (InvalidResetPasswordToken, UserInactive) as error:
                raise InvalidAuthToken(
                    "The reset token is invalid or expired."
                ) from error
            except InvalidPasswordException as error:
                raise ValueError(error.reason) from error

    async def _claim_anonymous_conversation(
        self,
        session,
        *,
        principal: CurrentPrincipal,
        conversation_id: str,
        route_session_id: str,
        owner_user_id: uuid.UUID,
        now: datetime,
    ) -> CorpusConversation:
        _require_anonymous_principal(principal)
        result = await session.execute(
            update(CorpusConversation)
            .where(
                CorpusConversation.public_id == conversation_id,
                CorpusConversation.route_session_id == route_session_id,
                CorpusConversation.anonymous_session_id
                == principal.auth_session_id,
                CorpusConversation.owner_user_id.is_(None),
                CorpusConversation.archived_at.is_(None),
            )
            .values(
                anonymous_session_id=None,
                owner_user_id=owner_user_id,
                updated_at=now,
            )
        )
        if result.rowcount != 1:
            raise ConversationUnavailable(
                "The selected anonymous conversation is unavailable."
            )
        conversation = await session.scalar(
            select(CorpusConversation).where(
                CorpusConversation.public_id == conversation_id,
                CorpusConversation.owner_user_id == owner_user_id,
            )
        )
        if conversation is None:
            raise ConversationUnavailable(
                "The selected anonymous conversation is unavailable."
            )
        return conversation

    def _conversation_owner_predicate(
        self, principal: CurrentPrincipal
    ) -> tuple[object, ...]:
        if principal.kind == "anonymous":
            return (
                CorpusConversation.anonymous_session_id
                == principal.auth_session_id,
            )
        return (CorpusConversation.owner_user_id == principal.user_id,)

    async def _resolve_access_in_session(
        self,
        session,
        access_token: str,
        now: datetime,
    ) -> CurrentPrincipal:
        row = (
            await session.execute(
                select(AccessToken, AuthSession)
                .join(
                    AuthSession,
                    AuthSession.id == AccessToken.auth_session_id,
                )
                .where(
                    AccessToken.token_hash == hash_opaque_token(access_token)
                )
            )
        ).one_or_none()
        if row is None:
            raise SessionUnavailable("The access token is unavailable.")
        access, auth_session = row
        if (
            access.revoked_at is not None
            or now >= _as_utc(access.expires_at)
            or not _refresh_is_active(
                auth_session,
                now=now,
                idle_timeout=self.idle_lifetime,
            )
        ):
            raise SessionUnavailable("The access token is unavailable.")
        owner: OwnerPrincipalView | None = None
        organization_id: uuid.UUID | None = None
        if auth_session.user_id is not None:
            user = await session.get(User, auth_session.user_id)
            if user is None or not user.is_active:
                raise SessionUnavailable("The access token is unavailable.")
            membership, organization = await self._personal_membership(
                session, user.id
            )
            owner = _owner_principal(user, organization, membership)
            organization_id = organization.id
        return CurrentPrincipal(
            kind="owner" if auth_session.user_id is not None else "anonymous",
            auth_session_id=auth_session.id,
            user_id=auth_session.user_id,
            organization_id=organization_id,
            access_expires_at=_as_utc(access.expires_at),
            owner=owner,
        )

    async def _issue_token_pair(
        self,
        session,
        *,
        user_id: uuid.UUID | None,
        now: datetime,
    ) -> TokenPairView:
        refresh = issue_opaque_token()
        auth_session = AuthSession(
            user_id=user_id,
            refresh_token_hash=refresh.digest,
            created_at=now,
            last_seen_at=now,
            absolute_expires_at=now + self.absolute_lifetime,
            revoked_at=None,
        )
        session.add(auth_session)
        await session.flush()
        return await self._issue_access_for_session(
            session,
            auth_session=auth_session,
            refresh_token=refresh.raw,
            now=now,
        )

    async def _issue_access_for_session(
        self,
        session,
        *,
        auth_session: AuthSession,
        refresh_token: str,
        now: datetime,
    ) -> TokenPairView:
        access = issue_opaque_token()
        access_expires_at = now + self.access_lifetime
        session.add(
            AccessToken(
                auth_session_id=auth_session.id,
                token_hash=access.digest,
                created_at=now,
                expires_at=access_expires_at,
                revoked_at=None,
            )
        )
        if auth_session.user_id is None:
            principal = AnonymousPrincipalView()
        else:
            user = await session.get(User, auth_session.user_id)
            if user is None:
                raise SessionUnavailable("The owner is unavailable.")
            membership, organization = await self._personal_membership(
                session, user.id
            )
            principal = _owner_principal(user, organization, membership)
        absolute = _as_utc(auth_session.absolute_expires_at)
        return TokenPairView(
            access_token=access.raw,
            access_expires_at=access_expires_at,
            refresh_token=refresh_token,
            refresh_idle_expires_at=min(now + self.idle_lifetime, absolute),
            refresh_absolute_expires_at=absolute,
            principal=principal,
        )

    async def _personal_membership(self, session, user_id):
        return (
            await session.execute(
                select(Membership, Organization)
                .join(
                    Organization,
                    Organization.id == Membership.organization_id,
                )
                .where(Membership.user_id == user_id)
                .order_by(Membership.created_at)
            )
        ).one()

    async def _revoke_auth_session(
        self, session, auth_session_id, now: datetime
    ) -> None:
        await session.execute(
            update(AuthSession)
            .where(
                AuthSession.id == auth_session_id,
                AuthSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        await session.execute(
            update(AccessToken)
            .where(
                AccessToken.auth_session_id == auth_session_id,
                AccessToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )


def _clean_display_name(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def _workspace_stem(user: User, display_name: str | None) -> str:
    return display_name or user.email.partition("@")[0]


def _workspace_name(user: User, display_name: str | None) -> str:
    return f"{_workspace_stem(user, display_name)}'s Workspace"


async def _available_slug(session, user: User, display_name: str | None) -> str:
    stem = _workspace_stem(user, display_name).casefold()
    base = re.sub(r"[^a-z0-9]+", "-", stem).strip("-") or "workspace"
    base = f"{base}-workspace"
    candidate = base
    suffix = 2
    while await session.scalar(
        select(Organization.id).where(Organization.slug == candidate)
    ):
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _view(
    user: User,
    organization: Organization,
    membership: Membership,
    route_session_state: str,
) -> OwnerSessionView:
    return OwnerSessionView(
        owner=OwnerView.model_validate(user),
        organization=OrganizationView(
            name=organization.name, slug=organization.slug
        ),
        membership=MembershipView(role=membership.role.value),
        route_session_state=route_session_state,
    )


def _owner_principal(
    user: User,
    organization: Organization,
    membership: Membership,
) -> OwnerPrincipalView:
    return OwnerPrincipalView(
        owner=OwnerView.model_validate(user),
        organization=OrganizationView(
            name=organization.name, slug=organization.slug
        ),
        membership=MembershipView(role=membership.role.value),
    )


def _as_utc(value: datetime) -> datetime:
    return (
        value.replace(tzinfo=UTC)
        if value.tzinfo is None
        else value.astimezone(UTC)
    )


def _require_anonymous_principal(principal: CurrentPrincipal) -> None:
    if principal.kind != "anonymous":
        raise ConversationUnavailable(
            "Account access requires an anonymous conversation."
        )


def _refresh_is_active(
    auth_session: AuthSession,
    *,
    now: datetime,
    idle_timeout: timedelta,
) -> bool:
    return (
        auth_session.revoked_at is None
        and now < _as_utc(auth_session.absolute_expires_at)
        and now - _as_utc(auth_session.last_seen_at) < idle_timeout
    )


__all__ = [
    "AuthConflict",
    "AuthService",
    "AuthServiceError",
    "ConversationLimitReached",
    "ConversationUnavailable",
    "CurrentPrincipal",
    "EmailToken",
    "InvalidAuthToken",
    "InvalidCredentials",
    "IssuedOwnerSession",
    "SessionUnavailable",
    "VerificationDeliveryContext",
]
