from __future__ import annotations

from routedeck_core.app import Feature
from routedeck_core.contracts.application import Capability, Node
from routedeck_core.contracts.navigation import (
    DeepLinkPolicy,
    NodeKind,
    NodeRef,
    Route,
    Transition,
)
from routedeck_core.contracts.projection import FrozenJsonObject
from routedeck_core.contracts.surfaces import (
    Surface,
    SurfaceAffordance,
    SurfaceLifecycle,
    SurfaceSlots,
)

from .declarations import (
    AUTHENTICATION_COMPLETED,
    EMPTY_OBJECT_SCHEMA,
    FORGOT_PASSWORD_REF,
    HOME_REF,
    LOUNGE_REF,
    OPEN_FORGOT_PASSWORD,
    OPEN_REGISTRATION,
    OPEN_RESET_PASSWORD,
    OPEN_SIGN_IN,
    OPEN_SOURCES,
    OPEN_VERIFY_EMAIL,
    OWNER_CONTEXT_PROVIDER,
    REGISTER_REF,
    RESET_PASSWORD_REF,
    RETURN_TO_LOUNGE,
    SIGN_IN_REF,
    VERIFY_EMAIL_REF,
)


LOUNGE_SURFACE = Surface(
    id="workspace.lounge",
    component="workspace.lounge",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    affordances=(
        SurfaceAffordance(
            id="open_sign_in",
            event="open",
            operation=OPEN_SIGN_IN.ref,
        ),
        SurfaceAffordance(
            id="open_registration",
            event="open",
            operation=OPEN_REGISTRATION.ref,
        ),
    ),
)
SIGN_IN_SURFACE = Surface(
    id="workspace.sign_in",
    component="workspace.sign_in",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    affordances=(
        SurfaceAffordance(
            id="return_to_lounge",
            event="open",
            operation=RETURN_TO_LOUNGE.ref,
        ),
        SurfaceAffordance(
            id="open_forgot_password",
            event="open",
            operation=OPEN_FORGOT_PASSWORD.ref,
        ),
        SurfaceAffordance(
            id="authentication_completed",
            event="submit",
            operation=AUTHENTICATION_COMPLETED.ref,
        ),
    ),
)
REGISTER_SURFACE = Surface(
    id="workspace.register",
    component="workspace.register",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    affordances=(
        SurfaceAffordance(
            id="return_to_lounge",
            event="open",
            operation=RETURN_TO_LOUNGE.ref,
        ),
        SurfaceAffordance(
            id="authentication_completed",
            event="submit",
            operation=AUTHENTICATION_COMPLETED.ref,
        ),
    ),
)
FORGOT_PASSWORD_SURFACE = Surface(
    id="workspace.forgot_password",
    component="workspace.forgot_password",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    affordances=(
        SurfaceAffordance(
            id="return_to_lounge",
            event="open",
            operation=RETURN_TO_LOUNGE.ref,
        ),
    ),
)
RESET_PASSWORD_SURFACE = Surface(
    id="workspace.reset_password",
    component="workspace.reset_password",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    affordances=(
        SurfaceAffordance(
            id="return_to_lounge",
            event="open",
            operation=RETURN_TO_LOUNGE.ref,
        ),
    ),
)
VERIFY_EMAIL_SURFACE = Surface(
    id="workspace.verify_email",
    component="workspace.verify_email",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    affordances=(
        SurfaceAffordance(
            id="return_to_lounge",
            event="open",
            operation=RETURN_TO_LOUNGE.ref,
        ),
    ),
)
HOME_SURFACE = Surface(
    id="workspace.home",
    component="workspace.home",
    lifecycle=SurfaceLifecycle.STABLE,
    public_props_schema=FrozenJsonObject(EMPTY_OBJECT_SCHEMA),
    affordances=(
        SurfaceAffordance(
            id="open_sources",
            event="open",
            operation=OPEN_SOURCES.ref,
        ),
    ),
)
WORKSPACE_CAPABILITY = Capability(
    id="workspace.access",
    title="Navigate the unauthenticated workspace entry journey",
    operations=(
        OPEN_SIGN_IN.ref,
        OPEN_REGISTRATION.ref,
        OPEN_FORGOT_PASSWORD.ref,
        OPEN_RESET_PASSWORD.ref,
        OPEN_VERIFY_EMAIL.ref,
        RETURN_TO_LOUNGE.ref,
        AUTHENTICATION_COMPLETED.ref,
        OPEN_SOURCES.ref,
    ),
    surfaces=(
        LOUNGE_SURFACE.ref,
        SIGN_IN_SURFACE.ref,
        REGISTER_SURFACE.ref,
        FORGOT_PASSWORD_SURFACE.ref,
        RESET_PASSWORD_SURFACE.ref,
        VERIFY_EMAIL_SURFACE.ref,
        HOME_SURFACE.ref,
    ),
)

LOUNGE_NODE = Node(
    id=LOUNGE_REF.id,
    title="Lounge",
    kind=NodeKind.SECTION,
    route=Route(template="/", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    operations=(
        OPEN_SIGN_IN,
        OPEN_REGISTRATION,
        OPEN_RESET_PASSWORD,
        OPEN_VERIFY_EMAIL,
    ),
    outgoing=(
        Transition(
            operation=OPEN_SIGN_IN.ref,
            outcome="opened",
            target=SIGN_IN_REF,
        ),
        Transition(
            operation=OPEN_RESET_PASSWORD.ref,
            outcome="opened",
            target=RESET_PASSWORD_REF,
        ),
        Transition(
            operation=OPEN_VERIFY_EMAIL.ref,
            outcome="opened",
            target=VERIFY_EMAIL_REF,
        ),
        Transition(
            operation=OPEN_REGISTRATION.ref,
            outcome="opened",
            target=REGISTER_REF,
        ),
    ),
    capabilities=(WORKSPACE_CAPABILITY,),
    surfaces=SurfaceSlots(active=LOUNGE_SURFACE),
)
SIGN_IN_NODE = Node(
    id=SIGN_IN_REF.id,
    title="Sign in",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/sign-in", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    context_providers=(OWNER_CONTEXT_PROVIDER,),
    operations=(RETURN_TO_LOUNGE, OPEN_FORGOT_PASSWORD, AUTHENTICATION_COMPLETED),
    outgoing=(
        Transition(
            operation=RETURN_TO_LOUNGE.ref,
            outcome="opened",
            target=LOUNGE_REF,
        ),
        Transition(
            operation=OPEN_FORGOT_PASSWORD.ref,
            outcome="opened",
            target=FORGOT_PASSWORD_REF,
        ),
        Transition(
            operation=AUTHENTICATION_COMPLETED.ref,
            outcome="opened",
            target=HOME_REF,
        ),
    ),
    capabilities=(WORKSPACE_CAPABILITY,),
    surfaces=SurfaceSlots(active=SIGN_IN_SURFACE),
)
REGISTER_NODE = Node(
    id=REGISTER_REF.id,
    title="Create account",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/register", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    context_providers=(OWNER_CONTEXT_PROVIDER,),
    operations=(RETURN_TO_LOUNGE, AUTHENTICATION_COMPLETED),
    outgoing=(
        Transition(
            operation=RETURN_TO_LOUNGE.ref,
            outcome="opened",
            target=LOUNGE_REF,
        ),
        Transition(
            operation=AUTHENTICATION_COMPLETED.ref,
            outcome="opened",
            target=HOME_REF,
        ),
    ),
    capabilities=(WORKSPACE_CAPABILITY,),
    surfaces=SurfaceSlots(active=REGISTER_SURFACE),
)
FORGOT_PASSWORD_NODE = Node(
    id=FORGOT_PASSWORD_REF.id,
    title="Forgot password",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/forgot-password", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    operations=(RETURN_TO_LOUNGE,),
    outgoing=(
        Transition(operation=RETURN_TO_LOUNGE.ref, outcome="opened", target=LOUNGE_REF),
    ),
    capabilities=(WORKSPACE_CAPABILITY,),
    surfaces=SurfaceSlots(active=FORGOT_PASSWORD_SURFACE),
)
RESET_PASSWORD_NODE = Node(
    id=RESET_PASSWORD_REF.id,
    title="Reset password",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/reset-password", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    operations=(RETURN_TO_LOUNGE,),
    outgoing=(
        Transition(operation=RETURN_TO_LOUNGE.ref, outcome="opened", target=LOUNGE_REF),
    ),
    capabilities=(WORKSPACE_CAPABILITY,),
    surfaces=SurfaceSlots(active=RESET_PASSWORD_SURFACE),
)
VERIFY_EMAIL_NODE = Node(
    id=VERIFY_EMAIL_REF.id,
    title="Verify email",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/verify", deep_link_policy=DeepLinkPolicy.SHAREABLE),
    operations=(RETURN_TO_LOUNGE,),
    outgoing=(
        Transition(operation=RETURN_TO_LOUNGE.ref, outcome="opened", target=LOUNGE_REF),
    ),
    capabilities=(WORKSPACE_CAPABILITY,),
    surfaces=SurfaceSlots(active=VERIFY_EMAIL_SURFACE),
)
HOME_NODE = Node(
    id=HOME_REF.id,
    title="Home",
    kind=NodeKind.SECTION,
    parent=LOUNGE_REF,
    route=Route(template="/home", deep_link_policy=DeepLinkPolicy.SESSION_BOUND),
    context_providers=(OWNER_CONTEXT_PROVIDER,),
    operations=(OPEN_SOURCES,),
    outgoing=(
        Transition(
            operation=OPEN_SOURCES.ref,
            outcome="opened",
            target=NodeRef(id="sources.home"),
        ),
    ),
    capabilities=(WORKSPACE_CAPABILITY,),
    surfaces=SurfaceSlots(active=HOME_SURFACE),
)

WORKSPACE_FEATURE = Feature(
    namespace="workspace",
    nodes=(
        LOUNGE_NODE,
        SIGN_IN_NODE,
        REGISTER_NODE,
        FORGOT_PASSWORD_NODE,
        RESET_PASSWORD_NODE,
        VERIFY_EMAIL_NODE,
        HOME_NODE,
    ),
)


__all__ = [
    "LOUNGE_NODE",
    "LOUNGE_SURFACE",
    "REGISTER_NODE",
    "REGISTER_SURFACE",
    "SIGN_IN_NODE",
    "SIGN_IN_SURFACE",
    "WORKSPACE_FEATURE",
    "FORGOT_PASSWORD_NODE",
    "HOME_NODE",
    "RESET_PASSWORD_NODE",
    "VERIFY_EMAIL_NODE",
]
