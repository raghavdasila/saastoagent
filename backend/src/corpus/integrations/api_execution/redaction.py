from __future__ import annotations

from typing import Any, Mapping

from corpus.shared.api_execution import RedactedApiExecution, SafeApiTraceRecord

from .adapters import SafeApiExecutionOutcome


_TRACE_DETAIL_ALLOWLIST: Mapping[str, frozenset[str]] = {
    "execution_started": frozenset({"attempt"}),
    "request_validated": frozenset(),
    "execution_succeeded": frozenset({"status_code", "outcome_verified"}),
    "execution_failed": frozenset({"error_code", "status_code"}),
}


def redact_execution(outcome: SafeApiExecutionOutcome) -> RedactedApiExecution:
    result = outcome.result
    traces: list[SafeApiTraceRecord] = []
    for event in outcome.traces:
        allowed = _TRACE_DETAIL_ALLOWLIST.get(event.event)
        if allowed is None:
            continue
        details: dict[str, str | int | bool | None] = {}
        for key in allowed:
            value = event.safe_details.get(key)
            if value is None or isinstance(value, (str, int, bool)):
                details[key] = value
        traces.append(
            SafeApiTraceRecord(
                event=event.event,
                occurred_at=event.occurred_at.isoformat(),
                safe_details=details,
            )
        )
    return RedactedApiExecution(
        status=result.status.value,
        status_code=result.status_code,
        error_code=result.error_code,
        public_message=result.public_message,
        validation_issue_count=len(result.validation_issues),
        validation_phases=tuple(sorted({item.phase for item in result.validation_issues})),
        http_call_count=outcome.http_call_count,
        started_at=result.started_at.isoformat(),
        finished_at=result.finished_at.isoformat(),
        traces=tuple(traces),
    )


__all__ = ["RedactedApiExecution", "SafeApiTraceRecord", "redact_execution"]
