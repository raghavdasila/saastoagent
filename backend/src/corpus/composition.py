"""Select product features; RouteDeck owns compilation and validation."""

from routedeck_core.app import Application, CompiledApplication, compile_app

from .features.lounge.feature import LOUNGE_FEATURE, LOUNGE_NODE
from .features.workspace.feature import WORKSPACE_FEATURE
from .features.sources.feature import SOURCES_FEATURE


CORPUS_APP = Application(
    name="corpus",
    entry_node=LOUNGE_NODE.ref,
    features=(LOUNGE_FEATURE, WORKSPACE_FEATURE, SOURCES_FEATURE),
)


def compile_corpus_app() -> CompiledApplication:
    return compile_app(CORPUS_APP)


__all__ = ["CORPUS_APP", "compile_corpus_app"]
