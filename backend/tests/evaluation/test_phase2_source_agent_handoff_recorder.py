from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "record_phase2_source_agent_handoff.py"
SPEC = importlib.util.spec_from_file_location("phase2_handoff_recorder", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_preflight_fails_before_recording_when_conversation_is_missing(monkeypatch) -> None:
    monkeypatch.setenv("CORPUS_PHASE2_ACCESS_TOKEN", "opaque-test-access")

    def missing(*_args, **_kwargs):
        raise RuntimeError("preflight HTTP 404: conversation_not_found")

    monkeypatch.setattr(MODULE, "_get_json", missing)
    args = MODULE.argparse.Namespace(
        conversation_id="missing-conversation",
        backend_url="http://127.0.0.1:8099",
        expected_node="sources.api",
        expected_agent_ref=None,
        expected_source_id=None,
        expected_revision_id=None,
    )
    with pytest.raises(RuntimeError, match="conversation_not_found"):
        MODULE._preflight(args)


def test_preflight_requires_exact_current_node(monkeypatch) -> None:
    monkeypatch.setenv("CORPUS_PHASE2_ACCESS_TOKEN", "opaque-test-access")
    responses = iter(
        [
            {"current_node_id": "agents.home", "session_version": 4},
            {"agent_context": {"snapshot": {}}, "operation_id": "agents.return_from_source"},
        ]
    )
    monkeypatch.setattr(MODULE, "_get_json", lambda *_args, **_kwargs: next(responses))
    args = MODULE.argparse.Namespace(
        conversation_id="retained-conversation",
        backend_url="http://127.0.0.1:8099",
        expected_node="sources.api",
        expected_agent_ref=None,
        expected_source_id=None,
        expected_revision_id=None,
    )
    with pytest.raises(RuntimeError, match="checkpoint node is 'agents.home'"):
        MODULE._preflight(args)


def test_preflight_retains_typed_operation_chronology(monkeypatch) -> None:
    monkeypatch.setenv("CORPUS_PHASE2_ACCESS_TOKEN", "opaque-test-access")
    responses = iter(
        [
            {"current_node_id": "sources.api", "session_version": 9},
            {
                "agent_context": {"snapshot": {}},
                "recent_operations": [
                    {"operation_id": "sources.approve_contract_revision"},
                    {"operationId": "sources.save_api_operation_curation"},
                ],
                "events": [
                    {"operation_id": "sources.approve_contract_revision"},
                    {"operationId": "sources.save_api_operation_curation"},
                ],
            },
        ]
    )
    monkeypatch.setattr(MODULE, "_get_json", lambda *_args, **_kwargs: next(responses))
    args = MODULE.argparse.Namespace(
        conversation_id="retained-conversation",
        backend_url="http://127.0.0.1:8099",
        expected_node="sources.api",
        expected_agent_ref=None,
        expected_source_id=None,
        expected_revision_id=None,
    )
    assert MODULE._preflight(args) == {
        "conversationId": "retained-conversation",
        "nodeId": "sources.api",
        "sessionVersion": 9,
        "operationIds": [
            "sources.approve_contract_revision",
            "sources.save_api_operation_curation",
        ],
        "committedOperationIds": [
            "sources.approve_contract_revision",
            "sources.save_api_operation_curation",
        ],
        "chatMessageCount": 0,
        "latestAssistant": None,
        "agentRef": None,
        "sourceId": None,
        "revisionId": None,
    }


def test_preflight_requires_exact_agent_source_revision_binding(monkeypatch) -> None:
    monkeypatch.setenv("CORPUS_PHASE2_ACCESS_TOKEN", "opaque-test-access")
    responses = iter(
        [
            {"current_node_id": "sources.api", "session_version": 9},
            {
                "agent_context": {
                    "snapshot": {},
                    "messages": [],
                    "model_context": {
                        "active_surface": {
                            "values": [
                                {"name": "return_agent_ref", "value": "agent-exact"},
                                {"name": "selected_source_id", "value": "source-exact"},
                                {"name": "selected_source_revision_id", "value": "revision-wrong"},
                            ]
                        }
                    },
                }
            },
        ]
    )
    monkeypatch.setattr(MODULE, "_get_json", lambda *_args, **_kwargs: next(responses))
    args = MODULE.argparse.Namespace(
        conversation_id="retained-conversation",
        backend_url="http://127.0.0.1:8099",
        expected_node="sources.api",
        expected_agent_ref="agent-exact",
        expected_source_id="source-exact",
        expected_revision_id="revision-exact",
    )
    with pytest.raises(RuntimeError, match="selected_source_revision_id"):
        MODULE._preflight(args)


def test_committed_operation_delta_does_not_parse_tool_message_strings() -> None:
    inspection = {
        "recent_operations": [{"operation_id": "sources.inspect_current_api"}],
        "agent_context": {
            "messages": [
                {
                    "role": "tool",
                    "content": '{"operation_id":"agents.return_from_source"}',
                }
            ]
        },
    }

    assert MODULE._committed_operation_ids(inspection) == ["sources.inspect_current_api"]
