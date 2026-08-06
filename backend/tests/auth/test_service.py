from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from corpus.persistence import CorpusDatabase
from corpus.auth.models import AccessToken, AuthSession, CorpusConversation, User
from corpus.auth.service import (
    AuthService,
    ConversationUnavailable,
    IssuedOwnerSession,
    SessionUnavailable,
)


@pytest_asyncio.fixture
async def auth_service(tmp_path: Path):
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    await database.create_schema_for_tests()
    service = AuthService(database)
    try:
        yield database, service
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_opaque_anonymous_tokens_rotate_atomically_and_store_only_hashes(
    auth_service,
) -> None:
    database, service = auth_service
    issued = await service.issue_anonymous()

    current = await service.resolve_access_token(issued.access_token)
    assert current.kind == "anonymous"
    rotated = await service.refresh(issued.refresh_token)
    assert rotated.refresh_token != issued.refresh_token
    assert rotated.access_token != issued.access_token
    with pytest.raises(SessionUnavailable):
        await service.refresh(issued.refresh_token)

    async with database.session() as session:
        auth = (await session.scalars(select(AuthSession))).one()
        access = (await session.scalars(select(AccessToken))).all()
        assert auth.refresh_token_hash not in {
            issued.refresh_token,
            rotated.refresh_token,
        }
        assert all(
            row.token_hash not in {issued.access_token, rotated.access_token}
            for row in access
        )


@pytest.mark.asyncio
async def test_registration_adopts_selected_anonymous_conversation(
    auth_service,
) -> None:
    database, service = auth_service
    anonymous = await service.issue_anonymous()
    conversation = await service.reserve_conversation(
        access_token=anonymous.access_token,
        route_session_id="internal-route-1",
    )

    issued = await service.register(
        email=" Owner@Example.com ",
        password="a sufficiently private password",
        display_name="Ada Owner",
        anonymous_access_token=anonymous.access_token,
        conversation_id=conversation.public_id,
        route_session_id="internal-route-1",
    )

    assert issued.view.owner.email == "owner@example.com"
    assert issued.conversation_id == conversation.public_id
    assert issued.tokens.principal.type == "owner"
    with pytest.raises(SessionUnavailable):
        await service.resolve_access_token(anonymous.access_token)
    owner_conversations = await service.list_conversations(
        issued.tokens.access_token
    )
    assert [item.public_id for item in owner_conversations] == [
        conversation.public_id
    ]
    assert owner_conversations[0].route_session_id == "internal-route-1"
    second = await service.reserve_conversation(
        access_token=issued.tokens.access_token,
        route_session_id="internal-route-2",
    )
    assert second.owner_user_id == owner_conversations[0].owner_user_id
    assert len(
        await service.list_conversations(issued.tokens.access_token)
    ) == 2

    async with database.session() as session:
        assert await session.scalar(select(func.count()).select_from(User)) == 1
        row = await session.scalar(
            select(CorpusConversation).where(
                CorpusConversation.public_id == conversation.public_id
            )
        )
        assert row is not None
        assert row.anonymous_session_id is None
        assert row.owner_user_id is not None


@pytest.mark.asyncio
async def test_sign_out_revokes_owner_token_pair(
    auth_service,
) -> None:
    _, service = auth_service
    anonymous = await service.issue_anonymous()
    conversation = await service.reserve_conversation(
        access_token=anonymous.access_token,
        route_session_id="internal-route-1",
    )
    owner = await service.register(
        email="owner@example.com",
        password="a sufficiently private password",
        display_name=None,
        anonymous_access_token=anonymous.access_token,
        conversation_id=conversation.public_id,
        route_session_id="internal-route-1",
    )

    await service.sign_out(owner.tokens.access_token)
    with pytest.raises(SessionUnavailable):
        await service.resolve_access_token(owner.tokens.access_token)
    with pytest.raises(SessionUnavailable):
        await service.refresh(owner.tokens.refresh_token)


@pytest.mark.asyncio
async def test_password_reset_revokes_every_owner_token_pair(auth_service) -> None:
    _, service = auth_service
    anonymous = await service.issue_anonymous()
    conversation = await service.reserve_conversation(
        access_token=anonymous.access_token,
        route_session_id="internal-route-reset",
    )
    owner = await service.register(
        email="reset-owner@example.com",
        password="a sufficiently private password",
        display_name=None,
        anonymous_access_token=anonymous.access_token,
        conversation_id=conversation.public_id,
        route_session_id="internal-route-reset",
    )
    reset = await service.request_password_reset("reset-owner@example.com")
    assert reset is not None
    await service.confirm_password_reset(
        reset.token,
        "a different sufficiently private password",
    )
    with pytest.raises(SessionUnavailable):
        await service.resolve_access_token(owner.tokens.access_token)
    with pytest.raises(SessionUnavailable):
        await service.refresh(owner.tokens.refresh_token)


@pytest.mark.asyncio
async def test_concurrent_sign_in_can_claim_anonymous_conversation_once(
    auth_service,
) -> None:
    database, service = auth_service
    registration_principal = await service.issue_anonymous()
    registration_conversation = await service.reserve_conversation(
        access_token=registration_principal.access_token,
        route_session_id="registration-route",
    )
    await service.register(
        email="owner@example.com",
        password="a sufficiently private password",
        display_name=None,
        anonymous_access_token=registration_principal.access_token,
        conversation_id=registration_conversation.public_id,
        route_session_id="registration-route",
    )
    anonymous = await service.issue_anonymous()
    conversation = await service.reserve_conversation(
        access_token=anonymous.access_token,
        route_session_id="concurrent-route",
    )

    async def sign_in():
        return await service.sign_in(
            email="owner@example.com",
            password="a sufficiently private password",
            anonymous_access_token=anonymous.access_token,
            conversation_id=conversation.public_id,
            route_session_id="concurrent-route",
        )

    results = await asyncio.gather(sign_in(), sign_in(), return_exceptions=True)
    assert sum(isinstance(result, IssuedOwnerSession) for result in results) == 1
    assert sum(
        isinstance(result, (ConversationUnavailable, SessionUnavailable))
        for result in results
    ) == 1

    async with database.session() as session:
        claimed = await session.scalar(
            select(CorpusConversation).where(
                CorpusConversation.public_id == conversation.public_id
            )
        )
        assert claimed is not None
        assert claimed.anonymous_session_id is None
        assert claimed.owner_user_id is not None
