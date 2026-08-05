from corpus.runtime.agent import should_enter_product_help
from corpus.runtime.prompt import CORPUS_AGENT_PROMPT


def test_only_lounge_home_requires_the_product_help_entry_operation() -> None:
    assert should_enter_product_help("lounge.home") is True
    assert should_enter_product_help("lounge.product_help") is False
    assert should_enter_product_help("lounge.sign_in") is False


def test_runtime_prompt_defers_product_scope_to_active_agent_context() -> None:
    assert "active RouteDeck agent context" in CORPUS_AGENT_PROMPT
    assert "resolved context" in CORPUS_AGENT_PROMPT
    assert "does not\nprovide" in CORPUS_AGENT_PROMPT
    assert "experimental Sources/API path" not in CORPUS_AGENT_PROMPT
    assert "not currently available" not in CORPUS_AGENT_PROMPT
