"""Select product features; RouteDeck owns compilation and validation."""

from routedeck_core.app import Application, CompiledApplication, compile_app

from .features.agents.contracts import AGENTS_HOME_REF
from .features.agents.feature import create_agents_feature
from .features.lounge.declarations import VERIFICATION_PENDING_REF
from .features.lounge.feature import LOUNGE_NODE, create_lounge_feature
from .features.sources.feature import SOURCES_FEATURE
from .features.sources.declarations import SOURCES_HOME_REF
from .features.workspace.contracts import HOME_REF
from .features.workspace.feature import create_workspace_feature


LOUNGE_FEATURE = create_lounge_feature(HOME_REF)
WORKSPACE_FEATURE = create_workspace_feature(
    agents_home_ref=AGENTS_HOME_REF,
    sources_home_ref=SOURCES_HOME_REF,
    verification_ref=VERIFICATION_PENDING_REF,
)
AGENTS_FEATURE = create_agents_feature(HOME_REF)


CORPUS_APP = Application(
    name="corpus",
    entry_node=LOUNGE_NODE.ref,
    features=(LOUNGE_FEATURE, WORKSPACE_FEATURE, AGENTS_FEATURE, SOURCES_FEATURE),
)


def compile_corpus_app() -> CompiledApplication:
    return compile_app(CORPUS_APP)


__all__ = [
    "AGENTS_FEATURE",
    "CORPUS_APP",
    "LOUNGE_FEATURE",
    "WORKSPACE_FEATURE",
    "compile_corpus_app",
]
