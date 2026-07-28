from __future__ import annotations

from pathlib import Path
from http.cookies import SimpleCookie

import pytest
from routedeck_fastapi.contracts import RouteDeckHttpProblem
from starlette.responses import JSONResponse
from starlette.requests import Request

from corpus.auth.database import AuthDatabase
from corpus.auth.selector import CorpusSessionCookieSettings, CorpusSessionSelector
from corpus.auth.service import AuthService, InvalidAuthToken, SessionUnavailable


def _request(cookies: dict[str, str]) -> Request:
    cookie = "; ".join(f"{name}={value}" for name, value in cookies.items())
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/api/routedeck/session",
            "headers": [(b"cookie", cookie.encode("ascii"))],
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 1234),
            "query_string": b"",
        }
    )


@pytest.mark.asyncio
async def test_two_owners_cannot_cross_select_route_sessions(tmp_path: Path) -> None:
    database = AuthDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    await database.create_schema_for_tests()
    service = AuthService(database)
    selector = CorpusSessionSelector(
        service,
        CorpusSessionCookieSettings(
            auth_name="corpus_auth",
            owner_route_name="corpus_owner_route",
            guest_name="corpus_guest",
            secure=False,
        ),
    )
    try:
        first = await service.register(
            email="first@example.com",
            password="first sufficiently long password",
            display_name="First",
            guest_route_session_id="route-first",
        )
        second = await service.register(
            email="second@example.com",
            password="second sufficiently long password",
            display_name="Second",
            guest_route_session_id="route-second",
        )

        assert await selector.selected_session_id(
            _request(
                {
                    "corpus_auth": first.auth_token,
                    "corpus_owner_route": first.owner_route_handle,
                }
            )
        ) == "route-first"
        with pytest.raises(RouteDeckHttpProblem) as cross_user:
            await selector.selected_session_id(
                _request(
                    {
                        "corpus_auth": first.auth_token,
                        "corpus_owner_route": second.owner_route_handle,
                    }
                )
            )
        with pytest.raises(RouteDeckHttpProblem) as old_guest:
            await selector.selected_session_id(
                _request({"corpus_guest": "route-first"})
            )
        assert cross_user.value.code == old_guest.value.code == "session_not_found"
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_created_session_replaces_the_current_owner_route(tmp_path: Path) -> None:
    database = AuthDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    await database.create_schema_for_tests()
    service = AuthService(database)
    selector = CorpusSessionSelector(
        service,
        CorpusSessionCookieSettings(
            auth_name="corpus_auth",
            owner_route_name="corpus_owner_route",
            guest_name="corpus_guest",
            secure=False,
        ),
    )
    try:
        issued = await service.register(
            email="owner@example.com",
            password="a sufficiently private password",
            display_name="Owner",
            guest_route_session_id="route-expired",
        )
        request = _request(
            {
                "corpus_auth": issued.auth_token,
                "corpus_owner_route": issued.owner_route_handle,
            }
        )
        response = JSONResponse({"ok": True})

        await selector.attach_created_session(request, response, "route-fresh")

        assert await selector.selected_session_id(request) == "route-fresh"
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_created_session_falls_back_to_guest_when_owner_tokens_are_invalid(
    tmp_path: Path,
) -> None:
    database = AuthDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    await database.create_schema_for_tests()
    selector = CorpusSessionSelector(
        AuthService(database),
        CorpusSessionCookieSettings(
            auth_name="corpus_auth",
            owner_route_name="corpus_owner_route",
            guest_name="corpus_guest",
            secure=False,
        ),
    )
    try:
        response = JSONResponse({"ok": True})
        await selector.attach_created_session(
            _request(
                {
                    "corpus_auth": "invalid-auth",
                    "corpus_owner_route": "invalid-route",
                }
            ),
            response,
            "route-lounge",
        )

        cookies = SimpleCookie()
        for value in response.headers.getlist("set-cookie"):
            cookies.load(value)
        assert cookies["corpus_auth"]["max-age"] == "0"
        assert cookies["corpus_owner_route"]["max-age"] == "0"
        assert cookies["corpus_guest"].value == "route-lounge"
    finally:
        await database.close()


@pytest.mark.asyncio
async def test_verification_is_advisory_and_reset_is_single_use_and_revokes_sessions(
    tmp_path: Path,
) -> None:
    database = AuthDatabase(
        f"sqlite+aiosqlite:///{(tmp_path / 'auth.sqlite3').as_posix()}"
    )
    await database.create_schema_for_tests()
    service = AuthService(database)
    try:
        issued = await service.register(
            email="owner@example.com",
            password="a sufficiently private password",
            display_name=None,
            guest_route_session_id="route-owner",
        )
        current = await service.resolve_browser_session(
            auth_token=issued.auth_token,
            owner_route_handle=issued.owner_route_handle,
            require_route=True,
        )
        assert current.view.owner.is_verified is False

        verification = await service.request_verification(issued.auth_token)
        assert verification is not None
        await service.verify(verification.token)
        verified = await service.resolve_browser_session(
            auth_token=issued.auth_token,
            owner_route_handle=issued.owner_route_handle,
            require_route=True,
        )
        assert verified.view.owner.is_verified is True

        reset = await service.request_password_reset("owner@example.com")
        assert reset is not None
        await service.confirm_password_reset(
            reset.token,
            "a new sufficiently private password",
        )
        with pytest.raises(SessionUnavailable):
            await service.resolve_browser_session(
                auth_token=issued.auth_token,
                owner_route_handle=issued.owner_route_handle,
                require_route=True,
            )
        with pytest.raises(InvalidAuthToken):
            await service.confirm_password_reset(
                reset.token,
                "yet another sufficiently private password",
            )
    finally:
        await database.close()
