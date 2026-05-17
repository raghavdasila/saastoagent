import uuid

from backend.core.models import AgentExecutionTrace
from backend.services.agent.learning_service import learning_payload_from_trace


def test_learning_payload_from_failed_trace():
    trace = AgentExecutionTrace(
        id=uuid.uuid4(),
        saas_agent_id=uuid.uuid4(),
        tool_name="create_product",
        method="POST",
        path="/admin/products",
        status="failed",
        approval_state="approved",
        risk_level="write",
        error="HTTP 401",
    )

    payload = learning_payload_from_trace(trace)

    assert payload is not None
    assert payload["trigger_type"] == "failed_execution"
    assert "create_product" in payload["hint_text"]


def test_learning_payload_from_missing_inputs_trace():
    trace = AgentExecutionTrace(
        id=uuid.uuid4(),
        saas_agent_id=uuid.uuid4(),
        tool_name="get_order",
        method="GET",
        path="/store/orders/{id}",
        status="needs_input",
        approval_state="not_required",
        risk_level="read",
        missing_inputs=["id"],
    )

    payload = learning_payload_from_trace(trace)

    assert payload is not None
    assert payload["trigger_type"] == "missing_inputs"
    assert "id" in payload["hint_text"]
