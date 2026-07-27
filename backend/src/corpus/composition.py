"""Select product features; RouteDeck owns compilation and validation."""

from routedeck_core.app import Application, CompiledApplication, compile_app

from .features.workspace.feature import LOUNGE_NODE, WORKSPACE_FEATURE
from .features.sources.feature import SOURCES_FEATURE


CORPUS_APP = Application(
    name="corpus",
    entry_node=LOUNGE_NODE.ref,
    features=(WORKSPACE_FEATURE, SOURCES_FEATURE),
)


def compile_corpus_app() -> CompiledApplication:
    return compile_app(CORPUS_APP)


__all__ = ["CORPUS_APP", "compile_corpus_app"]
