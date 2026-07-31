from routedeck_core.app import CompiledApplication
from routedeck_core.contracts.session import (
    PrivateSessionState,
    PublicSessionState,
    PublicSurfaceState,
    RouteDeckSession,
    SessionSnapshot,
)
from routedeck_core.contracts.projection import ClassifiedValue, DataClassification
from routedeck_core.runtime import RouteDeckRuntimeServices
from routedeck_core.state.session import create_session

from corpus.features.lounge.declarations import (
    REGISTER_FORM_ID,
    RESET_CONFIRM_FORM_ID,
    RESET_REQUEST_FORM_ID,
    SIGN_IN_FORM_ID,
    VERIFY_EMAIL_FORM_ID,
)


_LOUNGE_FORM_HANDLES = (
    ("lounge.register", REGISTER_FORM_ID),
    ("lounge.sign_in", SIGN_IN_FORM_ID),
    ("lounge.forgot_password", RESET_REQUEST_FORM_ID),
    ("lounge.reset_password", RESET_CONFIRM_FORM_ID),
    ("lounge.verify_email", VERIFY_EMAIL_FORM_ID),
)


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
                for surface_id, form_id in _LOUNGE_FORM_HANDLES
            )
        ),
    )


async def initialize_guest_session(
    services: RouteDeckRuntimeServices,
    created: SessionSnapshot,
) -> SessionSnapshot:
    del services
    return created


__all__ = ["create_guest_session", "initialize_guest_session"]
