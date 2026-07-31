from __future__ import annotations

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class RejectDirectRouteDeckSessionCreationMiddleware:
    """Require server-owned conversation creation before RouteDeck session use."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] == "http"
            and scope.get("method") == "POST"
            and scope.get("path") == "/api/routedeck/sessions"
        ):
            response = JSONResponse(
                status_code=409,
                content={
                    "code": "conversation_creation_required",
                    "message": "Create conversations through /api/conversations.",
                },
                headers={"Cache-Control": "no-store"},
            )
            await response(scope, receive, send)
            return
        await self._app(scope, receive, send)


__all__ = ["RejectDirectRouteDeckSessionCreationMiddleware"]
