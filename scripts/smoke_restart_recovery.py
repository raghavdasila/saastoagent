from __future__ import annotations

import asyncio
import json
import os
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path, PureWindowsPath
from typing import Any, TextIO
from urllib.parse import urlsplit
from uuid import UUID, uuid4

import httpx
from fastapi_users.password import PasswordHelper
from sqlalchemy import delete, or_, select
from sqlalchemy.engine import make_url

from corpus.auth.config import AuthSettings
from corpus.persistence import CorpusDatabase
from corpus.auth.models import (
    AccessToken,
    AuthSession,
    CorpusConversation,
    Membership,
    MembershipRole,
    Organization,
    User,
)
from corpus.auth.security import hash_opaque_token, issue_opaque_token


_TEMPORARY_OWNER_PREFIX = "restart-smoke-"
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
_OWNER_FIELDS = frozenset(
    {
        "access_token",
        "access_token_hash",
        "access_token_id",
        "auth_session_id",
        "refresh_token_hash",
        "owner_user_id",
        "organization_id",
        "membership_id",
        "email",
        "organization_slug",
    }
)
_CONVERSATION_FIELDS = frozenset(
    {"row_id", "public_id", "route_session_id", "owner_user_id"}
)
_READY_STATE_FIELDS = frozenset(
    {"status", "reservation_id", "owner", "conversation", "request_id"}
)


@dataclass(frozen=True)
class TemporaryOwner:
    access_token: str
    access_token_hash: str
    access_token_id: UUID
    auth_session_id: UUID
    refresh_token_hash: str
    owner_user_id: UUID
    organization_id: UUID
    membership_id: UUID
    email: str
    organization_slug: str

    def to_payload(self) -> dict[str, str]:
        return {
            "access_token": self.access_token,
            "access_token_hash": self.access_token_hash,
            "access_token_id": str(self.access_token_id),
            "auth_session_id": str(self.auth_session_id),
            "refresh_token_hash": self.refresh_token_hash,
            "owner_user_id": str(self.owner_user_id),
            "organization_id": str(self.organization_id),
            "membership_id": str(self.membership_id),
            "email": self.email,
            "organization_slug": self.organization_slug,
        }

    @classmethod
    def from_payload(cls, payload: object) -> TemporaryOwner:
        values = _exact_string_payload(payload, _OWNER_FIELDS, "owner")
        owner = cls(
            access_token=values["access_token"],
            access_token_hash=values["access_token_hash"],
            access_token_id=UUID(values["access_token_id"]),
            auth_session_id=UUID(values["auth_session_id"]),
            refresh_token_hash=values["refresh_token_hash"],
            owner_user_id=UUID(values["owner_user_id"]),
            organization_id=UUID(values["organization_id"]),
            membership_id=UUID(values["membership_id"]),
            email=values["email"],
            organization_slug=values["organization_slug"],
        )
        if hash_opaque_token(owner.access_token) != owner.access_token_hash:
            raise ValueError("Restart smoke owner token hash does not match.")
        return owner


@dataclass(frozen=True)
class TemporaryConversation:
    row_id: UUID
    public_id: str
    route_session_id: str
    owner_user_id: UUID

    def to_payload(self) -> dict[str, str]:
        return {
            "row_id": str(self.row_id),
            "public_id": self.public_id,
            "route_session_id": self.route_session_id,
            "owner_user_id": str(self.owner_user_id),
        }

    @classmethod
    def from_payload(cls, payload: object) -> TemporaryConversation:
        values = _exact_string_payload(
            payload,
            _CONVERSATION_FIELDS,
            "conversation",
        )
        return cls(
            row_id=UUID(values["row_id"]),
            public_id=values["public_id"],
            route_session_id=values["route_session_id"],
            owner_user_id=UUID(values["owner_user_id"]),
        )


@dataclass(frozen=True)
class RestartSmokeState:
    reservation_id: str
    owner: TemporaryOwner
    conversation: TemporaryConversation
    request_id: str

    def __post_init__(self) -> None:
        if not self.reservation_id or not self.request_id:
            raise ValueError("Restart smoke state identifiers must be non-empty.")
        if self.conversation.owner_user_id != self.owner.owner_user_id:
            raise ValueError("Restart smoke conversation owner does not match.")

    def to_payload(self) -> dict[str, object]:
        return {
            "status": "ready",
            "reservation_id": self.reservation_id,
            "owner": self.owner.to_payload(),
            "conversation": self.conversation.to_payload(),
            "request_id": self.request_id,
        }

    @classmethod
    def from_payload(cls, payload: object) -> RestartSmokeState:
        if not isinstance(payload, dict) or set(payload) != _READY_STATE_FIELDS:
            raise ValueError(
                "Restart smoke state must contain exactly the expected fields."
            )
        if payload.get("status") != "ready":
            raise ValueError("Restart smoke state is not ready for verification.")
        reservation_id = payload.get("reservation_id")
        request_id = payload.get("request_id")
        if not isinstance(reservation_id, str) or not isinstance(request_id, str):
            raise ValueError("Restart smoke state identifiers must be strings.")
        return cls(
            reservation_id=reservation_id,
            owner=TemporaryOwner.from_payload(payload.get("owner")),
            conversation=TemporaryConversation.from_payload(
                payload.get("conversation")
            ),
            request_id=request_id,
        )


@dataclass
class StateReservation:
    path: Path
    reservation_id: str
    stream: TextIO
    finalized: bool = False

    @classmethod
    def acquire(cls, path: Path) -> StateReservation:
        path.parent.mkdir(parents=True, exist_ok=True)
        reservation_id = uuid4().hex
        try:
            stream = path.open("x+", encoding="utf-8")
        except FileExistsError as error:
            raise RuntimeError(
                f"Restart smoke state already exists and will not be overwritten: "
                f"{path}"
            ) from error
        reservation = cls(path=path, reservation_id=reservation_id, stream=stream)
        reservation._write_owned_payload(
            {"status": "reserved", "reservation_id": reservation_id}
        )
        return reservation

    def record_owner(self, owner: TemporaryOwner) -> None:
        self._write_owned_payload(
            {
                "status": "identity_created",
                "reservation_id": self.reservation_id,
                "owner": owner.to_payload(),
            }
        )

    def record_conversation(
        self,
        owner: TemporaryOwner,
        conversation: TemporaryConversation,
    ) -> None:
        self._write_owned_payload(
            {
                "status": "conversation_created",
                "reservation_id": self.reservation_id,
                "owner": owner.to_payload(),
                "conversation": conversation.to_payload(),
            }
        )

    def finalize(self, state: RestartSmokeState) -> None:
        if state.reservation_id != self.reservation_id:
            raise RuntimeError("Restart smoke reservation identity changed.")
        self._write_owned_payload(state.to_payload())
        self.finalized = True
        self.close()

    def abort_after_cleanup(self) -> None:
        self.close()
        payload = _load_json(self.path)
        if (
            not isinstance(payload, dict)
            or payload.get("reservation_id") != self.reservation_id
        ):
            raise RuntimeError(
                "Restart smoke reservation changed; refusing to remove it."
            )
        self.path.unlink()

    def close(self) -> None:
        if not self.stream.closed:
            self.stream.close()

    def _write_owned_payload(self, payload: dict[str, object]) -> None:
        if self.finalized or self.stream.closed:
            raise RuntimeError("Restart smoke reservation is no longer writable.")
        self.stream.seek(0)
        current_text = self.stream.read()
        if current_text:
            current = json.loads(current_text)
            if (
                not isinstance(current, dict)
                or current.get("reservation_id") != self.reservation_id
            ):
                raise RuntimeError("Restart smoke reservation identity changed.")
        self.stream.seek(0)
        self.stream.truncate()
        json.dump(payload, self.stream, separators=(",", ":"))
        self.stream.flush()
        os.fsync(self.stream.fileno())


def main() -> None:
    raise SystemExit(
        "Direct prepare/verify execution is disabled because it cannot own the "
        "RouteDeck database. Run scripts/smoke_restart_recovery_isolated.py."
    )


def _prepare(
    base_url: str,
    origin: str,
    state_file: Path,
    *,
    settings: AuthSettings,
    database_url: str,
    migration_revision: str,
) -> None:
    reservation = StateReservation.acquire(state_file)
    owner: TemporaryOwner | None = None
    conversation: TemporaryConversation | None = None
    try:
        owner = asyncio.run(
            _create_temporary_owner(
                database_url,
                migration_revision=migration_revision,
                access_lifetime=timedelta(minutes=settings.access_token_minutes),
                absolute_lifetime=timedelta(days=settings.absolute_session_days),
            )
        )
        reservation.record_owner(owner)
        with httpx.Client(
            base_url=base_url,
            headers={
                "Origin": origin,
                "Authorization": f"Bearer {owner.access_token}",
            },
            timeout=180.0,
        ) as client:
            identity = client.get("/api/auth/session")
            identity.raise_for_status()
            _assert_owner_identity(
                identity.json(),
                email=owner.email,
                organization_slug=owner.organization_slug,
            )
            created = client.post("/api/conversations", json={})
            created.raise_for_status()
            conversation_id = _required_string(created.json(), "id")
            conversation = asyncio.run(
                _load_temporary_conversation(
                    database_url,
                    migration_revision=migration_revision,
                    owner=owner,
                    public_id=conversation_id,
                )
            )
            reservation.record_conversation(owner, conversation)
            client.headers["X-Corpus-Conversation-ID"] = conversation.public_id
            active = created.json().get("active_run")
            if active is not None:
                if not isinstance(active, dict):
                    raise RuntimeError("The created conversation has an invalid run.")
                _wait_for_terminal(client, _required_string(active, "request_id"))

            projection = client.get("/api/routedeck/session")
            projection.raise_for_status()
            projection_body = projection.json()
            request_id = f"restart-smoke-{uuid4().hex}"
            started = client.post(
                "/api/routedeck/conversation/runs",
                json={
                    "request_id": request_id,
                    "expected_session_version": projection_body["projection"][
                        "session_version"
                    ],
                    "trigger": "user_message",
                    "message": (
                        "Explain Corpus architecture in a detailed multi-section "
                        "response so this generation remains active during an "
                        "immediate process stop."
                    ),
                },
            )
            started.raise_for_status()
            run = started.json().get("run")
            if not isinstance(run, dict) or run.get("stage") not in {
                "awaiting_model",
                "generating",
            }:
                raise RuntimeError(
                    f"The restart smoke did not obtain an active durable run: {run}"
                )

        reservation.finalize(
            RestartSmokeState(
                reservation_id=reservation.reservation_id,
                owner=owner,
                conversation=conversation,
                request_id=request_id,
            )
        )
    except BaseException:
        try:
            if owner is not None:
                asyncio.run(
                    _delete_temporary_owner(
                        database_url,
                        migration_revision=migration_revision,
                        owner=owner,
                        conversation=conversation,
                    )
                )
        except BaseException:
            reservation.close()
            raise
        reservation.abort_after_cleanup()
        raise
    print(f"restart_smoke_prepared request_id={request_id}")
    print(
        "owner=temporary bearer=real conversation=public "
        f"state_file={state_file.resolve()}"
    )


def _verify(
    base_url: str,
    origin: str,
    state_file: Path,
    *,
    settings: AuthSettings,
    database_url: str,
    migration_revision: str,
) -> None:
    state = _read_state(state_file)
    headers = {
        "Origin": origin,
        "Authorization": f"Bearer {state.owner.access_token}",
        "X-Corpus-Conversation-ID": state.conversation.public_id,
    }
    try:
        with httpx.Client(base_url=base_url, headers=headers, timeout=30.0) as client:
            identity = client.get("/api/auth/session")
            identity.raise_for_status()
            _assert_owner_identity(
                identity.json(),
                email=state.owner.email,
                organization_slug=state.owner.organization_slug,
            )
            catalog = client.get("/api/conversations")
            catalog.raise_for_status()
            catalog_items = catalog.json().get("conversations")
            if not isinstance(
                catalog_items, list
            ) or state.conversation.public_id not in {
                item.get("id") for item in catalog_items if isinstance(item, dict)
            }:
                raise RuntimeError(
                    "The owner-authorized public conversation was lost across restart."
                )
            selected = client.get(f"/api/conversations/{state.conversation.public_id}")
            selected.raise_for_status()
            if selected.json().get("id") != state.conversation.public_id:
                raise RuntimeError(
                    "The selected public conversation changed across restart."
                )
            recovered = client.get(
                f"/api/routedeck/conversation/runs/{state.request_id}"
            )
            recovered.raise_for_status()
            run = recovered.json().get("run")
            if (
                not isinstance(run, dict)
                or run.get("stage") != "interrupted"
                or not isinstance(run.get("failure"), dict)
                or run["failure"].get("code") != "turn_interrupted"
            ):
                raise RuntimeError(f"Unexpected recovered run: {run}")
    finally:
        asyncio.run(
            _delete_temporary_owner(
                database_url,
                migration_revision=migration_revision,
                owner=state.owner,
                conversation=state.conversation,
            )
        )
        state_file.unlink()
    print("Corpus backend restart recovery smoke passed.")
    print(
        "owner_identity=authorized conversation=authorized "
        "run=durably_interrupted cleanup=complete"
    )


async def _create_temporary_owner(
    database_url: str,
    *,
    migration_revision: str,
    access_lifetime: timedelta,
    absolute_lifetime: timedelta,
) -> TemporaryOwner:
    database = CorpusDatabase(database_url)
    try:
        await database.verify_revision(migration_revision)
        now = datetime.now(UTC)
        unique = uuid4().hex
        email = f"{_TEMPORARY_OWNER_PREFIX}{unique}@example.com"
        organization_slug = f"{_TEMPORARY_OWNER_PREFIX}{unique}"
        hashed_password = PasswordHelper().hash(secrets.token_urlsafe(32))
        owner = User(
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False,
            is_verified=True,
            display_name="Restart Smoke Owner",
        )
        organization = Organization(
            name="Restart Smoke Workspace",
            slug=organization_slug,
            created_at=now,
        )
        refresh = issue_opaque_token()
        access = issue_opaque_token()
        async with database.session() as session:
            async with session.begin():
                session.add_all((owner, organization))
                await session.flush()
                membership = Membership(
                    user_id=owner.id,
                    organization_id=organization.id,
                    role=MembershipRole.OWNER,
                    created_at=now,
                )
                auth_session = AuthSession(
                    user_id=owner.id,
                    refresh_token_hash=refresh.digest,
                    created_at=now,
                    last_seen_at=now,
                    absolute_expires_at=now + absolute_lifetime,
                    revoked_at=None,
                )
                session.add_all((membership, auth_session))
                await session.flush()
                access_token = AccessToken(
                    auth_session_id=auth_session.id,
                    token_hash=access.digest,
                    created_at=now,
                    expires_at=now + access_lifetime,
                    revoked_at=None,
                )
                session.add(access_token)
                await session.flush()
        return TemporaryOwner(
            access_token=access.raw,
            access_token_hash=access.digest,
            access_token_id=access_token.id,
            auth_session_id=auth_session.id,
            refresh_token_hash=refresh.digest,
            owner_user_id=owner.id,
            organization_id=organization.id,
            membership_id=membership.id,
            email=email,
            organization_slug=organization_slug,
        )
    finally:
        await database.close()


async def _load_temporary_conversation(
    database_url: str,
    *,
    migration_revision: str,
    owner: TemporaryOwner,
    public_id: str,
) -> TemporaryConversation:
    database = CorpusDatabase(database_url)
    try:
        await database.verify_revision(migration_revision)
        async with database.session() as session:
            rows = tuple(
                await session.scalars(
                    select(CorpusConversation).where(
                        CorpusConversation.owner_user_id == owner.owner_user_id
                    )
                )
            )
            if len(rows) != 1 or rows[0].public_id != public_id:
                raise RuntimeError(
                    "The temporary owner does not exclusively own the expected "
                    "conversation."
                )
            row = rows[0]
            if row.anonymous_session_id is not None or row.archived_at is not None:
                raise RuntimeError(
                    "The temporary conversation has unexpected ownership state."
                )
            return TemporaryConversation(
                row_id=row.id,
                public_id=row.public_id,
                route_session_id=row.route_session_id,
                owner_user_id=owner.owner_user_id,
            )
    finally:
        await database.close()


async def _delete_temporary_owner(
    database_url: str,
    *,
    migration_revision: str,
    owner: TemporaryOwner,
    conversation: TemporaryConversation | None,
) -> None:
    database = CorpusDatabase(database_url)
    try:
        await database.verify_revision(migration_revision)
        async with database.session() as session:
            async with session.begin():
                await _validate_exclusive_cleanup_ownership(
                    session,
                    owner=owner,
                    conversation=conversation,
                )
                await session.execute(
                    delete(User).where(User.id == owner.owner_user_id)
                )
                await session.execute(
                    delete(Organization).where(Organization.id == owner.organization_id)
                )
    finally:
        await database.close()


async def _validate_exclusive_cleanup_ownership(
    session,
    *,
    owner: TemporaryOwner,
    conversation: TemporaryConversation | None,
) -> None:
    user = await session.get(User, owner.owner_user_id)
    organization = await session.get(Organization, owner.organization_id)
    if (
        user is None
        or user.email != owner.email
        or not user.email.startswith(_TEMPORARY_OWNER_PREFIX)
        or user.display_name != "Restart Smoke Owner"
        or not user.is_active
        or user.is_superuser
        or not user.is_verified
    ):
        _cleanup_mismatch("user")
    if (
        organization is None
        or organization.slug != owner.organization_slug
        or not organization.slug.startswith(_TEMPORARY_OWNER_PREFIX)
        or organization.name != "Restart Smoke Workspace"
    ):
        _cleanup_mismatch("organization")

    memberships = tuple(
        await session.scalars(
            select(Membership).where(
                or_(
                    Membership.user_id == owner.owner_user_id,
                    Membership.organization_id == owner.organization_id,
                )
            )
        )
    )
    if (
        len(memberships) != 1
        or memberships[0].id != owner.membership_id
        or memberships[0].user_id != owner.owner_user_id
        or memberships[0].organization_id != owner.organization_id
        or memberships[0].role is not MembershipRole.OWNER
    ):
        _cleanup_mismatch("exclusive owner membership")

    auth_sessions = tuple(
        await session.scalars(
            select(AuthSession).where(AuthSession.user_id == owner.owner_user_id)
        )
    )
    if (
        len(auth_sessions) != 1
        or auth_sessions[0].id != owner.auth_session_id
        or auth_sessions[0].refresh_token_hash != owner.refresh_token_hash
        or auth_sessions[0].revoked_at is not None
    ):
        _cleanup_mismatch("auth session")

    access_tokens = tuple(
        await session.scalars(
            select(AccessToken).where(
                or_(
                    AccessToken.auth_session_id == owner.auth_session_id,
                    AccessToken.token_hash == owner.access_token_hash,
                )
            )
        )
    )
    if (
        hash_opaque_token(owner.access_token) != owner.access_token_hash
        or len(access_tokens) != 1
        or access_tokens[0].id != owner.access_token_id
        or access_tokens[0].auth_session_id != owner.auth_session_id
        or access_tokens[0].token_hash != owner.access_token_hash
        or access_tokens[0].revoked_at is not None
    ):
        _cleanup_mismatch("access token")

    conversations = tuple(
        await session.scalars(
            select(CorpusConversation).where(
                CorpusConversation.owner_user_id == owner.owner_user_id
            )
        )
    )
    if conversation is None:
        if conversations:
            _cleanup_mismatch("unexpected conversation")
        return
    if (
        conversation.owner_user_id != owner.owner_user_id
        or len(conversations) != 1
        or conversations[0].id != conversation.row_id
        or conversations[0].public_id != conversation.public_id
        or conversations[0].route_session_id != conversation.route_session_id
        or conversations[0].owner_user_id != owner.owner_user_id
        or conversations[0].anonymous_session_id is not None
        or conversations[0].archived_at is not None
    ):
        _cleanup_mismatch("conversation")


def _cleanup_mismatch(subject: str) -> None:
    raise RuntimeError(
        f"Restart smoke cleanup ownership mismatch for {subject}; nothing was deleted."
    )


def _assert_owner_identity(
    payload: object,
    *,
    email: str,
    organization_slug: str,
) -> None:
    if not isinstance(payload, dict):
        raise RuntimeError("Corpus returned an invalid owner identity.")
    owner = payload.get("owner")
    organization = payload.get("organization")
    membership = payload.get("membership")
    if (
        payload.get("type") != "owner"
        or not isinstance(owner, dict)
        or owner.get("email") != email
        or not isinstance(organization, dict)
        or organization.get("slug") != organization_slug
        or not isinstance(membership, dict)
        or membership.get("role") != "owner"
    ):
        raise RuntimeError("The temporary owner identity is not authorized.")


def _exact_string_payload(
    payload: object,
    expected_fields: frozenset[str],
    label: str,
) -> dict[str, str]:
    if not isinstance(payload, dict) or set(payload) != expected_fields:
        raise ValueError(
            f"Restart smoke {label} must contain exactly the expected fields."
        )
    if any(not isinstance(value, str) or not value for value in payload.values()):
        raise ValueError(f"Restart smoke {label} values must be non-empty strings.")
    return payload


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"Corpus response is missing a valid {key}.")
    return value


def _read_state(state_file: Path) -> RestartSmokeState:
    try:
        return RestartSmokeState.from_payload(_load_json(state_file))
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        raise RuntimeError(f"Restart smoke state is invalid: {state_file}") from error


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_local_database(database_url: str) -> Path:
    try:
        parsed = make_url(database_url)
    except Exception as error:
        raise RuntimeError("Corpus database URL is invalid.") from error
    database = parsed.database
    if (
        parsed.drivername != "sqlite+aiosqlite"
        or parsed.query
        or not database
        or database == ":memory:"
        or database.casefold().startswith("file:")
        or database.startswith(("\\\\", "//"))
    ):
        raise RuntimeError(
            "Restart smoke owner setup requires the configured absolute local "
            "file-backed sqlite+aiosqlite Corpus database."
        )
    path = Path(database)
    windows_path = PureWindowsPath(database)
    if not path.is_absolute() and not windows_path.is_absolute():
        raise RuntimeError(
            "Restart smoke owner setup requires an absolute local Corpus database path."
        )
    if windows_path.drive.startswith("\\\\"):
        raise RuntimeError("Network Corpus database paths are not allowed.")
    return path


def _require_loopback_http_url(value: str, *, label: str) -> None:
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError as error:
        raise RuntimeError(f"Restart smoke {label} has an invalid port.") from error
    if (
        parsed.scheme != "http"
        or parsed.hostname not in _LOOPBACK_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
        or port is None
    ):
        raise RuntimeError(
            f"Restart smoke {label} must be credential-free HTTP on localhost, "
            "127.0.0.1, or ::1 with an explicit port."
        )


def _wait_for_terminal(client: httpx.Client, request_id: str) -> None:
    with client.stream(
        "GET",
        f"/api/routedeck/conversation/runs/{request_id}/events",
        params={"after": 0},
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if line.startswith("data: "):
                run = json.loads(line.removeprefix("data: "))
                if run["stage"] in {"completed", "interrupted"}:
                    if run["stage"] != "completed":
                        raise RuntimeError(
                            f"Entry run failed before restart smoke: {run}"
                        )
                    return
    raise RuntimeError("Entry run ended without a terminal event.")


if __name__ == "__main__":
    main()
