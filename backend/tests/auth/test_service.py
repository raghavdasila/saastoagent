from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from corpus.auth.database import AuthDatabase
from corpus.auth.models import (
    AuthSession,
    Membership,
    Organization,
    OwnerRouteClaim,
    OwnerRouteHandle,
    User,
)
from corpus.auth.service import (
    AuthConflict,
    AuthService,
    InvalidCredentials,
)


@pytest_asyncio.fixture
async def auth_service(tmp_path: Path):
    database = AuthDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    await database.create_schema_for_tests()
    service = AuthService(database)
    try:
        yield database, service
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_registration_atomically_provisions_personal_owner_and_claim(
    auth_service,
) -> None:
    database, service = auth_service

    issued = await service.register(
        email=" Owner@Example.com ",
        password="a sufficiently private password",
        display_name="Ada Owner",
        guest_route_session_id="route-guest-1",
    )

    assert issued.view.owner.email == "owner@example.com"
    assert issued.view.organization.name == "Ada Owner's Workspace"
    assert issued.view.membership.role == "owner"
    assert issued.view.route_session_state == "adopted"
    assert issued.auth_token != issued.owner_route_handle

    async with database.session() as session:
        for model in (
            User,
            Organization,
            Membership,
            AuthSession,
            OwnerRouteClaim,
            OwnerRouteHandle,
        ):
            count = await session.scalar(select(func.count()).select_from(model))
            assert count == 1
        auth_row = (await session.scalars(select(AuthSession))).one()
        handle_row = (await session.scalars(select(OwnerRouteHandle))).one()
        assert auth_row.token_hash != issued.auth_token
        assert handle_row.token_hash != issued.owner_route_handle


@pytest.mark.asyncio
async def test_duplicate_registration_rolls_back_every_provisioning_write(
    auth_service,
) -> None:
    database, service = auth_service
    await service.register(
        email="owner@example.com",
        password="a sufficiently private password",
        display_name=None,
        guest_route_session_id="route-guest-1",
    )

    with pytest.raises(AuthConflict):
        await service.register(
            email="OWNER@example.com",
            password="another sufficiently private password",
            display_name="Other",
            guest_route_session_id="route-guest-2",
        )

    async with database.session() as session:
        assert await session.scalar(select(func.count()).select_from(User)) == 1
        assert (
            await session.scalar(select(func.count()).select_from(Organization))
            == 1
        )
        assert (
            await session.scalar(select(func.count()).select_from(OwnerRouteClaim))
            == 1
        )


@pytest.mark.asyncio
async def test_sign_in_resumes_owner_claim_and_rejects_invalid_password(
    auth_service,
) -> None:
    _, service = auth_service
    registered = await service.register(
        email="owner@example.com",
        password="a sufficiently private password",
        display_name=None,
        guest_route_session_id="route-guest-1",
    )

    resumed = await service.sign_in(
        email="owner@example.com",
        password="a sufficiently private password",
        guest_route_session_id="unclaimed-guest-2",
    )
    assert resumed.view.route_session_state == "resumed"
    assert resumed.route_session_id == registered.route_session_id
    assert resumed.auth_token != registered.auth_token

    with pytest.raises(InvalidCredentials):
        await service.sign_in(
            email="owner@example.com",
            password="wrong password value",
            guest_route_session_id="unclaimed-guest-2",
        )
