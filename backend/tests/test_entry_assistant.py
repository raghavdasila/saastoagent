from __future__ import annotations

import asyncio

from backend.core.config import settings
from backend.services.entry_runtime.entry_assistant import run_entry_assistant


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
    assert any(artifact.widget_type == "platform_overview" for artifact in artifacts)
    assert any(artifact.widget_type == "knowledge_citations" for artifact in artifacts)
    assert context and context[-1]["sources"]


def test_setup_request_creates_pre_auth_draft_without_activation(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "", raising=False)

    result, artifacts, _ = _run_assistant(
        user_input=(
            "Create a billing operator workspace using API https://api.example.com "
            "and OpenAPI spec https://api.example.com/openapi.json with bearer auth"
        ),
        selected_action_id=None,
        action_payload=None,
        existing_draft={},
        platform_question_context=[],
    )

    assert result.next_step == "ask"
    assert result.entry_draft["workspace_job"]
    assert result.entry_draft["api_draft"]["base_url"] == "https://api.example.com"
    assert result.entry_draft["api_draft"]["spec_url"] == "https://api.example.com/openapi.json"
    assert "sign in or create an account" in result.message.lower()
    assert any(artifact.widget_type == "setup_draft_summary" for artifact in artifacts)


def test_explicit_auth_intent_routes_deterministically(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", "", raising=False)

    result, artifacts, context = _run_assistant(
        user_input="sign in",
        selected_action_id=None,
        action_payload=None,
        existing_draft={"workspace_job": "billing ops"},
        platform_question_context=[],
    )

    assert result.next_step == "login"
    assert result.entry_draft == {"workspace_job": "billing ops"}
    assert artifacts == []
    assert context == []
