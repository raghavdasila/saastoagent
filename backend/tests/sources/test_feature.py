from __future__ import annotations

from routedeck_core.contracts.navigation import DeepLinkPolicy

from corpus.composition import compile_corpus_app


def test_sources_is_a_generic_session_bound_node_with_an_api_debug_surface() -> None:
    contract = compile_corpus_app().frontend_contract
    node = contract.nodes["sources.home"]

    assert node.title == "Sources"
    assert node.route_template == "/sources"
    assert node.deep_link_policy == DeepLinkPolicy.SESSION_BOUND.value
    assert node.surfaces.active == "sources.debug"
    assert contract.surfaces["sources.debug"].component == "sources.debug"

