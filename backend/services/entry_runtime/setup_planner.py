from __future__ import annotations

import re
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from backend.core.config import settings


SetupPlannerNextStep = Literal["ask", "show_form", "confirm", "open_chat"]


class SetupPlannerResult(BaseModel):
    message: str = Field(
        description="One concise assistant reply for the user. Do not mention internal graph nodes or schemas."
    )
    next_step: SetupPlannerNextStep = Field(
        description="What the graph should do next."
    )
    draft: dict[str, str] = Field(
        default_factory=dict,
        description="Known REST connection details: name, base_url, spec_url, auth_type, credential_value, header_name, query_param_name.",
    )
    missing: list[str] = Field(
        default_factory=list,
        description="Missing required details before activation.",
    )


REQUIRED_FIELDS = ("name", "base_url", "spec_url", "auth_type")
SUPPORTED_AUTH_TYPES = {
    "none",
    "bearer",
    "api_key_header",
    "api_key_query",
    "basic",
    "custom_header",
    "oauth_client_credentials",
}


def _clean_draft(draft: dict[str, Any] | None) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for key, value in (draft or {}).items():
        if value is None:
            continue
        text = str(value).strip()
        if text:
            cleaned[key] = text
    if cleaned.get("auth_type") not in SUPPORTED_AUTH_TYPES:
        cleaned["auth_type"] = "none"
    return cleaned


def _missing_fields(draft: dict[str, str]) -> list[str]:
    missing = [field for field in REQUIRED_FIELDS if not draft.get(field)]
    auth_type = draft.get("auth_type", "none")
    if auth_type != "none" and not draft.get("credential_value"):
        missing.append("credential_value")
    if auth_type in {"api_key_header", "custom_header"} and not draft.get("header_name"):
        missing.append("header_name")
    if auth_type == "api_key_query" and not draft.get("query_param_name"):
        missing.append("query_param_name")
    return missing


def _merge_draft(existing: dict[str, Any] | None, update: dict[str, Any] | None) -> dict[str, str]:
    draft = _clean_draft(existing)
    for key, value in _clean_draft(update).items():
        draft[key] = value
    if "auth_type" not in draft:
        draft["auth_type"] = "none"
    return draft


def _merge_llm_and_heuristic(
    *,
    llm_draft: dict[str, Any] | None,
    heuristic_draft: dict[str, Any],
) -> dict[str, str]:
    draft = _merge_draft(heuristic_draft, llm_draft)
    heuristic = _clean_draft(heuristic_draft)
    # URLs and auth markers extracted directly from the user's text are more
    # reliable than model-normalized URLs.
    for key in ("base_url", "spec_url", "auth_type"):
        if heuristic.get(key):
            draft[key] = heuristic[key]
    return draft


def _infer_from_text(user_input: str, existing: dict[str, Any] | None = None) -> dict[str, str]:
    draft = _clean_draft(existing)
    value = user_input.strip()
    if not value:
        if "auth_type" not in draft:
            draft["auth_type"] = "none"
        return draft

    urls = re.findall(r"https?://[^\s,)>\]}]+", value)
    if urls:
        if not draft.get("base_url"):
            draft["base_url"] = urls[0].rstrip(".,")
        spec_candidates = [
            url.rstrip(".,")
            for url in urls
            if re.search(
                r"(openapi|swagger|api-docs|schema|\.ya?ml|\.json)",
                re.sub(r"^https?://[^/]+", "", url),
                re.I,
            )
        ]
        if spec_candidates:
            draft["spec_url"] = spec_candidates[0]
        elif len(urls) > 1 and not draft.get("spec_url"):
            draft["spec_url"] = urls[1].rstrip(".,")

    if re.search(r"\b(no auth|without auth|public api|unauthenticated)\b", value, re.I):
        draft["auth_type"] = "none"
    elif re.search(r"\b(bearer|token)\b", value, re.I):
        draft["auth_type"] = "bearer"
    elif re.search(r"\b(api key|apikey)\b", value, re.I):
        draft["auth_type"] = "api_key_header"

    name_match = re.search(
        r"(?:name|call it|called)\s*[:=]?\s*([A-Za-z0-9][A-Za-z0-9 _.-]{1,80})",
        value,
        re.I,
    )
    if name_match and not draft.get("name"):
        draft["name"] = name_match.group(1).strip(" .")
    elif not draft.get("name") and draft.get("base_url"):
        host_match = re.search(r"https?://(?:www\.)?([^/]+)", draft["base_url"])
        if host_match:
            host = host_match.group(1).split(":")[0]
            draft["name"] = " ".join(part.capitalize() for part in host.split(".")[:2])

    if "auth_type" not in draft:
        draft["auth_type"] = "none"
    return draft


def _fallback_plan(
    *,
    user_input: str,
    existing_draft: dict[str, Any] | None,
    force_form: bool = False,
) -> SetupPlannerResult:
    draft = _infer_from_text(user_input, existing_draft)
    missing = _missing_fields(draft)

    if force_form:
        return SetupPlannerResult(
            message="Use the setup form below for the API details. I will keep anything already known filled in.",
            next_step="show_form",
            draft=draft,
            missing=missing,
        )

    if user_input.strip() and not missing:
        return SetupPlannerResult(
            message=f"I have enough to connect {draft.get('name', 'this API')}. Review the details and activate it when ready.",
            next_step="confirm",
            draft=draft,
            missing=[],
        )

    if user_input.strip():
        readable_missing = ", ".join(missing)
        return SetupPlannerResult(
            message=f"I still need {readable_missing}. Send those details here, or open the form if that is faster.",
            next_step="ask",
            draft=draft,
            missing=missing,
        )

    return SetupPlannerResult(
        message=(
            "Tell me the API this operator should use. A base URL and OpenAPI or Swagger spec URL are enough to start; "
            "include auth details only if the API needs them."
        ),
        next_step="ask",
        draft=draft,
        missing=missing,
    )


async def plan_setup_turn(
    *,
    workspace_name: str | None,
    user_input: str | None,
    existing_draft: dict[str, Any] | None,
    force_form: bool = False,
) -> SetupPlannerResult:
    value = (user_input or "").strip()
    fallback = _fallback_plan(
        user_input=value,
        existing_draft=existing_draft,
        force_form=force_form,
    )
    if force_form or not settings.openai_api_key:
        return fallback

    llm = ChatOpenAI(
        model=settings.default_model,
        api_key=settings.openai_api_key,
    ).with_structured_output(SetupPlannerResult, method="function_calling")

    system = SystemMessage(
        content=(
            "You are the onboarding operator for SaaStoAgent. Your job is to help the user connect the REST API "
            "their workspace operator should use. Be conversational and concise. Do not open a form by default. "
            "Infer connection details from the user's message when possible. Required details are connection name, "
            "base URL, OpenAPI or Swagger spec URL, and auth type. Auth type must be one of: none, bearer, "
            "api_key_header, api_key_query, basic, custom_header, oauth_client_credentials. If details are missing, "
            "ask only for the missing details. If all required details are present, set next_step to confirm. "
            "Use show_form only when the user explicitly asks for a form or says they want to edit details. "
            "When returning a sectioned reply, use valid Markdown with ## headings and bullets."
        )
    )
    human = HumanMessage(
        content=(
            f"Workspace: {workspace_name or 'current workspace'}\n"
            f"Existing draft: {_clean_draft(existing_draft)}\n"
            f"Heuristic draft from latest message: {fallback.draft}\n"
            f"Latest user message: {value or '(no latest user message; start the setup conversation)'}"
        )
    )

    try:
        result = await llm.ainvoke([system, human])
    except Exception:
        return fallback

    draft = _merge_llm_and_heuristic(
        llm_draft=result.draft,
        heuristic_draft=fallback.draft,
    )
    missing = _missing_fields(draft)
    next_step = result.next_step
    if missing and next_step == "confirm":
        next_step = "ask"
    if not missing and value and next_step == "ask":
        next_step = "confirm"
    return SetupPlannerResult(
        message=result.message.strip() or fallback.message,
        next_step=next_step,
        draft=draft,
        missing=missing,
    )
