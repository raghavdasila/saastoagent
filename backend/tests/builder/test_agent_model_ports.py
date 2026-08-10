from types import SimpleNamespace

import pytest

from corpus.app.agent_runtime_adapters import (
    CorpusAgentModelPort,
    _message_text,
    _plain_json_object,
    _toolrouter_endpoint_map,
    resolve_openai_model_identity,
)
from corpus.features.agents.declarations import (
    OPEN_AGENT_CHANNELS,
    OPEN_AGENT_EVALUATION,
    OPEN_AGENT_OPERATIONS,
    OPEN_AGENT_SANDBOX,
    RETURN_TO_AGENT_HUB,
)
from corpus.features.channels.declarations import CREATE_CHANNEL
from corpus.features.deployment.declarations import DEPLOY_AGENT
from corpus.features.evaluation.declarations import CREATE_CASE, RUN_CASE
from corpus.features.operations.declarations import PROMOTE_INTERACTION
from corpus.features.sandbox.declarations import START_SANDBOX
from corpus.features.sandbox.schemas import StartSandboxArguments


class PlainJsonModel:
    def invoke(self, messages):
        assert "ToolRouter owns operation selection and clarification" in messages[0][1]
        assert "pass the user's unresolved intent to the router" in messages[0][1]
        assert "Never use answer to ask for an operation choice" in messages[0][1]
        assert "action must be api even when required details are missing" in messages[0][1]
        assert "Allowed operation identities: GetProductsId" in messages[1][1]
        return SimpleNamespace(
            content='{"action":"api","response":"","requests":'
            '[{"call_id":"lookup-1","query":"get product by id"}]}'
        )


def test_ollama_plain_json_decision_is_explicit_and_exact():
    port = CorpusAgentModelPort(PlainJsonModel(), plain_json=True)

    result = port.decide(
        SimpleNamespace(allowed_operations=("GetProductsId",)),
        "get product by id",
    )

    assert result.action == "api"
    assert result.requests[0].call_id == "lookup-1"
    assert result.requests[0].query == "get product by id"


def test_sandbox_start_schema_requires_the_unresolved_user_intent() -> None:
    message = StartSandboxArguments.model_json_schema()["properties"]["message"]

    assert message["description"] == (
        "The user's unresolved request for the built Agent. Preserve its meaning and "
        "ambiguity; do not answer it, add missing details, split it into operations, "
        "select an operation, or invent identifiers."
    )


def test_sandbox_operations_describe_the_owners_natural_private_trial_intent() -> None:
    assert "try or test" in OPEN_AGENT_SANDBOX.description
    assert "private trial" in OPEN_AGENT_SANDBOX.description
    assert "try or test" in START_SANDBOX.description
    assert "private trial" in START_SANDBOX.description


def test_later_feature_operations_describe_ordinary_owner_intents() -> None:
    assert "another selected-agent work area" in RETURN_TO_AGENT_HUB.description
    assert "deployed interaction evidence" in RETURN_TO_AGENT_HUB.description
    assert "keep a private trial" in OPEN_AGENT_EVALUATION.description
    assert "required evaluation case" in CREATE_CASE.description
    assert "check" in RUN_CASE.description.casefold()
    assert "saved evaluation case" in RUN_CASE.description
    assert "set up a hosted address" in OPEN_AGENT_CHANNELS.description
    assert "set up" in CREATE_CHANNEL.description.casefold()
    assert "put or publish" in DEPLOY_AGENT.description.casefold()
    assert "how a completed public request ran" in OPEN_AGENT_OPERATIONS.description.casefold()
    assert "only when the owner explicitly asks" in PROMOTE_INTERACTION.description.casefold()
    assert "future evaluation case" in PROMOTE_INTERACTION.description.casefold()
    assert "never use this operation to inspect" in PROMOTE_INTERACTION.description.casefold()


def test_ollama_plain_json_accepts_the_models_exact_json_fence():
    assert _plain_json_object(
        SimpleNamespace(content='```json\n{"passed":true,"reasons":[]}\n```')
    ) == {"passed": True, "reasons": []}


@pytest.mark.parametrize("content", ["```\n{}\n```", "[]", "not json"])
def test_plain_json_contract_fails_closed(content):
    with pytest.raises((ValueError, TypeError)):
        _plain_json_object(SimpleNamespace(content=content))


def test_public_operation_id_maps_to_one_source_qualified_endpoint(tmp_path):
    graph = tmp_path / "graph"
    graph.mkdir()
    (graph / "semantic_graph.json").write_text(
        '{"nodes":[{"endpoint_id":"medusa_store:GetProductsId",'
        '"facets":{"operation_id":"GetProductsId"}}]}',
        encoding="utf-8",
    )

    assert _toolrouter_endpoint_map(
        tmp_path, ("GetProductsId",)
    ) == {"GetProductsId": "medusa_store:GetProductsId"}


def test_openai_runtime_identity_is_exact_and_model_bound():
    first = resolve_openai_model_identity("gpt-5.6-luna")
    repeated = resolve_openai_model_identity("gpt-5.6-luna")
    other = resolve_openai_model_identity("gpt-5.6-luna-2026-08-08")

    assert first == repeated
    assert first[0] == "openai/gpt-5.6-luna"
    assert len(first[1]) == 64
    assert other[1] != first[1]


def test_standard_langchain_text_blocks_are_accepted_through_message_text():
    response = SimpleNamespace(
        content=[{"type": "text", "text": "Product types are available."}],
        text="Product types are available.",
    )

    assert _message_text(response) == "Product types are available."


def test_non_text_model_response_fails_closed():
    with pytest.raises(RuntimeError, match="agent_model_text_response_required"):
        _message_text(SimpleNamespace(content=[{"type": "image"}]))
