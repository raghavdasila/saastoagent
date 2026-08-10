import secrets
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Literal, Protocol

from routedeck_core.app import CompiledApplication
from routedeck_core.contracts.session import (
    Location,
    PrivateSessionState,
    PublicSessionState,
    PublicSurfaceState,
    ResumeCapabilityBinding,
    RouteDeckSession,
    SessionSnapshot,
)
from routedeck_core.contracts.projection import ClassifiedValue, DataClassification
from routedeck_core.runtime import RouteDeckRuntimeServices
from routedeck_core.state.session import create_session
from routedeck_core.state.surfaces import surface_state_for_node

from corpus.features.lounge.declarations import (
    REGISTER_FORM_ID,
    RESET_CONFIRM_FORM_ID,
    RESET_REQUEST_FORM_ID,
    SIGN_IN_FORM_ID,
    VERIFY_EMAIL_FORM_ID,
)
from corpus.features.sources.declarations import API_CONNECTION_FORM_ID


_PRIVATE_FORM_HANDLES = (
    ("lounge.register", REGISTER_FORM_ID),
    ("lounge.sign_in", SIGN_IN_FORM_ID),
    ("lounge.forgot_password", RESET_REQUEST_FORM_ID),
    ("lounge.reset_password", RESET_CONFIRM_FORM_ID),
    ("lounge.verify_email", VERIFY_EMAIL_FORM_ID),
    ("sources.home", API_CONNECTION_FORM_ID),
)


class RoutePrincipalResolver(Protocol):
    async def route_principal_kind(
        self,
        route_session_id: str,
    ) -> Literal["anonymous", "owner"]: ...


def create_guest_session(
    app: CompiledApplication,
    session_id: str,
) -> RouteDeckSession:
    return create_session(
        app=app,
        session_id=session_id,
        private_state=PrivateSessionState(),
        public_state=PublicSessionState(
            surface_state=tuple(
                PublicSurfaceState(
                    surface_id=surface_id,
                    values=(
                        ClassifiedValue(
                            name="form_handle",
                            value=form_id,
                            classification=DataClassification.PUBLIC,
                        ),
                    ),
                )
                for surface_id, form_id in _PRIVATE_FORM_HANDLES
            )
        ),
    )


def create_owner_session(
    app: CompiledApplication,
    session_id: str,
    *,
    now: datetime,
    resume_handle: str,
    resume_ttl: timedelta,
) -> RouteDeckSession:
    guest = create_guest_session(app, session_id)
    workspace = app.require_node("workspace.home")
    public_state = guest.public_state.model_copy(
        update={
            "surface_state": surface_state_for_node(
                app,
                guest.public_state.surface_state,
                workspace,
            )
        }
    )
    return guest.model_copy(
        update={
            "current": Location(node_id=workspace.id, entry_id=1),
            "private_state": guest.private_state.model_copy(
                update={
                    "resume_capabilities": (
                        ResumeCapabilityBinding(
                            handle=resume_handle,
                            session_id=session_id,
                            node_id=workspace.id,
                            expires_at=now + resume_ttl,
                        ),
                    )
                }
            ),
            "public_state": public_state,
        }
    )


def create_principal_session_factory(
    resolver: RoutePrincipalResolver,
    *,
    now_factory: Callable[[], datetime] | None = None,
    resume_ttl: timedelta = timedelta(minutes=10),
    handle_factory: Callable[[], str] | None = None,
):
    resolved_now_factory = now_factory or (lambda: datetime.now(UTC))
    resolved_handle_factory = handle_factory or (lambda: secrets.token_urlsafe(24))

    async def create_principal_session(
        app: CompiledApplication,
        session_id: str,
    ) -> RouteDeckSession:
        principal = await resolver.route_principal_kind(session_id)
        if principal == "owner":
            return create_owner_session(
                app,
                session_id,
                now=resolved_now_factory(),
                resume_handle=resolved_handle_factory(),
                resume_ttl=resume_ttl,
            )
        if principal == "anonymous":
            return create_guest_session(app, session_id)
        raise RuntimeError("The route session principal is invalid.")

    return create_principal_session


async def initialize_guest_session(
    services: RouteDeckRuntimeServices,
    created: SessionSnapshot,
) -> SessionSnapshot:
    del services
    return created


__all__ = [
    "RoutePrincipalResolver",
    "create_guest_session",
    "create_owner_session",
    "create_principal_session_factory",
    "initialize_guest_session",
]
