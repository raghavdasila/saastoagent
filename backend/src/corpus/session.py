from routedeck_core.app import CompiledApplication
from routedeck_core.contracts.session import (
    PrivateSessionState,
    RouteDeckSession,
    SessionSnapshot,
)
from routedeck_core.runtime import RouteDeckRuntimeServices
from routedeck_core.state.session import create_session


def create_guest_session(
    app: CompiledApplication,
    session_id: str,
) -> RouteDeckSession:
    return create_session(
        app=app,
        session_id=session_id,
        private_state=PrivateSessionState(),
    )


async def initialize_guest_session(
    services: RouteDeckRuntimeServices,
    created: SessionSnapshot,
) -> SessionSnapshot:
    del services
    return created


__all__ = ["create_guest_session", "initialize_guest_session"]
