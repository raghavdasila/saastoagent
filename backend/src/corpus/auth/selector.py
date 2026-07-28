from __future__ import annotations

from dataclasses import dataclass

from fastapi import Request, Response
from routedeck_fastapi.contracts import RouteDeckHttpProblem

from .service import AuthService, SessionUnavailable


@dataclass(frozen=True)
class CorpusSessionCookieSettings:
    auth_name: str
    owner_route_name: str
    guest_name: str
    secure: bool
    path: str = "/"


@dataclass(frozen=True)
class CorpusSessionSelector:
    service: AuthService
    settings: CorpusSessionCookieSettings

    async def selected_session_id(self, request: Request) -> str:
        auth_token = request.cookies.get(self.settings.auth_name)
        owner_handle = request.cookies.get(self.settings.owner_route_name)
        guest_session = request.cookies.get(self.settings.guest_name)
        if auth_token or owner_handle:
            if not auth_token or not owner_handle:
                raise _unavailable()
            try:
                current = await self.service.resolve_browser_session(
                    auth_token=auth_token,
                    owner_route_handle=owner_handle,
                    require_route=True,
                )
            except SessionUnavailable as error:
                raise _unavailable() from error
            if current.route_session_id is None:
                raise _unavailable()
            return current.route_session_id
        if not guest_session or await self.service.is_route_claimed(guest_session):
            raise _unavailable()
        return guest_session

    async def attach_created_session(
        self,
        request: Request,
        response: Response,
        session_id: str,
    ) -> None:
        auth_token = request.cookies.get(self.settings.auth_name)
        owner_handle = request.cookies.get(self.settings.owner_route_name)
        if auth_token and owner_handle:
            try:
                await self.service.replace_browser_route(
                    auth_token=auth_token,
                    owner_route_handle=owner_handle,
                    replacement_route_session_id=session_id,
                )
            except SessionUnavailable:
                pass
            else:
                response.delete_cookie(
                    self.settings.guest_name,
                    path=self.settings.path,
                    secure=self.settings.secure,
                    httponly=True,
                    samesite="lax",
                )
                return
        for name in (self.settings.auth_name, self.settings.owner_route_name):
            response.delete_cookie(
                name,
                path=self.settings.path,
                secure=self.settings.secure,
                httponly=True,
                samesite="lax",
            )
        response.set_cookie(
            key=self.settings.guest_name,
            value=session_id,
            httponly=True,
            secure=self.settings.secure,
            samesite="lax",
            path=self.settings.path,
        )


def _unavailable() -> RouteDeckHttpProblem:
    return RouteDeckHttpProblem(
        404,
        "session_not_found",
        "The selected session is unavailable.",
    )


__all__ = ["CorpusSessionCookieSettings", "CorpusSessionSelector"]
