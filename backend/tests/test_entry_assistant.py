from __future__ import annotations

import asyncio

from backend.core.config import settings
from backend.services.entry_runtime import entry_assistant
from backend.services.entry_runtime.entry_assistant import EntryAssistantResult, run_entry_assistant
from backend.services.entry_runtime.stage_events import stream_chunks


def _run_assistant(**kwargs):
    return asyncio.run(run_entry_assistant(**kwargs))


def test_anonymous_platform_question_uses_kb_and_actions_without_auth(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "", raising=False)

    result, artifacts, context = _run_assistant(
        user_input="What is this platform and how do I use it?",
        selected_action_id=None,
        action_payload=None,
        existing_draft={},
        platform_question_context=[],
    )

    assert result.next_step == "ask"
    assert "sign in/create an account" in result.message.lower()
    assert result.follow_up_prompts
    assert artifacts == []
    assert context and context[-1]["sources"]


def test_setup_request_creates_pre_auth_draft_without_activation(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "", raising=False)

    result, artifacts, _ = _run_assistant(
        user_input=(
            "Create a workspace using API https://api.example.com "
            "and OpenAPI spec https://api.example.com/openapi.json with bearer auth"
        ),
        selected_action_id=None,
        action_payload=None,
        existing_draft={},
        platform_question_context=[],
    )

    assert result.next_step == "ask"
    assert "workspace_job" not in result.entry_draft
    assert "workspace_name" not in result.entry_draft
    assert result.entry_draft["api_draft"]["base_url"] == "https://api.example.com"
    assert result.entry_draft["api_draft"]["spec_url"] == "https://api.example.com/openapi.json"
    assert "sign in or create an account" in result.message.lower()
    assert any(artifact.widget_type == "setup_draft_summary" for artifact in artifacts)


def test_setup_request_preserves_explicit_workspace_name_only(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "", raising=False)

    result, _, _ = _run_assistant(
        user_input=(
            "Create a workspace named Support Ops using API https://api.example.com "
            "and OpenAPI spec https://api.example.com/openapi.json"
        ),
        selected_action_id=None,
        action_payload=None,
        existing_draft={},
        platform_question_context=[],
    )

    assert result.entry_draft["workspace_name"] == "Support Ops"
    assert "workspace_job" not in result.entry_draft


def test_explicit_auth_intent_routes_deterministically(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "", raising=False)

    result, artifacts, context = _run_assistant(
        user_input="sign in",
        selected_action_id=None,
        action_payload=None,
        existing_draft={"workspace_name": "Billing"},
        platform_question_context=[],
    )

    assert result.next_step == "login"
    assert result.entry_draft == {"workspace_name": "Billing"}
    assert artifacts == []
    assert context == []


def test_public_assistant_streams_live_deltas_when_llm_is_available(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "test-key", raising=False)
    deltas: list[tuple[str, bool]] = []

    async def fake_streaming_llm_result(**kwargs):
        await kwargs["on_delta"]("Hello ", False)
        await kwargs["on_delta"]("live", False)
        await kwargs["on_delta"]("", True)
        return EntryAssistantResult(
            message="Hello live",
            entry_draft=kwargs["draft"],
            follow_up_prompts=["Create account"],
            message_live_streamed=True,
        )

    async def collect_delta(content: str, is_final: bool) -> None:
        deltas.append((content, is_final))

    monkeypatch.setattr(entry_assistant, "_streaming_llm_result", fake_streaming_llm_result)

    result, _, _ = _run_assistant(
        user_input="What is SaaStoAgent?",
        selected_action_id=None,
        action_payload=None,
        existing_draft={},
        platform_question_context=[],
        on_delta=collect_delta,
    )

    assert deltas == [("Hello ", False), ("live", False), ("", True)]
    assert result.message == "Hello live"
    assert result.message_live_streamed is True


def test_stage_output_does_not_fake_token_chunks():
    message = "This response is deliberately long enough that the old chunking hack would split it."

    assert stream_chunks(message) == [message]
