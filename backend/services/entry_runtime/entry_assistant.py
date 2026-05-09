from __future__ import annotations

import re
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from backend.core.config import settings
from backend.core.schemas import EntryUIArtifact

from .platform_kb import PlatformKBResult, citation_payload, platform_kb
from .setup_planner import _infer_from_text


EntryAssistantNextStep = Literal["ask", "login", "register"]


class EntryAssistantResult(BaseModel):
    message: str = Field(description="Concise assistant response.")
    next_step: EntryAssistantNextStep = "ask"
    entry_draft: dict[str, Any] = Field(default_factory=dict)
    follow_up_prompts: list[str] = Field(default_factory=list)


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
    if action_id == "entry.learn.platform":
        return "What is SaaStoAgent and what can I build with it?"
    if action_id == "entry.learn.setup":
        return "How do I set up a workspace and connect an API?"
    return None


async def run_entry_assistant(
    *,
    user_input: str | None,
    selected_action_id: str | None,
    action_payload: dict[str, Any] | None,
    existing_draft: dict[str, Any] | None,
    platform_question_context: list[dict[str, Any]] | None,
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
        if not entry_draft.get("workspace_job"):
            entry_draft["workspace_job"] = _infer_workspace_job(prompt)

    kb_results = await platform_kb.search(prompt or "SaaStoAgent overview")
    fallback = _fallback_result(prompt=prompt, draft=entry_draft, kb_results=kb_results)
    result = fallback
    if prompt and settings.openai_api_key:
        result = await _llm_result(
            prompt=prompt,
            draft=entry_draft,
            kb_results=kb_results,
            fallback=fallback,
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

    artifacts = _build_artifacts(result.entry_draft, kb_results)
    return result, artifacts, context


def _looks_like_setup_request(prompt: str, setup_draft: dict[str, str]) -> bool:
    if setup_draft.get("base_url") or setup_draft.get("spec_url"):
        return True
    return bool(re.search(r"\b(api|openapi|swagger|workspace|operator|connect|setup)\b", prompt, re.I))


def _infer_workspace_job(prompt: str) -> str:
    value = re.sub(r"https?://\S+", "", prompt)
    value = re.sub(r"\b(connect|setup|create|build|api|openapi|swagger|workspace|operator)\b", "", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip(" .,-")
    return value[:120] or "SaaS operations"


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
            follow_up_prompts=[
                "What is SaaStoAgent?",
                "How does API setup work?",
                "I want to create a workspace",
            ],
        )

    if draft.get("api_draft") or draft.get("workspace_job"):
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
) -> EntryAssistantResult:
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
                        "Keep responses concise and useful. Preserve any draft values provided."
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


def _build_artifacts(
    draft: dict[str, Any],
    kb_results: list[PlatformKBResult],
) -> list[EntryUIArtifact]:
    artifacts = [
        EntryUIArtifact(
            id="platform-overview",
            kind="widget",
            surface="both",
            title="Platform Overview",
            widget_type="platform_overview",
            payload={
                "cards": [
                    {
                        "title": "Workspace-owned operator",
                        "body": "One workspace owns the REST sources, inferred actions, chat runtime, QA, and learnings.",
                    },
                    {
                        "title": "REST-first setup",
                        "body": "Connect an OpenAPI or Swagger spec, generate action nodes, then activate callable tools.",
                    },
                    {
                        "title": "Closed improvement loop",
                        "body": "Capture weak outcomes, inspect traces, tune behavior, and persist validated learnings.",
                    },
                ]
            },
        ),
        EntryUIArtifact(
            id="onboarding-checklist",
            kind="widget",
            surface="inline",
            title="Onboarding Checklist",
            widget_type="onboarding_checklist",
            payload={
                "items": [
                    {"label": "Ask questions or describe the intended operator", "status": "active"},
                    {"label": "Sign in or create an account", "status": "pending"},
                    {"label": "Create or select a workspace", "status": "pending"},
                    {"label": "Connect and activate a REST API", "status": "pending"},
                ]
            },
        ),
        EntryUIArtifact(
            id="knowledge-citations",
            kind="widget",
            surface="inline",
            title="Knowledge Sources",
            widget_type="knowledge_citations",
            payload={"sources": citation_payload(kb_results)},
        ),
    ]
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
    artifacts.append(
        EntryUIArtifact(
            id="platform-loop",
            kind="markup",
            surface="canvas",
            title="SaaStoAgent Loop",
            markup=(
                '<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SaaStoAgent loop">'
                '<rect width="640" height="220" rx="18" fill="#061018"/>'
                '<g fill="#0ea5e9" font-family="Inter,Arial" font-size="17" font-weight="700">'
                '<text x="58" y="70">Workspace</text><text x="230" y="70">REST Actions</text>'
                '<text x="430" y="70">Operator Chat</text><text x="245" y="172">QA + Learnings</text></g>'
                '<g stroke="#38bdf8" stroke-width="3" fill="none" stroke-linecap="round">'
                '<path d="M145 64 H220"/><path d="M356 64 H424"/><path d="M506 84 C500 162 396 172 350 172"/>'
                '<path d="M234 172 C148 166 92 125 98 83"/></g>'
                '<g fill="#082f49" stroke="#38bdf8" stroke-width="2">'
                '<circle cx="112" cy="64" r="34"/><circle cx="290" cy="64" r="42"/><circle cx="494" cy="64" r="42"/><circle cx="312" cy="172" r="42"/></g>'
                '</svg>'
            ),
        )
    )
    return artifacts
