from __future__ import annotations

import json
import os
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import delete, func, select

from corpus.persistence import CorpusDatabase
from corpus.persistence.migrations import upgrade_database
from corpus.auth.models import (
    CorpusConversation,
    Membership,
    MembershipRole,
    Organization,
    User,
)
from corpus.auth.security import hash_opaque_token
from corpus.auth.service import AuthService, SessionUnavailable
from scripts.smoke_restart_recovery import (
    RestartSmokeState,
    StateReservation,
    TemporaryConversation,
    TemporaryOwner,
    _create_temporary_owner,
    _delete_temporary_owner,
    _load_temporary_conversation,
    _read_state,
    _require_local_database,
    _require_loopback_http_url,
    main as legacy_restart_smoke_main,
)
from scripts.smoke_restart_recovery_isolated import (
    create_isolated_runtime,
    remove_isolated_runtime,
)


_REVISION = "0015_builder_retry_attempts"


def _owner() -> TemporaryOwner:
    access_token = "temporary-access-token"
    return TemporaryOwner(
        access_token=access_token,
        access_token_hash=hash_opaque_token(access_token),
        access_token_id=uuid4(),
        auth_session_id=uuid4(),
        refresh_token_hash=hash_opaque_token("temporary-refresh-token"),
        owner_user_id=uuid4(),
        organization_id=uuid4(),
        membership_id=uuid4(),
        email="restart-smoke-owner@example.com",
        organization_slug="restart-smoke-owner",
    )


def _state() -> RestartSmokeState:
    owner = _owner()
    return RestartSmokeState(
        reservation_id=uuid4().hex,
        owner=owner,
        conversation=TemporaryConversation(
            row_id=uuid4(),
            public_id="public-conversation",
            route_session_id="internal-route-session",
            owner_user_id=owner.owner_user_id,
        ),
        request_id="restart-request",
    )


def test_restart_state_round_trip_is_exact_and_excludes_refresh_credentials(
    tmp_path: Path,
) -> None:
    state_file = tmp_path / "restart.json"
    expected = _state()
    reservation = StateReservation.acquire(state_file)

    reservation.finalize(replace(expected, reservation_id=reservation.reservation_id))

    assert _read_state(state_file) == replace(
        expected,
        reservation_id=reservation.reservation_id,
    )
    payload = json.loads(state_file.read_text(encoding="utf-8"))
    assert set(payload) == {
        "status",
        "reservation_id",
        "owner",
        "conversation",
        "request_id",
    }
    assert isinstance(payload["owner"], dict)
    assert "refresh_token" not in payload["owner"]


def test_restart_state_rejects_unexpected_fields_and_token_hash_mismatch() -> None:
    payload = _state().to_payload()
    payload["password"] = "must-not-be-persisted"
    with pytest.raises(ValueError, match="exactly"):
        RestartSmokeState.from_payload(payload)

    payload = _state().to_payload()
    assert isinstance(payload["owner"], dict)
    payload["owner"]["access_token_hash"] = "0" * 64
    with pytest.raises(ValueError, match="token hash"):
        RestartSmokeState.from_payload(payload)


@pytest.mark.parametrize(
    "database_url",
    [
        "sqlite+aiosqlite:///relative.sqlite3",
        "sqlite+aiosqlite:///:memory:",
        "sqlite+aiosqlite:///file:relative.sqlite3?uri=true",
        "sqlite+aiosqlite://///server/share/auth.sqlite3",
        r"sqlite+aiosqlite:///\\server\share\auth.sqlite3",
        "sqlite:///D:/tmp/auth.sqlite3",
        "postgresql+asyncpg://localhost/corpus",
    ],
)
def test_restart_owner_setup_rejects_nonlocal_or_nonconfigured_shapes(
    database_url: str,
) -> None:
    with pytest.raises(RuntimeError):
        _require_local_database(database_url)


def test_restart_owner_setup_accepts_absolute_local_file_sqlite() -> None:
    path = _require_local_database("sqlite+aiosqlite:///D:/tmp/corpus.sqlite3")
    assert path == Path("D:/tmp/corpus.sqlite3")


@pytest.mark.parametrize(
    "value",
    [
        "https://127.0.0.1:8099",
        "http://127.0.0.2:8099",
        "http://example.com:8099",
        "http://user:secret@127.0.0.1:8099",
        "http://127.0.0.1:8099/api",
        "http://127.0.0.1:8099?token=secret",
        "http://127.0.0.1",
    ],
)
def test_restart_smoke_rejects_nonloopback_or_credentialed_urls(value: str) -> None:
    with pytest.raises(RuntimeError):
        _require_loopback_http_url(value, label="test URL")


@pytest.mark.parametrize(
    "value",
    [
        "http://localhost:8099",
        "http://127.0.0.1:8099/",
        "http://[::1]:8099",
    ],
)
def test_restart_smoke_accepts_explicit_loopback_http_urls(value: str) -> None:
    _require_loopback_http_url(value, label="test URL")


def test_direct_restart_smoke_execution_is_disabled() -> None:
    with pytest.raises(SystemExit, match="cannot own the RouteDeck database"):
        legacy_restart_smoke_main()


def test_isolated_runtime_owns_both_databases_and_does_not_mutate_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_corpus = "sqlite+aiosqlite:///D:/normal/corpus.sqlite3"
    original_routedeck = "sqlite+pysqlite:///D:/normal/routedeck.sqlite"
    monkeypatch.setenv("CORPUS_DATABASE_URL", original_corpus)
    monkeypatch.setenv("ROUTEDECK_DATABASE_URL", original_routedeck)

    runtime = create_isolated_runtime()
    try:
        assert runtime.directory.parent == Path(tempfile.gettempdir()).resolve()
        assert str(runtime.directory).replace("\\", "/") in runtime.database_url
        assert (
            str(runtime.directory).replace("\\", "/") in runtime.routedeck_database_url
        )
        assert runtime.environment["CORPUS_DATABASE_URL"] != original_corpus
        assert runtime.environment["ROUTEDECK_DATABASE_URL"] != original_routedeck
        assert os.environ["CORPUS_DATABASE_URL"] == original_corpus
        assert os.environ["ROUTEDECK_DATABASE_URL"] == original_routedeck
    finally:
        remove_isolated_runtime(runtime)
    assert not runtime.directory.exists()


def test_isolated_runtime_cleanup_refuses_unowned_directory(tmp_path: Path) -> None:
    runtime = create_isolated_runtime()
    unsafe = replace(runtime, directory=tmp_path)
    try:
        with pytest.raises(RuntimeError, match="unowned"):
            remove_isolated_runtime(unsafe)
    finally:
        remove_isolated_runtime(runtime)


def test_state_path_reservation_is_atomic_and_exclusive(tmp_path: Path) -> None:
    state_file = tmp_path / "restart.json"

    def acquire():
        return StateReservation.acquire(state_file)

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = [
            future for future in (executor.submit(acquire), executor.submit(acquire))
        ]
        results: list[StateReservation | BaseException] = []
        for future in outcomes:
            try:
                results.append(future.result())
            except BaseException as error:
                results.append(error)

    reservations = [item for item in results if isinstance(item, StateReservation)]
    failures = [item for item in results if isinstance(item, RuntimeError)]
    assert len(reservations) == 1
    assert len(failures) == 1
    reservations[0].abort_after_cleanup()
    assert not state_file.exists()


async def _create_owner_and_conversation(
    database_url: str,
    *,
    route_session_id: str,
) -> tuple[TemporaryOwner, TemporaryConversation]:
    owner = await _create_temporary_owner(
        database_url,
        migration_revision=_REVISION,
        access_lifetime=timedelta(minutes=15),
        absolute_lifetime=timedelta(days=30),
    )
    database = CorpusDatabase(database_url)
    service = AuthService(database)
    try:
        conversation = await service.reserve_conversation(
            access_token=owner.access_token,
            route_session_id=route_session_id,
        )
    finally:
        await database.close()
    return owner, await _load_temporary_conversation(
        database_url,
        migration_revision=_REVISION,
        owner=owner,
        public_id=conversation.public_id,
    )


@pytest.mark.asyncio
async def test_exact_cleanup_preserves_decoy_user_org_and_conversation(
    tmp_path: Path,
) -> None:
    database_url = (
        f"sqlite+aiosqlite:///{(tmp_path / 'corpus.sqlite3').as_posix()}"
    )
    await upgrade_database(database_url)
    decoy_owner, decoy_conversation = await _create_owner_and_conversation(
        database_url,
        route_session_id="decoy-route-session",
    )
    target_owner, target_conversation = await _create_owner_and_conversation(
        database_url,
        route_session_id="target-route-session",
    )

    await _delete_temporary_owner(
        database_url,
        migration_revision=_REVISION,
        owner=target_owner,
        conversation=target_conversation,
    )

    database = CorpusDatabase(database_url)
    service = AuthService(database)
    try:
        principal = await service.resolve_access_token(decoy_owner.access_token)
        assert principal.user_id == decoy_owner.owner_user_id
        async with database.session() as session:
            assert await session.get(User, decoy_owner.owner_user_id) is not None
            assert (
                await session.get(Organization, decoy_owner.organization_id) is not None
            )
            retained = await session.get(CorpusConversation, decoy_conversation.row_id)
            assert retained is not None
            assert retained.public_id == decoy_conversation.public_id
            assert await session.get(User, target_owner.owner_user_id) is None
    finally:
        await database.close()

    await _delete_temporary_owner(
        database_url,
        migration_revision=_REVISION,
        owner=decoy_owner,
        conversation=decoy_conversation,
    )


@pytest.mark.asyncio
async def test_crafted_state_and_shared_membership_fail_without_deleting_anything(
    tmp_path: Path,
) -> None:
    database_url = (
        f"sqlite+aiosqlite:///{(tmp_path / 'corpus.sqlite3').as_posix()}"
    )
    await upgrade_database(database_url)
    target_owner, target_conversation = await _create_owner_and_conversation(
        database_url,
        route_session_id="target-route-session",
    )
    decoy_owner, decoy_conversation = await _create_owner_and_conversation(
        database_url,
        route_session_id="decoy-route-session",
    )
    state_file = tmp_path / "restart-state.json"
    state_file.write_text("retained-on-cleanup-mismatch", encoding="utf-8")

    crafted = replace(target_owner, email=decoy_owner.email)
    with pytest.raises(RuntimeError, match="user"):
        await _delete_temporary_owner(
            database_url,
            migration_revision=_REVISION,
            owner=crafted,
            conversation=target_conversation,
        )
    assert state_file.exists()

    database = CorpusDatabase(database_url)
    try:
        async with database.session() as session:
            async with session.begin():
                unsafe_membership = Membership(
                    user_id=decoy_owner.owner_user_id,
                    organization_id=target_owner.organization_id,
                    role=MembershipRole.MEMBER,
                    created_at=datetime.now(UTC),
                )
                session.add(unsafe_membership)
                await session.flush()
                unsafe_membership_id = unsafe_membership.id
    finally:
        await database.close()

    with pytest.raises(RuntimeError, match="exclusive owner membership"):
        await _delete_temporary_owner(
            database_url,
            migration_revision=_REVISION,
            owner=target_owner,
            conversation=target_conversation,
        )

    database = CorpusDatabase(database_url)
    try:
        async with database.session() as session:
            assert await session.get(User, target_owner.owner_user_id) is not None
            assert await session.get(User, decoy_owner.owner_user_id) is not None
            assert (
                await session.get(Organization, target_owner.organization_id)
                is not None
            )
            assert (
                await session.get(CorpusConversation, target_conversation.row_id)
                is not None
            )
            await session.execute(
                delete(Membership).where(Membership.id == unsafe_membership_id)
            )
            await session.commit()
    finally:
        await database.close()

    await _delete_temporary_owner(
        database_url,
        migration_revision=_REVISION,
        owner=target_owner,
        conversation=target_conversation,
    )
    await _delete_temporary_owner(
        database_url,
        migration_revision=_REVISION,
        owner=decoy_owner,
        conversation=decoy_conversation,
    )
    assert state_file.exists()


@pytest.mark.asyncio
async def test_temporary_owner_cleanup_without_conversation_is_exact(
    tmp_path: Path,
) -> None:
    database_url = (
        f"sqlite+aiosqlite:///{(tmp_path / 'corpus.sqlite3').as_posix()}"
    )
    await upgrade_database(database_url)
    owner = await _create_temporary_owner(
        database_url,
        migration_revision=_REVISION,
        access_lifetime=timedelta(minutes=15),
        absolute_lifetime=timedelta(days=30),
    )

    await _delete_temporary_owner(
        database_url,
        migration_revision=_REVISION,
        owner=owner,
        conversation=None,
    )

    database = CorpusDatabase(database_url)
    service = AuthService(database)
    try:
        with pytest.raises(SessionUnavailable):
            await service.resolve_access_token(owner.access_token)
        async with database.session() as session:
            assert await session.scalar(select(func.count()).select_from(User)) == 0
            assert (
                await session.scalar(select(func.count()).select_from(Organization))
                == 0
            )
    finally:
        await database.close()
