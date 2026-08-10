from __future__ import annotations

import asyncio
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest
import pytest_asyncio
from cryptography.fernet import Fernet
from routedeck_sqlalchemy import open_sqlalchemy_routedeck_runtime
from sqlalchemy import func, select

from corpus.bindings import bind_corpus_app
from corpus.composition import compile_corpus_app
from corpus.persistence import CorpusDatabase
from corpus.auth.models import AccessToken, AuthSession, CorpusConversation, User
from corpus.auth.service import (
    AuthService,
    ConversationUnavailable,
    IssuedOwnerSession,
    SessionUnavailable,
)
from corpus.session import (
    create_guest_session,
    create_principal_session_factory,
    initialize_guest_session,
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
    assert await service.route_principal_kind("internal-route-1") == "owner"
    assert await service.route_principal_kind("internal-route-2") == "owner"

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
async def test_registration_adoption_commits_across_database_close_and_reopen(
    tmp_path: Path,
) -> None:
    database_url = (
        f"sqlite+aiosqlite:///{(tmp_path / 'adoption.sqlite3').as_posix()}"
    )
    database = CorpusDatabase(database_url)
    await database.create_schema_for_tests()
    service = AuthService(database)
    anonymous = await service.issue_anonymous()
    conversation = await service.reserve_conversation(
        access_token=anonymous.access_token,
        route_session_id="durable-owner-route",
    )
    owner = await service.register(
        email="durable-owner@example.com",
        password="a sufficiently private password",
        display_name="Durable Owner",
        anonymous_access_token=anonymous.access_token,
        conversation_id=conversation.public_id,
        route_session_id=conversation.route_session_id,
    )
    owner_user_id = (
        await service.list_conversations(owner.tokens.access_token)
    )[0].owner_user_id
    await database.close()

    reopened_database = CorpusDatabase(database_url)
    reopened_service = AuthService(reopened_database)
    try:
        conversations = await reopened_service.list_conversations(
            owner.tokens.access_token
        )
        assert [item.public_id for item in conversations] == [
            conversation.public_id
        ]
        assert conversations[0].owner_user_id == owner_user_id
        with pytest.raises(SessionUnavailable):
            await reopened_service.resolve_access_token(anonymous.access_token)
    finally:
        await reopened_database.close()


@pytest.mark.asyncio
async def test_adopted_conversation_and_route_session_reopen_together(
    tmp_path: Path,
) -> None:
    auth_url = f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    route_url = f"sqlite+pysqlite:///{(tmp_path / 'route.sqlite3').as_posix()}"
    encryption_key = Fernet.generate_key().decode("ascii")
    database = CorpusDatabase(auth_url)
    await database.create_schema_for_tests()
    service = AuthService(database)

    async def open_runtime(current_service: AuthService, instance_id: str):
        compiled = compile_corpus_app()
        return await open_sqlalchemy_routedeck_runtime(
            compiled_app=compiled,
            application_factory=lambda resources: bind_corpus_app(
                compiled,
                current_service,
                auth_service=current_service,
                auth_limiter=object(),
                auth_mail=object(),
                auth_settings=SimpleNamespace(
                    public_frontend_url="http://127.0.0.1:5199"
                ),
                private_form_store=resources.store,
                private_form_codec=resources.codec,
                credential_transition=object(),
                    agent_service=object(),
                    designer_service=object(),
                    builder_service=object(),
                    sandbox_service=object(),
                    evaluation_service=object(),
                    channel_service=object(),
                    deployment_service=object(),
                    operations_service=object(),
                    workspace_service=object(),
                source_service=object(),
                source_graph_presenter=object(),
                source_connection_service=object(),
                source_contract_revision_service=object(),
                source_connection_check_service=object(),
                source_operation_curation_service=object(),
            ),
            session_factory=create_principal_session_factory(
                current_service,
                resume_ttl=timedelta(hours=1),
            ),
            session_initializer=initialize_guest_session,
            public_key_validator_factory=lambda _session: None,
            agent_driver_factory=None,
            database_url=route_url,
            encryption_key=encryption_key,
            instance_id=instance_id,
            review_ttl=timedelta(minutes=15),
            resume_capability_ttl=timedelta(hours=1),
            worker_count=1,
        )

    anonymous = await service.issue_anonymous()
    conversation = await service.reserve_conversation(
        access_token=anonymous.access_token,
        route_session_id="durable-route-session",
    )
    runtime = await open_runtime(service, "adoption-first")
    await runtime.services.store.create(
        create_guest_session(
            compile_corpus_app(),
            conversation.route_session_id,
        )
    )
    owner = await service.register(
        email="route-durable-owner@example.com",
        password="a sufficiently private password",
        display_name="Route Durable Owner",
        anonymous_access_token=anonymous.access_token,
        conversation_id=conversation.public_id,
        route_session_id=conversation.route_session_id,
    )
    before = await runtime.services.store.load(conversation.route_session_id)
    await runtime.close()
    await database.close()

    reopened_database = CorpusDatabase(auth_url)
    reopened_service = AuthService(reopened_database)
    reopened_runtime = await open_runtime(reopened_service, "adoption-reopened")
    try:
        owner_conversations = await reopened_service.list_conversations(
            owner.tokens.access_token
        )
        assert [item.public_id for item in owner_conversations] == [
            conversation.public_id
        ]
        after = await reopened_runtime.services.store.load(
            conversation.route_session_id
        )
        assert after.state.session_id == before.state.session_id
        assert after.state.navgraph_version == before.state.navgraph_version
    finally:
        await reopened_runtime.close()
        await reopened_database.close()


@pytest.mark.asyncio
async def test_route_principal_kind_preserves_anonymous_and_missing_distinction(
    auth_service,
) -> None:
    _, service = auth_service
    anonymous = await service.issue_anonymous()
    await service.reserve_conversation(
        access_token=anonymous.access_token,
        route_session_id="anonymous-route",
    )

    assert await service.route_principal_kind("anonymous-route") == "anonymous"
    with pytest.raises(SessionUnavailable):
        await service.route_principal_kind("missing-route")


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
