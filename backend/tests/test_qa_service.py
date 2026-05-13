from __future__ import annotations

from backend.services.qa.schemas import QAEvalRequest, QAEvidenceGate
from backend.services.qa.service import evaluate_turn, is_reset_allowed, list_scenarios


def test_qa_scenarios_cover_navigation_permutations():
    scenarios = {scenario.id: scenario for scenario in list_scenarios()}

    assert {
        "first_load_contract",
        "general_question",
        "signin_cancel_signup",
        "auth_mode_switches",
        "invalid_email_recovery",
        "signup_workspace_path",
        "routedeck_smoke",
    } <= set(scenarios)
    assert any(
        action.params.get("action_id") == "nav.cancel"
        for milestone in scenarios["signin_cancel_signup"].milestones
        for action in milestone.actions
    )


def test_qa_evaluator_checks_route_deck_action_and_forbidden_copy():
    result = evaluate_turn(
        QAEvalRequest(
            evidence={
                "current_node": "intent",
                "route_deck_snapshot_present": True,
                "enabled_action_ids": ["intent.sign_in", "intent.register"],
                "visible_text": "Welcome. Ask a question or sign in.",
                "assistant_messages": ["Welcome. Ask a question or sign in."],
                "console_errors": [],
            },
            evidence_gates=[
                QAEvidenceGate(gate="route_deck_current_node", params={"node": "intent"}),
                QAEvidenceGate(gate="action_enabled", params={"action_id": "intent.register"}),
                QAEvidenceGate(gate="message_not_contains", params={"text": "valid email address"}),
                QAEvidenceGate(gate="no_console_errors", params={}),
            ],
        )
    )

    assert result.verdict == "pass"
    assert result.failures == []


def test_qa_evaluator_fails_missing_recovery_action():
    result = evaluate_turn(
        QAEvalRequest(
            evidence={"current_node": "email", "enabled_action_ids": ["intent.register"]},
            evidence_gates=[
                QAEvidenceGate(gate="route_deck_current_node", params={"node": "email"}),
                QAEvidenceGate(gate="action_enabled", params={"action_id": "nav.cancel"}),
            ],
        )
    )

    assert result.verdict == "fail"
    assert "action_enabled" in result.failures


def test_qa_reset_guard_defaults_to_local_dev_secret_only():
    assert is_reset_allowed("CHANGE-ME-IN-PRODUCTION")
    assert is_reset_allowed("dev-secret-change-in-prod")
    assert not is_reset_allowed("production-secret")
