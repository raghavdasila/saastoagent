from __future__ import annotations

from types import SimpleNamespace

from corpus.integrations.toolrouter.openai_responses import (
    OpenAIResponsesTransport,
)


class _Responses:
    def __init__(self) -> None:
        self.request: dict[str, object] | None = None

    def create(self, **kwargs):
        self.request = kwargs
        return SimpleNamespace(
            output_text='{"candidate_id":"candidate-1"}',
            usage=SimpleNamespace(input_tokens=41, output_tokens=7),
        )


def test_openai_transport_preserves_the_structured_generation_contract() -> None:
    responses = _Responses()
    client = SimpleNamespace(responses=responses)
    transport = OpenAIResponsesTransport(
        api_key="deployment-key",
        timeout_seconds=90,
        reasoning_effort="low",
        client=client,
    )
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {"candidate_id": {"type": "string"}},
        "required": ["candidate_id"],
    }

    result = transport(
        {
            "model": "gpt-5.6-luna",
            "prompt": "Return the candidate.",
            "format": schema,
            "options": {"num_predict": 320},
        }
    )

    assert result == {
        "response": '{"candidate_id":"candidate-1"}',
        "prompt_eval_count": 41,
        "eval_count": 7,
    }
    assert responses.request == {
        "model": "gpt-5.6-luna",
        "input": "Return the candidate.",
        "reasoning": {"effort": "low"},
        "max_output_tokens": 320,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "toolrouter_structured_output",
                "schema": schema,
                "strict": True,
            }
        },
        "store": False,
    }
