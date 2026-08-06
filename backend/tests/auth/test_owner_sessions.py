from __future__ import annotations

from pathlib import Path

import pytest
from routedeck_fastapi.contracts import RouteDeckHttpProblem
from starlette.requests import Request

from corpus.persistence import CorpusDatabase
from corpus.auth.selector import CorpusSessionSelector
from corpus.auth.service import AuthService


def _request(access_token: str, conversation_id: str | None) -> Request:
    headers = [(b"authorization", f"Bearer {access_token}".encode("ascii"))]
    if conversation_id is not None:
        headers.append(
            (b"x-corpus-conversation-id", conversation_id.encode("ascii"))
        )
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/routedeck/session",
            "headers": headers,
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 1234),
            "query_string": b"",
        }
    )


@pytest.mark.asyncio
async def test_selector_requires_bearer_and_authorized_public_conversation(
    tmp_path: Path,
) -> None:
    database = CorpusDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    await database.create_schema_for_tests()
    service = AuthService(database)
    selector = CorpusSessionSelector(service)
    try:
        first = await service.issue_anonymous()
        first_conversation = await service.reserve_conversation(
            access_token=first.access_token,
            route_session_id="internal-first",
        )
        second = await service.issue_anonymous()
        second_conversation = await service.reserve_conversation(
            access_token=second.access_token,
            route_session_id="internal-second",
        )

        selected = await selector.selected_session_id(
            _request(first.access_token, first_conversation.public_id)
        )
        assert selected == "internal-first"
        with pytest.raises(RouteDeckHttpProblem) as foreign:
            await selector.selected_session_id(
                _request(first.access_token, second_conversation.public_id)
            )
        assert foreign.value.code == "conversation_not_found"
        with pytest.raises(RouteDeckHttpProblem) as missing:
            await selector.selected_session_id(
                _request(first.access_token, None)
            )
        assert missing.value.code == "conversation_selection_required"
    finally:
        await database.close()
