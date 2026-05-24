from types import SimpleNamespace
import uuid

import pytest

from backend.services.agent import rest_operator
from backend.services.agent.timing import RequestTiming


def test_request_timing_records_named_spans_and_offsets():
    timing = RequestTiming()
    timing.mark("chat.request_received")
    with timing.span("router.decision"):
        pass

    snapshot = timing.snapshot()

    assert snapshot["total_ms"] >= 0
    assert [span["name"] for span in snapshot["spans"]] == ["chat.request_received", "router.decision"]
    assert all("offset_ms" in span and "duration_ms" in span for span in snapshot["spans"])


@pytest.mark.asyncio
async def test_finalize_execution_trace_schedules_rag_refresh_off_hot_path(monkeypatch):
    scheduled = []
    trace = SimpleNamespace(
        saas_agent_id=uuid.uuid4(),
        error=None,
        duration_ms=None,
        status="executing",
        route_node="executing",
    )

    class FakeDb:
        async def commit(self):
            return None

    def fake_schedule(saas_agent_id):
        scheduled.append(saas_agent_id)

    monkeypatch.setattr(rest_operator, "schedule_generated_knowledge_refresh", fake_schedule)

    await rest_operator.finalize_execution_trace(
        trace,
        {"status_code": 200, "body": {"ok": True}, "duration_ms": 12, "error": None},
        FakeDb(),
    )

    assert trace.status == "succeeded"
    assert trace.duration_ms == 12
    assert scheduled == [trace.saas_agent_id]
