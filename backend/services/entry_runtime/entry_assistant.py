from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from backend.core.config import settings
from backend.core.schemas import EntryUIArtifact
from backend.services.route_deck import RouteDeckActionIds

from .platform_kb import PlatformKBResult, platform_kb
from .setup_planner import _infer_from_text


EntryAssistantNextStep = Literal["ask", "login", "register"]
EntryAssistantDeltaSink = Callable[[str, bool], Awaitable[None]]


class EntryAssistantResult(BaseModel):
    message: str = Field(description="Concise assistant response.")
    next_step: EntryAssistantNextStep = "ask"
    entry_draft: dict[str, Any] = Field(default_factory=dict)
    follow_up_prompts: list[str] = Field(default_factory=list)
    message_live_streamed: bool = False


def _detect_auth_intent(value: str) -> EntryAssistantNextStep | None:
    normalized = value.strip().lower()
    if not normalized:
        return None
    if re.search(r"\b(sign\s?in|log\s?in|login|access|enter)\b", normalized) and not re.search(
        r"\b(sign\s?up|register|create account|new account)\b",
        normalized,
    ):
        return "login"
    if re.search(r"\b(sign\s?up|register|create account|new account|join)\b", normalized):
        return "register"
    return None


def action_prompt(action_id: str | None, payload: dict[str, Any] | None) -> str | None:
    if payload and isinstance(payload.get("prompt"), str):
        return str(payload["prompt"])
    if action_id == RouteDeckActionIds.ENTRY_LEARN_PLATFORM:
        return "What is SaaStoAgent and what can I build with it?"
    if action_id == RouteDeckActionIds.ENTRY_LEARN_SETUP:
        return "How do I set up a workspace and connect an API?"
    return None


async def run_entry_assistant(
    *,
    user_input: str | None,
    selected_action_id: str | None,
    action_payload: dict[str, Any] | None,
    existing_draft: dict[str, Any] | None,
    platform_question_context: list[dict[str, Any]] | None,
    on_delta: EntryAssistantDeltaSink | None = None,
) -> tuple[EntryAssistantResult, list[EntryUIArtifact], list[dict[str, Any]]]:
    prompt = action_prompt(selected_action_id, action_payload) or (user_input or "").strip()
    existing = dict(existing_draft or {})
    auth_intent = _detect_auth_intent(prompt)
    if auth_intent:
        return (
            EntryAssistantResult(
                message=(
                    "I can sign you in. Send the email for your account."
                    if auth_intent == "login"
                    else "I can create the account. What display name should I use? Type `skip` to leave it blank."
                ),
                next_step=auth_intent,
                entry_draft=existing,
            ),
            [],
            platform_question_context or [],
        )

    setup_draft = _infer_from_text(prompt, existing.get("api_draft") or None)
    entry_draft = dict(existing)
    if _looks_like_setup_request(prompt, setup_draft):
        entry_draft["api_draft"] = setup_draft
        workspace_name = _infer_workspace_name(prompt)
        if workspace_name and not entry_draft.get("workspace_name"):
            entry_draft["workspace_name"] = workspace_name

    kb_results = await platform_kb.search(prompt or "SaaStoAgent overview")
    fallback = _fallback_result(prompt=prompt, draft=entry_draft, kb_results=kb_results)
    result = fallback
    if settings.openai_api_key:
        result = await _llm_result(
            prompt=prompt,
            draft=entry_draft,
            kb_results=kb_results,
            fallback=fallback,
            on_delta=on_delta,
        )

    context = list(platform_question_context or [])
    if prompt:
        context.append(
            {
                "question": prompt[:300],
                "sources": [item.chunk.source_path for item in kb_results],
            }
        )
        context = context[-8:]

    artifacts = _build_artifacts(result.entry_draft, kb_results) if prompt else []
    return result, artifacts, context


def _looks_like_setup_request(prompt: str, setup_draft: dict[str, str]) -> bool:
    if setup_draft.get("base_url") or setup_draft.get("spec_url"):
        return True
    return bool(re.search(r"\b(api|openapi|swagger|workspace|operator|connect|setup)\b", prompt, re.I))


def _infer_workspace_name(prompt: str) -> str | None:
    patterns = [
        r"\bworkspace\s+(?:named|called)\s+([A-Za-z0-9][A-Za-z0-9 _.-]{1,80})",
        r"\b(?:named|called)\s+([A-Za-z0-9][A-Za-z0-9 _.-]{1,80})\s+workspace\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt, flags=re.I)
        if match:
            value = re.sub(r"https?://\S+", "", match.group(1))
            value = re.split(r"\b(?:using|with|and|that|which)\b", value, maxsplit=1, flags=re.I)[0]
            value = re.sub(r"\s+", " ", value).strip(" .,-")
            return value[:80] or None
    return None


def _fallback_result(
    *,
    prompt: str,
    draft: dict[str, Any],
    kb_results: list[PlatformKBResult],
) -> EntryAssistantResult:
    if not prompt:
        return EntryAssistantResult(
            message=(
                "I can explain SaaStoAgent, help draft the workspace/API setup, or get you signed in when you are ready."
            ),
            entry_draft=draft,
            follow_up_prompts=[],
        )

    if draft.get("api_draft") or draft.get("workspace_name") or draft.get("workspace_job"):
        return EntryAssistantResult(
            message=(
                "I saved that as a setup draft. To actually create the workspace or activate the API, sign in or create an account; "
                "I will carry these details forward."
            ),
            entry_draft=draft,
            follow_up_prompts=[
                "Create account",
                "What details are still needed?",
                "Show me what is in the draft",
            ],
        )

    source_text = " ".join(result.chunk.content for result in kb_results[:2])
    return EntryAssistantResult(
        message=(
            source_text[:520]
            + " You can keep asking questions, or sign in/create an account when you want to start building."
        ),
        entry_draft=draft,
        follow_up_prompts=[
            "How does setup work?",
            "What happens after activation?",
            "Create account",
        ],
    )


async def _llm_result(
    *,
    prompt: str,
    draft: dict[str, Any],
    kb_results: list[PlatformKBResult],
    fallback: EntryAssistantResult,
    on_delta: EntryAssistantDeltaSink | None = None,
) -> EntryAssistantResult:
    if on_delta is not None:
        return await _streaming_llm_result(
            prompt=prompt,
            draft=draft,
            kb_results=kb_results,
            fallback=fallback,
            on_delta=on_delta,
        )

    llm = ChatOpenAI(
        model=settings.default_model,
        api_key=settings.openai_api_key,
    ).with_structured_output(EntryAssistantResult, method="function_calling")
    kb_context = "\n".join(
        f"- {result.chunk.title} ({result.chunk.source_path}): {result.chunk.content}"
        for result in kb_results
    )
    try:
        result = await llm.ainvoke(
            [
                SystemMessage(
                    content=(
                        "You are the public entry assistant for SaaStoAgent. Conversation is primary. "
                        "Answer platform questions from the supplied knowledge context, help draft workspace/API setup before auth, "
                        "and only route to login/register when the user explicitly asks. Do not claim actions are completed before auth. "
                        "Keep responses concise and useful. Preserve any draft values provided. "
                        "When the answer has sections, emit valid Markdown with explicit ## headings, bullet lists, and fenced code blocks for JSON. "
                        "Do not use plain heading-like paragraphs for sections."
                    )
                ),
                HumanMessage(
                    content=(
                        f"Knowledge context:\n{kb_context}\n\n"
                        f"Existing/detected draft:\n{draft}\n\n"
                        f"User message:\n{prompt or '(initial empty turn)'}"
                    )
                ),
            ]
        )
    except Exception:
        return fallback
    merged_draft = dict(draft)
    merged_draft.update(result.entry_draft or {})
    return EntryAssistantResult(
        message=result.message.strip() or fallback.message,
        next_step=result.next_step,
        entry_draft=merged_draft,
        follow_up_prompts=result.follow_up_prompts[:4] or fallback.follow_up_prompts,
    )


async def _streaming_llm_result(
    *,
    prompt: str,
    draft: dict[str, Any],
    kb_results: list[PlatformKBResult],
    fallback: EntryAssistantResult,
    on_delta: EntryAssistantDeltaSink,
) -> EntryAssistantResult:
    llm = ChatOpenAI(
        model=settings.default_model,
        api_key=settings.openai_api_key,
        streaming=True,
    )
    messages = _assistant_messages(prompt=prompt, draft=draft, kb_results=kb_results)
    chunks: list[str] = []
    try:
        async for chunk in llm.astream(messages):
            text = _content_text(getattr(chunk, "content", ""))
            if not text:
                continue
            chunks.append(text)
            await on_delta(text, False)
    except Exception:
        return fallback

    message = "".join(chunks).strip()
    if not message:
        return fallback
    await on_delta("", True)
    return EntryAssistantResult(
        message=message,
        next_step="ask",
        entry_draft=draft,
        follow_up_prompts=fallback.follow_up_prompts,
        message_live_streamed=True,
    )


def _assistant_messages(
    *,
    prompt: str,
    draft: dict[str, Any],
    kb_results: list[PlatformKBResult],
) -> list[SystemMessage | HumanMessage]:
    kb_context = "\n".join(
        f"- {result.chunk.title} ({result.chunk.source_path}): {result.chunk.content}"
        for result in kb_results
    )
    return [
        SystemMessage(
            content=(
                "You are the public entry assistant for SaaStoAgent. Conversation is primary. "
                "Answer platform questions from the supplied knowledge context, help draft workspace/API setup before auth, "
                "and only route to login/register when the user explicitly asks. Do not claim actions are completed before auth. "
                "Keep responses concise and useful. Preserve any draft values provided. "
                "When the answer has sections, emit valid Markdown with explicit ## headings, bullet lists, and fenced code blocks for JSON. "
                "Do not use plain heading-like paragraphs for sections."
            )
        ),
        HumanMessage(
            content=(
                f"Knowledge context:\n{kb_context}\n\n"
                f"Existing/detected draft:\n{draft}\n\n"
                f"User message:\n{prompt or '(initial empty turn)'}"
            )
        ),
    ]


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                value = item.get("text") or item.get("content")
                if isinstance(value, str):
                    parts.append(value)
        return "".join(parts)
    return ""


def _build_artifacts(
    draft: dict[str, Any],
    kb_results: list[PlatformKBResult],
) -> list[EntryUIArtifact]:
    artifacts: list[EntryUIArtifact] = []
    if draft:
        artifacts.append(
            EntryUIArtifact(
                id="setup-draft",
                kind="widget",
                surface="both",
                title="Setup Draft",
                widget_type="setup_draft_summary",
                payload={"draft": draft},
            )
        )
    return artifacts
