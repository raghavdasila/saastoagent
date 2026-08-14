from __future__ import annotations

import re
from collections.abc import Mapping


class ClarificationInputRejected(ValueError):
    pass


def screen_clarification_values(
    message: str, answers: Mapping[str, str] | None = None
) -> None:
    values = (message, *(answers or {}).keys(), *(answers or {}).values())
    if any(not str(item).strip() for item in values):
        raise ClarificationInputRejected(
            "Clarification values must be explicit and non-empty."
        )
    if any(_sensitive_name(str(name)) for name in (answers or {})):
        raise ClarificationInputRejected(
            "Credentials and secret values cannot be used for clarification."
        )
    if any(_secret_like_value(str(item)) for item in values):
        raise ClarificationInputRejected(
            "Credentials and secret values cannot be used for clarification."
        )


def parse_clarification_answers(
    message: str, missing_names: tuple[str, ...]
) -> dict[str, str]:
    normalized = message.strip()
    if not missing_names:
        screen_clarification_values(normalized)
        return {}
    if len(missing_names) == 1:
        answers = {missing_names[0]: normalized}
        screen_clarification_values(normalized, answers)
        return answers
    pieces = tuple(
        item.strip()
        for item in re.split(r"[;\n,]+", normalized)
        if item.strip()
    )
    answers: dict[str, str] = {}
    for piece in pieces:
        name, separator, value = piece.partition("=")
        if separator != "=" or not name.strip() or not value.strip():
            raise ClarificationInputRejected(
                "Answer every requested input as name=value."
            )
        canonical = next(
            (item for item in missing_names if item.casefold() == name.strip().casefold()),
            None,
        )
        if canonical is None or canonical in answers:
            raise ClarificationInputRejected(
                "Answer every exact requested input and no others."
            )
        answers[canonical] = value.strip()
    if set(answers) != set(missing_names):
        raise ClarificationInputRejected(
            "Answer every exact requested input and no others."
        )
    screen_clarification_values(normalized, answers)
    return answers


def _sensitive_name(value: str) -> bool:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value).casefold()
    collapsed = re.sub(r"[^a-z0-9]", "", normalized)
    fragments = (
        "authorization",
        "bearer",
        "cookie",
        "credential",
        "password",
        "passwd",
        "secret",
        "token",
        "apikey",
        "privatekey",
        "publishablekey",
        "accesskey",
        "clientkey",
    )
    return any(fragment in collapsed for fragment in fragments)


def _secret_like_value(value: str) -> bool:
    stripped = value.strip()
    return bool(
        re.search(r"(?i)\bbearer\s+[a-z0-9._~+/=-]{8,}", stripped)
        or "-----BEGIN PRIVATE KEY-----" in stripped
        or re.fullmatch(
            r"eyJ[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,}\.[a-zA-Z0-9_-]{8,}",
            stripped,
        )
        or re.search(
            r"(?i)\b(?:authorization|cookie|client[_ -]?secret|access[_ -]?token|"
            r"refresh[_ -]?token|x[_ -]?api[_ -]?key|x[_ -]?publishable[_ -]?api[_ -]?key)"
            r"\s*[:=]\s*\S+",
            stripped,
        )
    )


__all__ = [
    "ClarificationInputRejected",
    "parse_clarification_answers",
    "screen_clarification_values",
]
