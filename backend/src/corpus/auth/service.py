from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.exceptions import InvalidPasswordException, UserAlreadyExists
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from .database import AuthDatabase, TransactionalUserDatabase
from .manager import CorpusUserManager
from .models import (
    AuthSession,
    Membership,
    MembershipRole,
    Organization,
    OwnerRouteClaim,
    OwnerRouteHandle,
    User,
)
from .schemas import (
    MembershipView,
    OrganizationView,
    OwnerSessionView,
    OwnerUserCreate,
    OwnerView,
)
from .security import issue_opaque_token, normalize_email, validate_password


class AuthServiceError(RuntimeError):
    pass


class AuthConflict(AuthServiceError):
    pass


class InvalidCredentials(AuthServiceError):
    pass


class GuestSessionUnavailable(AuthServiceError):
    pass


class SessionUnavailable(AuthServiceError):
    pass


class InvalidAuthToken(AuthServiceError):
    pass


@dataclass(frozen=True)
class IssuedOwnerSession:
    view: OwnerSessionView
    auth_token: str
    owner_route_handle: str
    route_session_id: str


@dataclass(frozen=True)
class CurrentOwnerSession:
    view: OwnerSessionView
    auth_session_id: object
    user_id: object
    route_session_id: str | None


@dataclass(frozen=True)
class EmailToken:
    recipient: str
    token: str


@dataclass(frozen=True)
class OwnerRouteContext:
    display_name: str | None
    organization_name: str
    organization_slug: str
    role: str
    is_verified: bool


class AuthService:
    def __init__(
        self,
        database: AuthDatabase,
        *,
        reset_secret: str = "test-reset-secret-at-least-32-bytes-long",
        verification_secret: str = "test-verification-secret-at-least-32-bytes-long",
        idle_lifetime: timedelta = timedelta(days=7),
        absolute_lifetime: timedelta = timedelta(days=30),
        reset_token_lifetime: timedelta = timedelta(hours=1),
        verification_token_lifetime: timedelta = timedelta(hours=24),
    ) -> None:
        self.database = database
        self.reset_secret = reset_secret
        self.verification_secret = verification_secret
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

    async def register(
        self,
        *,
        email: str,
        password: str,
        display_name: str | None,
        guest_route_session_id: str,
    ) -> IssuedOwnerSession:
        normalized = normalize_email(email)
        validate_password(password, normalized)
        cleaned_name = _clean_display_name(display_name)
        now = datetime.now(UTC)
        try:
            async with self.database.session() as session:
                async with session.begin():
                    if await session.get(OwnerRouteClaim, guest_route_session_id):
                        raise GuestSessionUnavailable(
                            "The guest Workspace session is unavailable."
                        )
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
                    session.add(
                        OwnerRouteClaim(
                            route_session_id=guest_route_session_id,
                            user_id=user.id,
                            organization_id=organization.id,
                            claimed_at=now,
                        )
                    )
                    issued = await self._issue_browser_session(
                        session,
                        user=user,
                        organization=organization,
                        membership=membership,
                        route_session_id=guest_route_session_id,
                        route_session_state="adopted",
                        now=now,
                    )
                return issued
        except (UserAlreadyExists, IntegrityError) as error:
            raise AuthConflict("An owner with that email already exists.") from error
        except InvalidPasswordException as error:
            raise ValueError(error.reason) from error

    async def sign_in(
        self,
        *,
        email: str,
        password: str,
        guest_route_session_id: str | None,
        current_auth_token: str | None = None,
    ) -> IssuedOwnerSession:
        try:
            normalized = normalize_email(email)
        except ValueError as error:
            raise InvalidCredentials("Invalid email or password.") from error
        now = datetime.now(UTC)
        async with self.database.session() as session:
            async with session.begin():
                user_db = TransactionalUserDatabase(session, User)
                user = await self._manager(user_db).authenticate(
                    OAuth2PasswordRequestForm(
                        username=normalized,
                        password=password,
                    )
                )
                if user is None or not user.is_active:
                    raise InvalidCredentials("Invalid email or password.")
                if current_auth_token:
                    previous = await session.scalar(
                        select(AuthSession).where(
                            AuthSession.token_hash == _hash(current_auth_token)
                        )
                    )
                    if previous is not None:
                        await self._revoke_auth_session(session, previous.id, now)
                membership, organization = (
                    await session.execute(
                        select(Membership, Organization)
                        .join(
                            Organization,
                            Organization.id == Membership.organization_id,
                        )
                        .where(Membership.user_id == user.id)
                        .order_by(Membership.created_at)
                    )
                ).one()
                claim = await session.scalar(
                    select(OwnerRouteClaim)
                    .where(OwnerRouteClaim.user_id == user.id)
                    .order_by(OwnerRouteClaim.claimed_at)
                )
                state = "resumed"
                if claim is None:
                    if not guest_route_session_id or await session.get(
                        OwnerRouteClaim, guest_route_session_id
                    ):
                        raise GuestSessionUnavailable(
                            "The guest Workspace session is unavailable."
                        )
                    claim = OwnerRouteClaim(
                        route_session_id=guest_route_session_id,
                        user_id=user.id,
                        organization_id=organization.id,
                        claimed_at=now,
                    )
                    session.add(claim)
                    state = "adopted"
                return await self._issue_browser_session(
                    session,
                    user=user,
                    organization=organization,
                    membership=membership,
                    route_session_id=claim.route_session_id,
                    route_session_state=state,
                    now=now,
                )

    async def resolve_browser_session(
        self,
        *,
        auth_token: str,
        owner_route_handle: str | None,
        require_route: bool,
    ) -> CurrentOwnerSession:
        now = datetime.now(UTC)
        async with self.database.session() as session:
            async with session.begin():
                auth_session = await session.scalar(
                    select(AuthSession).where(
                        AuthSession.token_hash == _hash(auth_token)
                    )
                )
                if auth_session is None or not _session_is_active(
                    auth_session,
                    now=now,
                    idle_timeout=self.idle_lifetime,
                ):
                    if auth_session is not None and auth_session.revoked_at is None:
                        await self._revoke_auth_session(session, auth_session.id, now)
                    raise SessionUnavailable("The owner session is unavailable.")
                route_session_id: str | None = None
                if require_route:
                    if not owner_route_handle:
                        raise SessionUnavailable("The owner session is unavailable.")
                    handle = await session.scalar(
                        select(OwnerRouteHandle).where(
                            OwnerRouteHandle.token_hash == _hash(owner_route_handle),
                            OwnerRouteHandle.auth_session_id == auth_session.id,
                            OwnerRouteHandle.revoked_at.is_(None),
                        )
                    )
                    if handle is None:
                        raise SessionUnavailable("The owner session is unavailable.")
                    claim = await session.get(OwnerRouteClaim, handle.route_session_id)
                    if claim is None or claim.user_id != auth_session.user_id:
                        raise SessionUnavailable("The owner session is unavailable.")
                    route_session_id = claim.route_session_id
                user = await session.get(User, auth_session.user_id)
                if user is None or not user.is_active:
                    raise SessionUnavailable("The owner session is unavailable.")
                membership, organization = await self._personal_membership(session, user.id)
                auth_session.last_seen_at = now
                return CurrentOwnerSession(
                    view=_view(user, organization, membership, "resumed"),
                    auth_session_id=auth_session.id,
                    user_id=user.id,
                    route_session_id=route_session_id,
                )

    async def is_route_claimed(self, route_session_id: str) -> bool:
        async with self.database.session() as session:
            return await session.get(OwnerRouteClaim, route_session_id) is not None

    async def owner_context_for_route(
        self,
        route_session_id: str,
    ) -> OwnerRouteContext:
        async with self.database.session() as session:
            claim = await session.get(OwnerRouteClaim, route_session_id)
            if claim is None:
                raise SessionUnavailable("The owner context is unavailable.")
            user = await session.get(User, claim.user_id)
            organization = await session.get(Organization, claim.organization_id)
            membership = await session.scalar(
                select(Membership).where(
                    Membership.user_id == claim.user_id,
                    Membership.organization_id == claim.organization_id,
                )
            )
            if user is None or organization is None or membership is None:
                raise SessionUnavailable("The owner context is unavailable.")
            return OwnerRouteContext(
                display_name=user.display_name,
                organization_name=organization.name,
                organization_slug=organization.slug,
                role=membership.role.value,
                is_verified=user.is_verified,
            )

    async def sign_out(self, auth_token: str | None) -> None:
        if not auth_token:
            return
        now = datetime.now(UTC)
        async with self.database.session() as session:
            async with session.begin():
                auth_session = await session.scalar(
                    select(AuthSession).where(AuthSession.token_hash == _hash(auth_token))
                )
                if auth_session is not None:
                    await self._revoke_auth_session(session, auth_session.id, now)

    async def request_verification(self, auth_token: str) -> EmailToken | None:
        current = await self.resolve_browser_session(
            auth_token=auth_token,
            owner_route_handle=None,
            require_route=False,
        )
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

    async def verify(self, token: str) -> None:
        from fastapi_users.exceptions import InvalidVerifyToken, UserAlreadyVerified

        async with self.database.session() as session:
            try:
                async with session.begin():
                    await self._manager(
                        TransactionalUserDatabase(session, User)
                    ).verify(token)
            except (InvalidVerifyToken, UserAlreadyVerified) as error:
                raise InvalidAuthToken("The verification token is invalid or expired.") from error

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
                        .where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
                        .values(revoked_at=now)
                    )
                    session_ids = select(AuthSession.id).where(AuthSession.user_id == user.id)
                    await session.execute(
                        update(OwnerRouteHandle)
                        .where(
                            OwnerRouteHandle.auth_session_id.in_(session_ids),
                            OwnerRouteHandle.revoked_at.is_(None),
                        )
                        .values(revoked_at=now)
                    )
            except (InvalidResetPasswordToken, UserInactive) as error:
                raise InvalidAuthToken("The reset token is invalid or expired.") from error
            except InvalidPasswordException as error:
                raise ValueError(error.reason) from error

    async def _personal_membership(self, session, user_id):
        return (
            await session.execute(
                select(Membership, Organization)
                .join(Organization, Organization.id == Membership.organization_id)
                .where(Membership.user_id == user_id)
                .order_by(Membership.created_at)
            )
        ).one()

    async def _revoke_auth_session(self, session, auth_session_id, now: datetime) -> None:
        await session.execute(
            update(AuthSession)
            .where(AuthSession.id == auth_session_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        await session.execute(
            update(OwnerRouteHandle)
            .where(
                OwnerRouteHandle.auth_session_id == auth_session_id,
                OwnerRouteHandle.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

    async def _issue_browser_session(
        self,
        session,
        *,
        user: User,
        organization: Organization,
        membership: Membership,
        route_session_id: str,
        route_session_state: str,
        now: datetime,
    ) -> IssuedOwnerSession:
        auth_token = issue_opaque_token()
        auth_session = AuthSession(
            user_id=user.id,
            token_hash=auth_token.digest,
            created_at=now,
            last_seen_at=now,
            absolute_expires_at=now + self.absolute_lifetime,
            revoked_at=None,
        )
        session.add(auth_session)
        await session.flush()
        route_handle = issue_opaque_token()
        session.add(
            OwnerRouteHandle(
                auth_session_id=auth_session.id,
                route_session_id=route_session_id,
                token_hash=route_handle.digest,
                created_at=now,
                revoked_at=None,
            )
        )
        return IssuedOwnerSession(
            view=_view(user, organization, membership, route_session_state),
            auth_token=auth_token.raw,
            owner_route_handle=route_handle.raw,
            route_session_id=route_session_id,
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
    while await session.scalar(select(Organization.id).where(Organization.slug == candidate)):
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
        organization=OrganizationView(name=organization.name, slug=organization.slug),
        membership=MembershipView(role=membership.role.value),
        route_session_state=route_session_state,
    )


def _hash(raw: str) -> str:
    from .security import hash_opaque_token

    return hash_opaque_token(raw)


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _session_is_active(
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
    "CurrentOwnerSession",
    "EmailToken",
    "GuestSessionUnavailable",
    "InvalidCredentials",
    "InvalidAuthToken",
    "IssuedOwnerSession",
    "OwnerRouteContext",
    "SessionUnavailable",
]
