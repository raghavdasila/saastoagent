from __future__ import annotations

import json
import os

from corpus.integrations.toolrouter.openai_responses import OpenAIResponsesTransport


transport = OpenAIResponsesTransport(
    api_key=os.environ["OPENAI_API_KEY"],
    timeout_seconds=90,
    reasoning_effort="low",
)
result = transport(
    {
        "model": "gpt-5.6-luna",
        "prompt": "Return status ok.",
        "format": {
            "type": "object",
            "additionalProperties": False,
            "properties": {"status": {"type": "string", "enum": ["ok"]}},
            "required": ["status"],
        },
        "options": {"num_predict": 128},
    }
)
assert json.loads(result["response"]) == {"status": "ok"}
print("OpenAI gpt-5.6-luna structured transport OK")
