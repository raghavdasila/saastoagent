from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest
import scripts.run_horizontal_product_journey as horizontal_journey
from scripts.run_api_route_planning_journey import (
    is_expected_completed_chat_abort,
)

from scripts.run_horizontal_product_journey import (
    CHAT_FORBIDDEN_PHRASES,
    CHAT_EVIDENCE_OPERATION_IDS,
    CHAT_OPERATION_SAFETY_CLASSES,
    CHAT_PROMPTS,
    EXPECTED_CHECKS,
    FEATURE_SURFACE_SELECTORS,
    _asks_for_agent_choice,
    _asks_for_agent_details,
    _chat_operation_evidence,
    _chat_inspection_tool_shapes,
    _chat_operations_after,
    _chat_operation_after,
    _classify_expected_graph_capture_warnings,
    _classify_expected_restart_interruptions,
    _contract_review_id,
    _capture,
    _durable_chat_message,
    _latest_build_request_id,
    _latest_channel_id,
    _latest_evaluation_case_id,
    _load_authenticated_chat_inspection,
    _observed_source_ids,
    _inspection_has_terminal_chat_turn,
    _hybrid_chat_ledger_is_coherent,
    _provider_safe_operation_name,
    _record_chat_inspection,
    _recent_operation_evidence,
    _require_secret_free_evidence,
    _save_profile_exact,
    _terminal_assistant_content,
    _restart_runtime,
    _validate_chat_prompts,
    _wait_for_runtime_generation,
    _wait_ready,
    _wait_for_unique_locator,
    _wait_for_sandbox_clarification,
)


class _ReadyResponse:
    def __init__(self, status: int) -> None:
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None


def test_chat_abort_is_expected_only_for_the_same_completed_200_request() -> None:
    item = {
        "method": "POST",
        "path": "/api/routedeck/chat",
        "failure": "net::ERR_ABORTED",
    }

    assert is_expected_completed_chat_abort(item, response_completed=True)
    assert not is_expected_completed_chat_abort(item, response_completed=False)
    assert not is_expected_completed_chat_abort(
        {**item, "path": "/api/routedeck/dispatch"},
        response_completed=True,
    )
    assert not is_expected_completed_chat_abort(
        {**item, "failure": "net::ERR_CONNECTION_RESET"},
        response_completed=True,
    )


def test_horizontal_pass_fails_on_every_unexpected_request_failure() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )
    passed = source[source.index("    passed = ("):source.index("    result = {")]

    assert 'and not diagnostics["requestFailures"]' in passed


def test_only_api_connection_interruptions_after_production_restart_are_expected() -> None:
    before = {"type": "error", "text": "unrelated", "locationPath": "/api/agents"}
    restart_console = {
        "type": "error",
        "text": "Failed to load resource: net::ERR_CONNECTION_REFUSED",
        "locationPath": "/api/agents",
    }
    restart_request = {
        "method": "GET",
        "path": "/api/agents",
        "failure": "net::ERR_CONNECTION_REFUSED",
    }
    unrelated_request = {
        "method": "POST",
        "path": "/api/agents",
        "failure": "net::ERR_CONNECTION_REFUSED",
    }
    diagnostics = {
        "consoleErrors": [before, restart_console],
        "requestFailures": [restart_request, unrelated_request],
        "expectedRestartInterruptions": [],
    }

    _classify_expected_restart_interruptions(
        diagnostics,
        console_from=1,
        request_from=0,
    )

    assert diagnostics["consoleErrors"] == [before]
    assert diagnostics["requestFailures"] == [unrelated_request]
    assert diagnostics["expectedRestartInterruptions"] == [restart_console, restart_request]


def test_only_exact_headless_graph_capture_warning_is_classified_expected() -> None:
    expected = {
        "page": "horizontal",
        "type": "warning",
        "text": "[.WebGL-0x123]GL Driver Message: GPU stall due to ReadPixels",
        "locationPath": "/sources/api",
    }
    unrelated = {**expected, "text": "API setup warning"}
    diagnostics = {
        "consoleErrors": [expected, unrelated],
        "expectedConsoleWarnings": [],
    }

    _classify_expected_graph_capture_warnings(diagnostics)

    assert diagnostics["expectedConsoleWarnings"] == [expected]
    assert diagnostics["consoleErrors"] == [unrelated]


def test_hybrid_ledger_allows_a_read_operation_for_distinct_user_requests_only() -> None:
    conversation_id = "conversation-one"
    events = [
        {
            "conversationId": conversation_id,
            "message": "Inspect the uploaded definition.",
            "operationId": "sources.inspect_current_api",
        },
        {
            "conversationId": conversation_id,
            "message": "Classify the collection endpoints.",
            "operationId": "sources.inspect_current_api",
        },
        {
            "conversationId": conversation_id,
            "message": "Classify the collection endpoints.",
            "operationId": "sources.save_api_operation_curation",
        },
    ]

    assert _hybrid_chat_ledger_is_coherent(
        events,
        expected_conversation_id=conversation_id,
    )
    assert not _hybrid_chat_ledger_is_coherent(
        [*events, dict(events[-1])],
        expected_conversation_id=conversation_id,
    )
    assert not _hybrid_chat_ledger_is_coherent(
        [*events[:-1], {**events[-1], "conversationId": "conversation-two"}],
        expected_conversation_id=conversation_id,
    )


def test_ready_barrier_resets_after_a_transient_unready_probe(monkeypatch) -> None:
    statuses = iter((200, 503, 200, 200, 200))
    observed: list[int] = []

    def urlopen(_target: str, *, timeout: int):
        assert timeout == 5
        status = next(statuses)
        observed.append(status)
        return _ReadyResponse(status)

    monkeypatch.setattr(horizontal_journey, "urlopen", urlopen)
    _wait_ready(
        "http://127.0.0.1:8099",
        timeout_seconds=1,
        poll_seconds=0,
        required_ready_successes=3,
    )

    assert observed == [200, 503, 200, 200, 200]


def test_runtime_generation_barrier_rejects_old_process_readiness(monkeypatch) -> None:
    generations = {
        "backend": iter(("backend-old", "backend-new", "backend-new", "backend-new")),
        "source-worker": iter(("worker-old", "worker-new", "worker-new", "worker-new")),
    }
    readiness_calls: list[str] = []

    monkeypatch.setattr(
        horizontal_journey,
        "_compose_service_generation",
        lambda service: next(generations[service]),
    )

    def urlopen(target: str, *, timeout: int):
        readiness_calls.append(target)
        assert timeout == 5
        return _ReadyResponse(200)

    monkeypatch.setattr(horizontal_journey, "urlopen", urlopen)
    _wait_for_runtime_generation(
        "http://127.0.0.1:8099",
        previous_backend_generation="backend-old",
        previous_worker_generation="worker-old",
        timeout_seconds=1,
        poll_seconds=0,
        required_ready_successes=3,
    )

    assert readiness_calls == [
        "http://127.0.0.1:8099/readyz",
        "http://127.0.0.1:8099/readyz",
        "http://127.0.0.1:8099/readyz",
    ]


def test_restart_starts_backend_and_worker_together_before_generation_barrier(
    monkeypatch,
) -> None:
    generations = iter(("backend-before", "worker-before"))
    commands: list[list[str]] = []
    barrier: list[tuple[str, str, str]] = []

    monkeypatch.setattr(
        horizontal_journey,
        "_compose_service_generation",
        lambda _service: next(generations),
    )

    def run(command, **_kwargs):
        commands.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(horizontal_journey.subprocess, "run", run)
    monkeypatch.setattr(
        horizontal_journey,
        "_wait_for_runtime_generation",
        lambda base_url, *, previous_backend_generation, previous_worker_generation: barrier.append(
            (base_url, previous_backend_generation, previous_worker_generation)
        ),
    )

    _restart_runtime("http://127.0.0.1:8099")

    assert commands == [
        ["docker", "compose", "stop", "--timeout", "60", "backend", "source-worker"],
        ["docker", "compose", "up", "-d", "backend", "source-worker"],
    ]
    assert barrier == [(
        "http://127.0.0.1:8099",
        "backend-before",
        "worker-before",
    )]


def test_horizontal_recorder_expected_count_matches_the_real_mode_branches() -> None:
    assert EXPECTED_CHECKS == 39


def test_horizontal_recorder_retains_the_complete_late_delivery_lifecycle() -> None:
    source = Path("scripts/run_horizontal_product_journey.py").read_text(encoding="utf-8")
    assert 'name="Create hosted channel", exact=True' in source
    assert 'name="Create channel", exact=True' not in source
    assert '"section.channels-home li[data-status=\'ready\'] > div > span"' in source
    assert '"section.channels-home li[data-status=\'ready\'] > span"' not in source
    assert '"Hosted Agent enabled"' not in source
    assert source.count('"Public and available", exact=True') >= 3
    assert source.count('"Active deployment", exact=True') >= 2
    assert source.count('_feature_surface(page, "Channels and Deployment").get_by_role(') >= 2
    assert "Ask the deployed Agent a question." not in source
    assert "Ask a question and continue the same request when the Agent needs one more detail." in source
    assert source.count('"[data-public-agent-application]"') >= 3
    assert 'page.locator("main.public-agent")' not in source
    assert '"textbox", name="Message the assistant", exact=True' in source
    assert '"button", name="Send message", exact=True' in source
    ordered_markers = (
        'CHAT_PROMPTS["request_second_deployment"]',
        'CHAT_PROMPTS["request_rollback"]',
        'CHAT_PROMPTS["request_pause"]',
        'CHAT_PROMPTS["request_resume"]',
        'CHAT_PROMPTS["enter_operations"]',
        'CHAT_PROMPTS["promote_interaction"]',
    )
    offsets = tuple(source.index(marker) for marker in ordered_markers)
    assert offsets == tuple(sorted(offsets))
    assert 'name="Approve hosted Agent rollback"' in source
    assert 'name="Approve hosted Web availability change"' in source
    assert (
        '"Operations durably promotes the exact successful deployed interaction into Evaluation"'
        in source
    )
    assert 'CHAT_PROMPTS["start_build_runtime"]' in source
    assert '"builder.run"' in source
    assert '"Add a case from a successful Sandbox interaction", exact=True' in source
    assert 'name="Add evaluation case", exact=True' in source
    assert '".evaluation-set-card", has_text="Baseline"' in source
    assert 'CHAT_PROMPTS["run_generated_evaluation"]' in source
    assert 'name="Run generated case", exact=True' in source
    assert 'get_by_text("Draft coverage", exact=True)' in source
    assert "generated_status = await _wait_for_evaluation_terminal(generated_case)" in source
    assert '"eligibleSetCount": await eligible_results.count()' in source


def test_contract_review_id_comes_from_the_exact_visible_review_surface() -> None:
    class ReviewSurface:
        async def get_attribute(self, name: str):
            assert name == "aria-labelledby"
            return "contract-review-review_exact-123"

    assert asyncio.run(_contract_review_id(ReviewSurface())) == "review_exact-123"

    class WrongSurface:
        async def get_attribute(self, name: str):
            assert name == "aria-labelledby"
            return "contract-review-proposal-only"

    with pytest.raises(RuntimeError, match="exact contract review ID"):
        asyncio.run(_contract_review_id(WrongSurface()))


def test_unique_locator_waits_for_the_authoritative_refresh_without_accepting_duplicates() -> None:
    class DelayedLocator:
        def __init__(self) -> None:
            self.counts = iter((0, 0, 1))
            self.waited = False

        async def count(self) -> int:
            return next(self.counts)

        async def wait_for(self, **kwargs) -> None:
            assert kwargs == {"state": "visible", "timeout": 1_000}
            self.waited = True

    delayed = DelayedLocator()
    asyncio.run(_wait_for_unique_locator(delayed, label="hosted channel", timeout_ms=1_000))
    assert delayed.waited is True

    class DuplicateLocator:
        async def count(self) -> int:
            return 2

    with pytest.raises(RuntimeError, match="was not unique"):
        asyncio.run(_wait_for_unique_locator(DuplicateLocator(), label="hosted channel", timeout_ms=100))


def test_chat_verifier_reads_and_records_the_post_turn_inspection_snapshot() -> None:
    inspection = {
        "recent_operations": [
            {
                "event_id": "event-7",
                "cursor": 7,
                "operation_id": "workspace.open_sources",
                "status_code": "ready",
                "session_version": 8,
                "projection_version": 7,
            },
            {
                "event_id": "event-8",
                "cursor": 8,
                "operation_id": "sources.inspect_current_api",
                "status_code": "ready",
                "session_version": 9,
                "projection_version": 8,
            },
        ],
        "agent_context": {
            "snapshot": {"session_version": 9, "projection_version": 8},
            "messages": [
                {
                    "role": "tool",
                    "id": "tool-7",
                    "name": _provider_safe_operation_name("workspace.open_sources"),
                    "status": "success",
                },
                {
                    "role": "tool",
                    "id": "tool-8",
                    "name": _provider_safe_operation_name("sources.inspect_current_api"),
                    "status": "success",
                },
            ],
        },
    }

    class AuthenticatedRequest:
        async def all_headers(self):
            return {
                "authorization": "Bearer in-memory-verifier-token",
                "x-corpus-conversation-id": "conversation-selector-1",
            }

    class AuthenticatedResponse:
        request = AuthenticatedRequest()

    class InspectionResponse:
        ok = True
        status = 200

        async def json(self):
            return inspection

    class RequestContext:
        calls: list[tuple[str, dict[str, object]]] = []

        async def get(self, url: str, **kwargs):
            self.calls.append((url, kwargs))
            return InspectionResponse()

    class Context:
        request = RequestContext()

    class Page:
        context = Context()

    observed = {"sequence": 4, "chatOperations": [], "chatInspectionTools": []}
    trace: list[dict[str, object]] = []

    page = Page()
    snapshot = asyncio.run(_load_authenticated_chat_inspection(
        page,
        AuthenticatedResponse(),
        backend_url="http://127.0.0.1:8099",
    ))
    _record_chat_inspection(snapshot, observed, trace)

    assert page.context.request.calls == [(
        "http://127.0.0.1:8099/api/routedeck/inspect",
        {
            "headers": {
                "Authorization": "Bearer in-memory-verifier-token",
                "X-Corpus-Conversation-ID": "conversation-selector-1",
                "Accept": "application/json",
                "Cache-Control": "no-cache",
            },
            "fail_on_status_code": True,
        },
    )]
    assert [item["operationId"] for item in trace] == [
        "workspace.open_sources",
        "sources.inspect_current_api",
    ]


def test_chat_turn_terminal_boundary_requires_the_exact_new_user_and_terminal_response() -> None:
    before = {
        "agent_context": {
            "snapshot": {"session_version": 4, "interaction_phase": "idle"},
            "messages": [{"id": "old", "role": "ai", "content": "Earlier."}],
        }
    }
    terminal = {
        "agent_context": {
            "snapshot": {"session_version": 7, "interaction_phase": "idle"},
            "messages": [
                {"id": "old", "role": "ai", "content": "Earlier."},
                {"id": "user-new", "role": "human", "content": "Help with my store API."},
                {"id": "tool-new", "role": "tool", "content": ""},
                {"id": "assistant-new", "role": "ai", "content": "The Source workspace is ready."},
            ],
        }
    }

    assert _inspection_has_terminal_chat_turn(
        before, terminal, "Help with my store API."
    )
    streaming = {
        "agent_context": {
            **terminal["agent_context"],
            "snapshot": {"session_version": 7, "interaction_phase": "active"},
        }
    }
    wrong_message = {
        "agent_context": {
            **terminal["agent_context"],
            "messages": [
                terminal["agent_context"]["messages"][0],
                {"id": "user-other", "role": "human", "content": "A different request."},
                terminal["agent_context"]["messages"][2],
            ],
        }
    }
    no_terminal_response = {
        "agent_context": {
            **terminal["agent_context"],
            "messages": terminal["agent_context"]["messages"][:2],
        }
    }
    tool_only = {
        "agent_context": {
            **terminal["agent_context"],
            "messages": terminal["agent_context"]["messages"][:3],
        }
    }
    assert not _inspection_has_terminal_chat_turn(
        before, streaming, "Help with my store API."
    )
    assert not _inspection_has_terminal_chat_turn(
        before, wrong_message, "Help with my store API."
    )
    assert not _inspection_has_terminal_chat_turn(
        before, no_terminal_response, "Help with my store API."
    )
    assert not _inspection_has_terminal_chat_turn(
        before, tool_only, "Help with my store API."
    )


def test_chat_turn_boundary_uses_the_exact_visible_attachment_sentence() -> None:
    assert _durable_chat_message("Check this API.", None) == "Check this API."
    assert _durable_chat_message("Check this API.", "medusa-store.yaml") == (
        'Check this API.\n\nI attached the API definition "medusa-store.yaml" '
        "to this conversation."
    )
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )
    upload = source[
        source.index("async def _chat_upload_source"):
        source.index("async def _chat_dispatch")
    ]
    assert "attachment_name=source_path.stem" in upload
    assert "attachment_name=source_path.name" not in upload


def test_chat_operation_boundary_accepts_one_exact_dispatch() -> None:
    trace = [
        {"sequence": 4, "path": "/api/routedeck/session"},
        {
            "sequence": 5,
            "event": "chat_operation",
            "operationId": "builder.assemble",
            "disposition": "completed",
        },
    ]

    observed = asyncio.run(
        _chat_operation_after(trace, 4, "builder.assemble")
    )

    assert observed["sequence"] == 5


def test_chat_operation_boundary_rejects_an_unrequested_mutation() -> None:
    trace = [
        {
            "sequence": 8,
            "event": "chat_operation",
            "operationId": "agents.create_agent",
        }
    ]

    with pytest.raises(RuntimeError, match="unexpected operation"):
        asyncio.run(_chat_operations_after(trace, 7, ("sandbox.start",)))


def test_chat_multi_operation_boundary_allows_autonomous_safe_navigation() -> None:
    trace = [
        {
            "sequence": 8,
            "event": "chat_operation",
            "operationId": "workspace.open_sources",
        },
        {
            "sequence": 9,
            "event": "chat_operation",
            "operationId": "sources.inspect_current_api",
        },
        {
            "sequence": 10,
            "event": "chat_operation",
            "operationId": "sources.open_api_creation",
        },
    ]

    observed = asyncio.run(
        _chat_operations_after(
            trace,
            7,
            ("workspace.open_sources", "sources.inspect_current_api"),
        )
    )

    assert [item["operationId"] for item in observed] == [
        "workspace.open_sources",
        "sources.inspect_current_api",
        "sources.open_api_creation",
    ]


def test_chat_multi_operation_boundary_requires_model_chosen_order() -> None:
    trace = [
        {
            "sequence": 8,
            "event": "chat_operation",
            "operationId": "agents.open_create",
        },
        {
            "sequence": 9,
            "event": "chat_operation",
            "operationId": "workspace.open_agents",
        },
    ]

    with pytest.raises(RuntimeError, match="invalid order"):
        asyncio.run(
            _chat_operations_after(
                trace,
                7,
                ("workspace.open_agents", "agents.open_create"),
            )
        )


@pytest.mark.parametrize(
    "navigation_operation",
    ["agents.return_from_source", "agents.choose_existing_for_source"],
)
def test_chat_source_attachment_accepts_either_exact_legal_return_route(
    navigation_operation: str,
) -> None:
    trace = [
        {
            "sequence": 8,
            "event": "chat_operation",
            "operationId": navigation_operation,
            "disposition": "completed",
        },
        {
            "sequence": 9,
            "event": "chat_operation",
            "operationId": "agents.attach_source",
            "disposition": "completed",
        },
    ]

    observed = asyncio.run(
        _chat_operations_after(
            trace,
            7,
            (
                "agents.return_from_source",
                "agents.attach_source",
                "agents.choose_existing_for_source",
            ),
            expected_operation_sequences=(
                ("agents.return_from_source", "agents.attach_source"),
                ("agents.choose_existing_for_source", "agents.attach_source"),
            ),
            allow_blocked_correction=False,
        )
    )

    assert [item["operationId"] for item in observed] == [
        navigation_operation,
        "agents.attach_source",
    ]


def test_chat_source_attachment_rejects_a_blocked_attach_attempt() -> None:
    trace = [
        {
            "sequence": 8,
            "event": "chat_operation",
            "operationId": "agents.choose_existing_for_source",
            "disposition": "completed",
        },
        {
            "sequence": 9,
            "event": "chat_operation",
            "operationId": "agents.attach_source",
            "disposition": "blocked",
        },
    ]

    with pytest.raises(RuntimeError, match="blocked operation"):
        asyncio.run(
            _chat_operations_after(
                trace,
                7,
                (
                    "agents.return_from_source",
                    "agents.attach_source",
                    "agents.choose_existing_for_source",
                ),
                expected_operation_sequences=(
                    ("agents.return_from_source", "agents.attach_source"),
                    ("agents.choose_existing_for_source", "agents.attach_source"),
                ),
                allow_blocked_correction=False,
            )
        )


def test_chat_boundary_retains_one_blocked_self_correction_without_claiming_duplicate_mutation() -> None:
    trace = [
        {
            "sequence": 8,
            "event": "chat_operation",
            "operationId": "sources.save_api_operation_curation",
            "disposition": "blocked",
        },
        {
            "sequence": 9,
            "event": "chat_operation",
            "operationId": "sources.save_api_operation_curation",
            "disposition": "completed",
            "outcome": "saved",
        },
    ]

    observed = asyncio.run(
        _chat_operations_after(
            trace,
            7,
            ("sources.save_api_operation_curation",),
        )
    )

    assert [(item["sequence"], item["disposition"]) for item in observed] == [
        (9, "completed")
    ]


@pytest.mark.parametrize(
    "dispositions",
    [
        ("completed", "completed"),
        ("blocked", "blocked", "completed"),
        ("completed", "blocked"),
    ],
)
def test_chat_boundary_rejects_repeated_effect_or_repeated_blocked_attempts(
    dispositions: tuple[str, ...],
) -> None:
    trace = [
        {
            "sequence": 8 + index,
            "event": "chat_operation",
            "operationId": "sources.save_api_operation_curation",
            "disposition": disposition,
        }
        for index, disposition in enumerate(dispositions)
    ]

    with pytest.raises(RuntimeError, match="repeated an operation"):
        asyncio.run(
            _chat_operations_after(
                trace,
                7,
                ("sources.save_api_operation_curation",),
            )
        )


def test_hybrid_identity_helpers_use_exact_observed_product_records() -> None:
    observations = {
        "designs": [{"build_request": {"id": "build-request-1"}}],
        "evaluations": [
            {"evaluation_sets": [{"cases": [{"id": "case-1"}]}]}
        ],
        "channels": [{"channels": [{"id": "channel-1"}]}],
    }

    async def collect() -> tuple[str, str, str]:
        return (
            await _latest_build_request_id(observations),
            await _latest_evaluation_case_id(observations),
            await _latest_channel_id(observations),
        )

    assert asyncio.run(collect()) == (
        "build-request-1",
        "case-1",
        "channel-1",
    )


def test_horizontal_evidence_scan_removes_the_run_directory_on_leak(tmp_path) -> None:
    run = tmp_path / "run-identity"
    run.mkdir()
    (run / "primary.webm").write_bytes(b"safe-prefix credential-canary safe-suffix")

    with pytest.raises(RuntimeError, match="forbidden input"):
        _require_secret_free_evidence(run, ("credential-canary",))

    assert not run.exists()


def test_chat_operation_evidence_uses_sanitized_routedeck_tool_results() -> None:
    payload = {
        "invocation_traces": {
            "traces": [{
                "model_boundary_request": {
                    "value": {
                        "messages": [{
                            "type": "tool",
                            "content": (
                                '{"type":"routedeck_operation_result",'
                                '"operation_id":"workspace.open_sources",'
                                '"disposition":"completed","outcome":"opened",'
                                '"session_version":9,"projection_version":8}'
                            ),
                        }]
                    }
                }
            }]
        }
    }

    assert _chat_operation_evidence(payload) == [{
        "operationId": "workspace.open_sources",
        "disposition": "completed",
        "outcome": "opened",
        "sessionVersion": 9,
        "projectionVersion": 8,
        "source": "agent",
    }]


def test_chat_operation_evidence_accepts_structured_tool_artifacts() -> None:
    payload = {
        "invocation_traces": {
            "traces": [{
                "model_boundary_request": {
                    "value": {
                        "messages": [{
                            "type": "tool",
                            "content": [{"type": "text", "text": "completed"}],
                            "artifact": {
                                "type": "routedeck_operation_result",
                                "operation_id": "workspace.open_sources",
                                "disposition": "completed",
                                "outcome": "opened",
                                "session_version": 12,
                                "projection_version": 11,
                            },
                        }]
                    }
                }
            }]
        }
    }

    assert _chat_operation_evidence(payload) == [{
        "operationId": "workspace.open_sources",
        "disposition": "completed",
        "outcome": "opened",
        "sessionVersion": 12,
        "projectionVersion": 11,
        "source": "agent",
    }]


def test_chat_operation_evidence_prefers_durable_reconstructed_tool_turns() -> None:
    payload = {
        "agent_context": {
            "snapshot": {
                "session_version": 15,
                "projection_version": 14,
            },
            "messages": [
                {"role": "human", "content": "A normal user request"},
                {
                    "id": "tool-turn-1",
                    "role": "tool",
                    "name": _provider_safe_operation_name(
                        "workspace.open_sources"
                    ),
                    "status": "success",
                    "content": "The Sources workspace is ready.",
                },
            ],
        },
        "invocation_traces": {"traces": []},
    }

    assert _chat_operation_evidence(payload) == [{
        "operationId": "workspace.open_sources",
        "evidenceId": "tool-turn-1",
        "disposition": "completed",
        "outcome": None,
        "sessionVersion": None,
        "projectionVersion": None,
        "source": "agent",
    }]


def test_chat_provider_tool_name_is_not_present_in_the_user_prompt() -> None:
    provider_name = _provider_safe_operation_name("workspace.open_sources")

    assert provider_name == "rd_workspace_open_sources_a65325eaba42"
    assert all(provider_name not in prompt for prompt in CHAT_PROMPTS.values())
    assert all("workspace.open_sources" not in prompt for prompt in CHAT_PROMPTS.values())


def test_inspection_recent_operations_are_unattributed_session_evidence() -> None:
    operations = _recent_operation_evidence({
        "recent_operations": [
            {
                "event_id": "event-7", "cursor": 7,
                "operation_id": "workspace.open_sources", "status_code": "ready",
                "session_version": 8, "projection_version": 7,
            },
            {
                "event_id": "event-8", "cursor": 8,
                "operation_id": "sources.inspect_current_api", "status_code": "ready",
                "session_version": 9, "projection_version": 8,
            },
        ]
    })

    assert [item["operationId"] for item in operations] == [
        "workspace.open_sources",
        "sources.inspect_current_api",
    ]


def test_surface_session_event_is_not_counted_as_model_selected_chat_evidence() -> None:
    inspection = {
        "recent_operations": [{
            "event_id": "event-surface",
            "cursor": 10,
            "operation_id": "agents.open_source_creation",
            "status_code": "ready",
            "session_version": 11,
            "projection_version": 10,
        }],
        "agent_context": {"messages": []},
        "invocation_traces": {"traces": []},
    }

    assert _chat_operation_evidence(inspection) == []


def test_durable_recent_operations_supersede_duplicate_tool_and_trace_views() -> None:
    inspection = {
        "recent_operations": [
            {
                "event_id": "event-7", "cursor": 7,
                "operation_id": "workspace.open_sources", "status_code": "ready",
                "session_version": 8, "projection_version": 7,
            },
            {
                "event_id": "event-8", "cursor": 8,
                "operation_id": "sources.inspect_current_api", "status_code": "ready",
                "session_version": 9, "projection_version": 8,
            },
        ],
        "agent_context": {
            "snapshot": {"session_version": 10, "projection_version": 9},
            "messages": [
                {
                    "role": "tool", "id": "tool-7",
                    "name": _provider_safe_operation_name("workspace.open_sources"),
                    "status": "success",
                },
                {
                    "role": "tool", "id": "tool-8",
                    "name": _provider_safe_operation_name("sources.inspect_current_api"),
                    "status": "success",
                },
            ],
        },
        "invocation_traces": {
            "traces": [{
                "provider_result": {
                    "value": {
                        "type": "routedeck_operation_result",
                        "operation_id": "workspace.open_sources",
                        "disposition": "completed",
                        "session_version": 8,
                        "projection_version": 7,
                    }
                }
            }]
        },
    }

    operations = _chat_operation_evidence(inspection)

    assert [(item["operationId"], item["evidenceId"]) for item in operations] == [
        ("workspace.open_sources", "event-7"),
        ("sources.inspect_current_api", "tool-8"),
    ]
    assert all(item["disposition"] == "completed" for item in operations)
    assert all(item["source"] == "agent" for item in operations)


def test_chat_operation_evidence_does_not_attribute_an_older_surface_commit_to_chat() -> None:
    inspection = {
        "recent_operations": [
            {
                "event_id": "surface-open",
                "cursor": 7,
                "operation_id": "agents.open_create",
                "status_code": "ready",
                "session_version": 8,
                "projection_version": 7,
            },
            {
                "event_id": "agent-open",
                "cursor": 10,
                "operation_id": "agents.open_create",
                "status_code": "ready",
                "session_version": 11,
                "projection_version": 10,
            },
        ],
        "agent_context": {"messages": []},
        "invocation_traces": {
            "traces": [{
                "provider_result": {
                    "value": {
                        "type": "routedeck_operation_result",
                        "operation_id": "agents.open_create",
                        "disposition": "completed",
                        "outcome": "opened",
                        "session_version": 11,
                        "projection_version": 10,
                    }
                }
            }]
        },
    }

    assert _chat_operation_evidence(inspection) == [{
        "operationId": "agents.open_create",
        "evidenceId": "agent-open",
        "eventCursor": 10,
        "disposition": "completed",
        "outcome": "opened",
        "sessionVersion": 11,
        "projectionVersion": 10,
        "source": "agent",
    }]


def test_chat_operation_evidence_keeps_sole_mismatched_surface_candidate_trace_only() -> None:
    inspection = {
        "recent_operations": [{
            "event_id": "surface-only",
            "cursor": 7,
            "operation_id": "agents.open_create",
            "status_code": "ready",
            "session_version": 8,
            "projection_version": 7,
        }],
        "agent_context": {"messages": []},
        "invocation_traces": {"traces": [{
            "provider_result": {"value": {
                "type": "routedeck_operation_result",
                "operation_id": "agents.open_create",
                "disposition": "completed",
                "outcome": "opened",
                "session_version": 11,
                "projection_version": 10,
            }}
        }]},
    }

    assert _chat_operation_evidence(inspection) == [{
        "operationId": "agents.open_create",
        "disposition": "completed",
        "outcome": "opened",
        "sessionVersion": 11,
        "projectionVersion": 10,
        "source": "agent",
    }]


def test_chat_operation_evidence_never_drops_unmatched_model_result_after_exact_match() -> None:
    inspection = {
        "recent_operations": [{
            "event_id": "exact-create",
            "cursor": 9,
            "operation_id": "agents.create_agent",
            "status_code": "ready",
            "session_version": 10,
            "projection_version": 9,
        }],
        "agent_context": {"messages": []},
        "invocation_traces": {"traces": [{
            "provider_result": {"value": [
                {
                    "type": "routedeck_operation_result",
                    "operation_id": "agents.create_agent",
                    "disposition": "completed",
                    "outcome": "created",
                    "session_version": 10,
                    "projection_version": 9,
                },
                {
                    "type": "routedeck_operation_result",
                    "operation_id": "agents.open_create",
                    "disposition": "completed",
                    "outcome": "opened",
                    "session_version": 11,
                    "projection_version": 10,
                },
            ]}
        }]},
    }

    operations = _chat_operation_evidence(inspection)

    assert operations[0]["evidenceId"] == "exact-create"
    assert operations[0]["eventCursor"] == 9
    assert operations[1] == {
        "operationId": "agents.open_create",
        "disposition": "completed",
        "outcome": "opened",
        "sessionVersion": 11,
        "projectionVersion": 10,
        "source": "agent",
    }


def test_durable_recent_operation_uses_exact_model_tool_failure_disposition() -> None:
    inspection = {
        "recent_operations": [{
            "event_id": "event-failed",
            "cursor": 24,
            "operation_id": "sources.save_api_operation_curation",
            "status_code": "api_operation_curation_selection_invalid",
            "session_version": 25,
            "projection_version": 23,
        }],
        "agent_context": {"messages": []},
        "invocation_traces": {
            "traces": [{
                "provider_result": {
                    "value": {
                        "type": "routedeck_operation_result",
                        "operation_id": "sources.save_api_operation_curation",
                        "disposition": "blocked",
                        "outcome": None,
                        "session_version": 25,
                        "projection_version": 23,
                    }
                }
            }]
        },
    }

    assert _chat_operation_evidence(inspection) == [{
        "operationId": "sources.save_api_operation_curation",
        "evidenceId": "event-failed",
        "eventCursor": 24,
        "disposition": "blocked",
        "outcome": None,
        "sessionVersion": 25,
        "projectionVersion": 23,
        "source": "agent",
    }]


def test_durable_review_pending_event_cannot_be_downgraded_by_trace_projection() -> None:
    inspection = {
        "recent_operations": [{
            "event_id": "event-review",
            "cursor": 16,
            "operation_id": "sources.approve_contract_revision",
            "status_code": "review_pending",
            "session_version": 17,
            "projection_version": 16,
        }],
        "agent_context": {"messages": []},
        "invocation_traces": {
            "traces": [{
                "provider_result": {
                    "value": {
                        "type": "routedeck_operation_result",
                        "operation_id": "sources.approve_contract_revision",
                        "disposition": "completed",
                        "session_version": 17,
                        "projection_version": 16,
                    }
                }
            }]
        },
    }

    assert _chat_operation_evidence(inspection)[0]["disposition"] == (
        "requires_review"
    )


def test_current_turn_pending_review_correlates_only_a_new_review_event() -> None:
    prior = {
        "recent_operations": [{
            "event_id": "event-proposal",
            "cursor": 15,
            "operation_id": "sources.propose_contract_revision",
            "status_code": "ready",
            "session_version": 16,
            "projection_version": 15,
        }],
    }
    inspection = {
        "recent_operations": [
            *prior["recent_operations"],
            {
                "event_id": "event-review",
                "cursor": 16,
                "operation_id": "sources.approve_contract_revision",
                "status_code": "review_pending",
                "session_version": 17,
                "projection_version": 16,
            },
        ],
        "agent_context": {
            "messages": [{
                "role": "tool",
                "id": "tool-review",
                "name": _provider_safe_operation_name(
                    "sources.approve_contract_revision"
                ),
                "status": "success",
            }],
        },
        "invocation_traces": {"traces": []},
    }

    assert _chat_operation_evidence(
        inspection,
        prior_inspection=prior,
    ) == [{
        "operationId": "sources.approve_contract_revision",
        "evidenceId": "event-review",
        "eventCursor": 16,
        "disposition": "requires_review",
        "outcome": None,
        "sessionVersion": 17,
        "projectionVersion": 16,
        "source": "agent",
    }]


def test_prior_surface_review_cannot_upgrade_a_current_trace_only_tool_turn() -> None:
    review_event = {
        "event_id": "surface-review",
        "cursor": 16,
        "operation_id": "sources.approve_contract_revision",
        "status_code": "review_pending",
        "session_version": 17,
        "projection_version": 16,
    }
    prior = {"recent_operations": [review_event]}
    inspection = {
        "recent_operations": [review_event],
        "agent_context": {
            "messages": [{
                "role": "tool",
                "id": "tool-review",
                "name": _provider_safe_operation_name(
                    "sources.approve_contract_revision"
                ),
                "status": "success",
            }],
        },
        "invocation_traces": {"traces": []},
    }

    assert _chat_operation_evidence(
        inspection,
        prior_inspection=prior,
    ) == [{
        "operationId": "sources.approve_contract_revision",
        "evidenceId": "tool-review",
        "disposition": "completed",
        "outcome": None,
        "sessionVersion": None,
        "projectionVersion": None,
        "source": "agent",
    }]


def test_new_review_event_correlates_only_the_new_durable_tool_occurrence() -> None:
    prior = {
        "recent_operations": [],
        "agent_context": {
            "messages": [{
                "role": "tool",
                "id": "old-tool-review",
                "name": _provider_safe_operation_name(
                    "sources.approve_contract_revision"
                ),
                "status": "success",
            }],
        },
    }
    inspection = {
        "recent_operations": [{
            "event_id": "new-review-event",
            "cursor": 22,
            "operation_id": "sources.approve_contract_revision",
            "status_code": "review_pending",
            "session_version": 23,
            "projection_version": 22,
        }],
        "agent_context": {
            "messages": [
                *prior["agent_context"]["messages"],
                {
                    "role": "tool",
                    "id": "new-tool-review",
                    "name": _provider_safe_operation_name(
                        "sources.approve_contract_revision"
                    ),
                    "status": "success",
                },
            ],
        },
        "invocation_traces": {"traces": []},
    }

    assert _chat_operation_evidence(
        inspection,
        prior_inspection=prior,
    ) == [
        {
            "operationId": "sources.approve_contract_revision",
            "evidenceId": "old-tool-review",
            "disposition": "completed",
            "outcome": None,
            "sessionVersion": None,
            "projectionVersion": None,
            "source": "agent",
        },
        {
            "operationId": "sources.approve_contract_revision",
            "evidenceId": "new-review-event",
            "eventCursor": 22,
            "disposition": "requires_review",
            "outcome": None,
            "sessionVersion": 23,
            "projectionVersion": 22,
            "source": "agent",
        },
    ]


def test_current_user_suffix_excludes_a_prior_review_finalized_during_next_turn() -> None:
    current_message = "Keep only tags and types."
    prior = {
        "recent_operations": [{
            "event_id": "prior-review-event",
            "cursor": 24,
            "operation_id": "sources.approve_contract_revision",
            "status_code": "review_pending",
            "session_version": 25,
            "projection_version": 24,
        }],
        "agent_context": {
            "messages": [{
                "role": "human",
                "id": "prior-user",
                "content": "Put the correction up for review.",
            }],
        },
    }
    inspection = {
        "recent_operations": [
            *prior["recent_operations"],
            {
                "event_id": "current-curation-event",
                "cursor": 29,
                "operation_id": "sources.save_api_operation_curation",
                "status_code": "ready",
                "session_version": 30,
                "projection_version": 28,
            },
        ],
        "agent_context": {
            "messages": [
                *prior["agent_context"]["messages"],
                {
                    "role": "tool",
                    "id": "late-prior-review-tool",
                    "name": _provider_safe_operation_name(
                        "sources.approve_contract_revision"
                    ),
                    "status": "success",
                },
                {
                    "role": "human",
                    "id": "current-user",
                    "content": current_message,
                },
                {
                    "role": "tool",
                    "id": "current-curation-tool",
                    "name": _provider_safe_operation_name(
                        "sources.save_api_operation_curation"
                    ),
                    "status": "success",
                },
            ],
        },
        "invocation_traces": {"traces": [{
            "model_boundary_request": {"value": {"messages": [{
                "type": "human", "content": current_message,
            }]}},
            "provider_result": {"value": {
                "type": "routedeck_operation_result",
                "operation_id": "sources.save_api_operation_curation",
                "disposition": "completed",
                "outcome": "saved",
                "session_version": 30,
                "projection_version": 28,
            }}
        }]},
    }

    assert _chat_operation_evidence(
        inspection,
        prior_inspection=prior,
        current_user_message=current_message,
    ) == [{
        "operationId": "sources.save_api_operation_curation",
        "evidenceId": "current-curation-event",
        "eventCursor": 29,
        "disposition": "completed",
        "outcome": "saved",
        "sessionVersion": 30,
        "projectionVersion": 28,
        "source": "agent",
    }]


def test_current_user_suffix_does_not_promote_an_unmatched_older_trace() -> None:
    current_message = "Keep only tags and types."
    prior = {
        "agent_context": {"messages": []},
        "invocation_traces": {"traces": [{
            "provider_result": {"value": {
                "type": "routedeck_operation_result",
                "operation_id": "sources.approve_contract_revision",
                "disposition": "completed",
                "outcome": "approved",
                "session_version": 25,
                "projection_version": 24,
            }},
        }]},
    }
    inspection = {
        "recent_operations": [{
            "event_id": "current-curation-event",
            "cursor": 29,
            "operation_id": "sources.save_api_operation_curation",
            "status_code": "ready",
            "session_version": 30,
            "projection_version": 28,
        }],
        "agent_context": {"messages": [
            {"role": "human", "id": "current-user", "content": current_message},
            {
                "role": "tool",
                "id": "current-curation-tool",
                "name": _provider_safe_operation_name(
                    "sources.save_api_operation_curation"
                ),
                "status": "success",
            },
        ]},
        "invocation_traces": {"traces": [
            {
                "model_boundary_request": {"value": {"messages": [{
                    "type": "human", "content": current_message,
                }]}},
                "provider_result": {"value": {
                    "type": "routedeck_operation_result",
                    "operation_id": "sources.save_api_operation_curation",
                    "disposition": "completed",
                    "outcome": "saved",
                    "session_version": 30,
                    "projection_version": 28,
                }},
            },
            *prior["invocation_traces"]["traces"],
        ]},
    }

    operations = _chat_operation_evidence(
        inspection,
        prior_inspection=prior,
        current_user_message=current_message,
    )

    assert [item["operationId"] for item in operations] == [
        "sources.save_api_operation_curation"
    ]
    assert operations[0]["evidenceId"] == "current-curation-event"


def test_current_user_suffix_accepts_only_declared_trace_retention_rotation() -> None:
    current_message = "Keep only tags and types."
    old_traces = [
        {"provider_result": {"value": {"marker": marker}}}
        for marker in ("newest-old", "middle-old", "dropped-old")
    ]
    current_trace = {
        "model_boundary_request": {"value": {"messages": [{
            "type": "human", "content": current_message,
        }]}},
        "provider_result": {"value": {
            "type": "routedeck_operation_result",
            "operation_id": "sources.save_api_operation_curation",
            "disposition": "completed",
            "outcome": "saved",
            "session_version": 30,
            "projection_version": 28,
        }},
    }
    prior = {
        "agent_context": {"messages": []},
        "invocation_traces": {
            "retention_per_session": 3,
            "traces": old_traces,
        },
    }
    inspection = {
        "recent_operations": [{
            "event_id": "current-curation-event",
            "cursor": 29,
            "operation_id": "sources.save_api_operation_curation",
            "status_code": "ready",
            "session_version": 30,
            "projection_version": 28,
        }],
        "agent_context": {"messages": [
            {"role": "human", "content": current_message},
            {
                "role": "tool",
                "id": "current-curation-tool",
                "name": _provider_safe_operation_name(
                    "sources.save_api_operation_curation"
                ),
                "status": "success",
            },
        ]},
        "invocation_traces": {
            "retention_per_session": 3,
            "traces": [current_trace, *old_traces[:2]],
        },
    }

    operations = _chat_operation_evidence(
        inspection,
        prior_inspection=prior,
        current_user_message=current_message,
    )

    assert len(operations) == 1
    assert operations[0]["operationId"] == "sources.save_api_operation_curation"
    assert operations[0]["outcome"] == "saved"


def test_current_user_suffix_accepts_rotation_when_pre_turn_history_was_one_below_bound() -> None:
    current_message = "Run the private trial."
    retained_prior = [
        {"provider_result": {"value": {"marker": f"prior-{index}"}}}
        for index in range(19)
    ]
    current_traces = [
        {
            "model_boundary_request": {"value": {"messages": [{
                "type": "human", "content": current_message,
            }]}},
            "provider_result": {"value": {
                "type": "routedeck_operation_result",
                "operation_id": "sandbox.start",
                "disposition": "completed",
                "outcome": "started",
                "session_version": 40,
                "projection_version": 38,
            }},
        },
        {"provider_result": {"value": {"marker": "current-first"}}},
        *retained_prior[:18],
    ]
    prior = {
        "agent_context": {"messages": []},
        "invocation_traces": {
            "retention_per_session": 20,
            "traces": retained_prior,
        },
    }
    inspection = {
        "recent_operations": [{
            "event_id": "sandbox-current-event",
            "cursor": 39,
            "operation_id": "sandbox.start",
            "status_code": "ready",
            "session_version": 40,
            "projection_version": 38,
        }],
        "agent_context": {"messages": [
            {"role": "human", "content": current_message},
            {
                "role": "tool",
                "id": "sandbox-current-tool",
                "name": _provider_safe_operation_name("sandbox.start"),
                "status": "success",
            },
        ]},
        "invocation_traces": {
            "retention_per_session": 20,
            "traces": current_traces,
        },
    }

    operations = _chat_operation_evidence(
        inspection,
        prior_inspection=prior,
        current_user_message=current_message,
    )

    assert [item["operationId"] for item in operations] == ["sandbox.start"]
    assert operations[0]["evidenceId"] == "sandbox-current-event"


def test_current_user_suffix_excludes_same_operation_from_older_trace_history() -> None:
    current_message = "Approve that corrected contract."
    prior = {
        "agent_context": {"messages": []},
        "invocation_traces": {"traces": []},
    }
    inspection = {
        "recent_operations": [{
            "event_id": "current-review-event",
            "cursor": 30,
            "operation_id": "sources.approve_contract_revision",
            "status_code": "review_pending",
            "session_version": 30,
            "projection_version": 29,
        }],
        "agent_context": {"messages": [
            {"role": "human", "content": current_message},
            {
                "role": "tool",
                "id": "current-review-tool",
                "name": _provider_safe_operation_name(
                    "sources.approve_contract_revision"
                ),
                "status": "success",
            },
        ]},
        "invocation_traces": {"traces": [{
            "model_boundary_request": {"value": {"messages": [
                {"type": "human", "content": "Approve the prior contract."},
                {
                    "type": "tool",
                    "content": {
                        "type": "routedeck_operation_result",
                        "operation_id": "sources.approve_contract_revision",
                        "disposition": "completed",
                        "outcome": "approved",
                        "session_version": 25,
                        "projection_version": 24,
                    },
                },
                {"type": "human", "content": current_message},
            ]}},
            "provider_result": {"value": {
                "type": "routedeck_operation_result",
                "operation_id": "sources.approve_contract_revision",
                "disposition": "requires_review",
                "outcome": None,
                "session_version": 30,
                "projection_version": 29,
            }},
        }]},
    }

    assert _chat_operation_evidence(
        inspection,
        prior_inspection=prior,
        current_user_message=current_message,
    ) == [{
        "operationId": "sources.approve_contract_revision",
        "evidenceId": "current-review-event",
        "eventCursor": 30,
        "disposition": "requires_review",
        "outcome": None,
        "sessionVersion": 30,
        "projectionVersion": 29,
        "source": "agent",
    }]


def test_current_user_suffix_keeps_two_current_same_operation_occurrences() -> None:
    current_message = "Save that classification twice."

    def result(session_version: int, projection_version: int) -> dict[str, object]:
        return {
            "type": "routedeck_operation_result",
            "operation_id": "sources.save_api_operation_curation",
            "disposition": "completed",
            "outcome": "saved",
            "session_version": session_version,
            "projection_version": projection_version,
        }

    first = result(30, 28)
    second = result(31, 29)
    prior = {
        "agent_context": {"messages": []},
        "invocation_traces": {"traces": []},
    }
    inspection = {
        "recent_operations": [
            {
                "event_id": "curation-event-1",
                "cursor": 29,
                "operation_id": "sources.save_api_operation_curation",
                "status_code": "ready",
                "session_version": 30,
                "projection_version": 28,
            },
            {
                "event_id": "curation-event-2",
                "cursor": 30,
                "operation_id": "sources.save_api_operation_curation",
                "status_code": "ready",
                "session_version": 31,
                "projection_version": 29,
            },
        ],
        "agent_context": {"messages": [
            {"role": "human", "content": current_message},
            {
                "role": "tool",
                "id": "curation-tool-1",
                "name": _provider_safe_operation_name(
                    "sources.save_api_operation_curation"
                ),
                "status": "success",
            },
            {
                "role": "tool",
                "id": "curation-tool-2",
                "name": _provider_safe_operation_name(
                    "sources.save_api_operation_curation"
                ),
                "status": "success",
            },
        ]},
        "invocation_traces": {"traces": [
            {
                "model_boundary_request": {"value": {"messages": [
                    {"type": "human", "content": current_message},
                    {"type": "tool", "artifact": first},
                    {"type": "tool", "artifact": second},
                ]}},
            },
            {
                "model_boundary_request": {"value": {"messages": [
                    {"type": "human", "content": current_message},
                    {"type": "tool", "artifact": first},
                ]}},
            },
        ]},
    }

    operations = _chat_operation_evidence(
        inspection,
        prior_inspection=prior,
        current_user_message=current_message,
    )

    assert [item["evidenceId"] for item in operations] == [
        "curation-event-1",
        "curation-event-2",
    ]
    assert [item["sessionVersion"] for item in operations] == [30, 31]


def test_chat_inspection_diagnostic_retains_shape_without_content_or_arguments() -> None:
    payload = {
        "agent_context": {
            "messages": [{
                "id": "tool-turn-2",
                "role": "tool",
                "name": "rd_sources_inspect_current_api_deadbeef0000",
                "status": "success",
                "content": "must not be retained",
                "arguments": {"source_id": "must not be retained"},
            }]
        }
    }

    assert _chat_inspection_tool_shapes(payload) == [{
        "evidenceId": "tool-turn-2",
        "providerSafeName": "rd_sources_inspect_current_api_deadbeef0000",
        "status": "success",
    }]


def test_chat_evidence_uses_short_ordinary_intent_without_spoonfeeding() -> None:
    _validate_chat_prompts()

    assert CHAT_PROMPTS["setup_from_file"] == (
        "Use this file please. Also set up the agent for me."
    )
    assert CHAT_PROMPTS["choose_new_agent"] == "Create a new one."
    assert CHAT_PROMPTS["create_agent"] == (
        "It is a shopping assistant that finds products and adds a chosen product to a cart only after approval."
    )
    assert CHAT_PROMPTS["resume_api"] == (
        "Continue with the store API we just added and show me its analyzed structure."
    )
    assert CHAT_PROMPTS["curate_api"] == (
        "Keep product search, cart creation, and adding an item to a cart. "
        "Exclude every other API action."
    )
    assert CHAT_PROMPTS["prepare_api_update"] == (
        "The API analysis is finished. Prepare the safest API correction for me to review, but do not apply it yet."
    )
    assert CHAT_PROMPTS["accept_api_update"] == (
        "That API correction looks right. Apply it, and stay with this API because I still need to choose what it may access."
    )
    assert CHAT_PROMPTS["request_build"] == (
        "Save this approved design as the version I want built next."
    )
    assert CHAT_PROMPTS["assemble_build"] == (
        "Create the runnable build from that approved design and its store access."
    )
    assert CHAT_PROMPTS["start_private_trial"] == (
        'Run a private trial that finds products matching "Medusa T-Shirt".'
    )
    assert "configure_connection" not in CHAT_PROMPTS
    assert CHAT_OPERATION_SAFETY_CLASSES["sources.inspect_current_api"] == "state_selection"
    assert CHAT_OPERATION_SAFETY_CLASSES["sources.prepare_routed_api_test"] == "state_selection"
    assert "workspace.open_sources" in CHAT_EVIDENCE_OPERATION_IDS
    assert "sources.prepare_routed_api_test" in CHAT_EVIDENCE_OPERATION_IDS


def test_file_first_chat_requires_real_agent_choice_and_detail_questions() -> None:
    before = {"agent_context": {"messages": [{"role": "human", "content": "earlier"}]}}
    after = {
        "agent_context": {
            "messages": [
                {"role": "human", "content": "earlier"},
                {"role": "human", "content": "setup"},
                {"role": "tool", "content": "accepted"},
                {
                    "role": "assistant",
                    "content": "Would you like to use an existing Agent or create a new Agent?",
                },
            ]
        }
    }

    response = _terminal_assistant_content(before, after, "setup")
    assert _asks_for_agent_choice(response)
    assert _asks_for_agent_details("What should this Agent do, and what are its responsibilities?")
    assert _asks_for_agent_details("What should this agent be responsible for?")
    assert _asks_for_agent_details("What should the new agent's name, description, and instructions be?")
    assert _asks_for_agent_details(
        "What should the new agent's role be? Please provide a short role and what you want it to handle."
    )
    assert not _asks_for_agent_choice("I opened the setup screen.")


def test_sandbox_clarification_gate_rejects_a_terminal_run_instead_of_waiting() -> None:
    class Item:
        def __init__(self, *, visible: bool, status: str | None = None) -> None:
            self.visible = visible
            self.status = status
            self.first = self

        async def is_visible(self) -> bool:
            return self.visible

        async def get_attribute(self, name: str) -> str | None:
            assert name == "data-status"
            return self.status

    waiting = Item(visible=False)
    terminal = Item(visible=True, status="succeeded")

    class Page:
        def locator(self, selector: str) -> Item:
            return waiting if "waiting" in selector else terminal

    with pytest.raises(RuntimeError, match="instead of producing ToolRouter clarification"):
        asyncio.run(_wait_for_sandbox_clarification(Page(), timeout_ms=100))


def test_horizontal_profile_save_uses_a_stable_surface_form_and_real_private_write() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )
    helper = source[
        source.index("async def _save_profile_exact"):
        source.index("async def _chat_operations_after")
    ]

    assert "_save_profile," not in source
    assert "await page.wait_for_timeout(500)" in helper
    assert helper.count("input_value()") >= 3
    assert "form.checkValidity()" in helper
    assert 'request.method == "PUT"' in helper
    assert '"/api/routedeck/private-forms/sources-api-connection"' in helper
    assert "await panel.get_by_text(name, exact=True).wait_for" not in helper
    assert "profiles = await _profiles(observations, ids[\"sourceId\"], minimum_count=1)" in source
    assert callable(_save_profile_exact)
    assert CHAT_PROMPTS["enter_operations"] == (
        "Show me how that public request to this assistant actually ran."
    )
    assert CHAT_PROMPTS["enter_evaluation"] == (
        "Keep that successful trial in the Baseline set as a required easy routing case "
        "called Product search success for future versions."
    )
    assert CHAT_PROMPTS["create_evaluation"] == (
        "Keep that trial in the Baseline set as a required easy routing case called Product "
        "search success for future versions."
    )
    assert CHAT_PROMPTS["enter_delivery"] == (
        "Set up /{slug} as a hosted address called Medusa Shopping, but do not publish it yet."
    )
    assert CHAT_PROMPTS["request_deployment"] == (
        "Put the eligible version on that address. Show me the consequences for approval before anything goes live."
    )
    assert all(len(prompt.split()) <= 28 for prompt in CHAT_PROMPTS.values())
    assert all(
        phrase not in f" {prompt.casefold()} "
        for prompt in CHAT_PROMPTS.values()
        for phrase in CHAT_FORBIDDEN_PHRASES
    )
    assert "leave_api" not in CHAT_PROMPTS
    assert "find_agents" not in CHAT_PROMPTS
    assert "start_agent" not in CHAT_PROMPTS
    assert "continue_agent" not in CHAT_PROMPTS


def test_chat_only_path_begins_file_first_then_collects_agent_intent() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )

    assert source.index('CHAT_PROMPTS["setup_from_file"]') < source.index(
        'CHAT_PROMPTS["choose_new_agent"]'
    ) < source.index('CHAT_PROMPTS["create_agent"]')
    assert '"workspace.open_sources",\n                        "sources.open_api_creation",\n                        "sources.accept_staged_api",\n                        "sources.process_api",' in source
    assert 'CHAT_PROMPTS["choose_new_agent"],\n                    "agents.open_create",' in source
    assert (
        'CHAT_PROMPTS["create_agent"],\n'
        '                    ("agents.create_agent", "agents.attach_source"),'
    ) in source
    assert 'CHAT_PROMPTS["resume_api"],' in source
    assert (
        '"agents.open_attached_source",\n'
        '                        "sources.inspect_current_api",'
    ) in source
    assert '"agents.return_to_workspace",\n                        "workspace.open_sources",' not in source[
        source.index('CHAT_PROMPTS["resume_api"]'):
        source.index('CHAT_PROMPTS["prepare_api_update"]')
    ]
    attach_flow = source[
        source.index('CHAT_PROMPTS["attach_source"]'):
        source.index('safe_trace,', source.index('CHAT_PROMPTS["attach_source"]'))
    ]
    assert 'ChatOperationAlternatives(' in attach_flow
    assert '("agents.return_from_source", "agents.attach_source")' in attach_flow
    assert '"agents.choose_existing_for_source"' in attach_flow
    assert '"agents.attach_source"' in attach_flow
    assert '("agents.open_designer", "designer.propose")' in source
    assert 'ChatOperationAlternatives(\n                        sequences=(' in source
    assert '("agents.open_builds", "builder.assemble"),' in source
    assert (
        '"designer.return_to_agent",\n'
        '                                "agents.open_builds",\n'
        '                                "builder.assemble",'
    ) in source
    assert (
        '"agents.open_sandbox",\n                                "sandbox.start",'
        in source
    )
    assert (
        '"agents.return_to_hub",\n                                "agents.open_sandbox",\n                                "sandbox.start",'
        in source
    )
    assert '("agents.open_evaluation", "evaluation.create_case")' in source
    assert '("agents.open_channels", "channels.create")' in source
    assert 'CHAT_PROMPTS["run_evaluation"],\n                    "evaluation.run_case",' in source
    assert 'CHAT_PROMPTS["request_deployment"],\n                    "deployment.deploy",' in source
    helper = source[
        source.index("async def _open_agent_area_for_mode"):
        source.index("async def _open_bound_agent_area")
    ]
    assert "CHAT_PROMPTS[\"continue_agent\"]" not in helper
    assert "(return_operation_id, open_operation_id)" in helper


def test_api_update_chat_separates_information_from_review_staging() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )
    start = source.index('CHAT_PROMPTS["request_api_update_decision"]')
    end = source.index('await hub.get_by_text("Validated API version"', start)
    flow = source[start:end]

    assert CHAT_PROMPTS["request_api_update_decision"] == (
        "What would that API correction change?"
    )
    assert CHAT_PROMPTS["stage_api_update"] == (
        "I am ready to review that API correction. Keep it pending until I decide."
    )
    assert flow.index('CHAT_PROMPTS["request_api_update_decision"]') < flow.index(
        'CHAT_PROMPTS["stage_api_update"]'
    )
    assert 'CHAT_PROMPTS["request_api_update_decision"],\n                    None,' in flow
    assert 'CHAT_PROMPTS["stage_api_update"],\n                    "sources.approve_contract_revision",' in flow


def test_chat_inspection_body_is_captured_before_navigation_can_discard_it() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )
    helper = source[
        source.index("async def _refresh_chat_evidence_inspector"):
        source.index("async def _load_authenticated_chat_inspection")
    ]
    dispatch = source[
        source.index("async def _chat_dispatch"):
        source.index("def _durable_chat_message")
    ]

    assert "snapshot = await inspection_response.json()" in helper
    assert "return inspection_response, snapshot" in helper
    assert "authenticated_inspection, before_inspection" in dispatch
    assert "before_inspection = await authenticated_inspection.json()" not in dispatch


def test_chat_builder_runtime_proof_survives_immediate_navigation_to_sandbox() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )
    runtime = source[
        source.index('CHAT_PROMPTS["start_build_runtime"]'):
        source.index('if args.mode == "chat":', source.index('CHAT_PROMPTS["start_build_runtime"]'))
    ]

    assert 'if args.mode in {"chat", "hybrid"}:' in runtime
    assert "await _wait_for_build_runtime_lifecycle(" in runtime
    assert 'ids["buildId"],\n                    "running",' in runtime
    assert "await ready_build.get_by_text(\"Running\"" in runtime


def test_chat_sandbox_start_accepts_current_node_without_redundant_navigation() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )
    start = source.index('CHAT_PROMPTS["start_private_trial"]')
    flow = source[start:source.index("sandbox_result =", start)]

    assert '("sandbox.start",),' in flow
    assert '(\n                                "agents.open_sandbox",\n                                "sandbox.start",' in flow
    assert '"agents.return_to_hub",\n                                "agents.open_sandbox",\n                                "sandbox.start",' in flow


def test_chat_downstream_navigation_accepts_direct_legal_cross_feature_paths() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )

    assert '("agents.open_evaluation", "evaluation.create_case")' in source
    assert '("agents.open_channels", "channels.create")' in source
    helper = source[
        source.index("async def _open_agent_area_for_mode"):
        source.index("async def _open_bound_agent_area")
    ]
    assert "(open_operation_id,)," in helper
    assert "(return_operation_id, open_operation_id)," in helper
    assert CHAT_PROMPTS["run_generated_evaluation"] == (
        "Evaluate the automatically generated required case for this version."
    )


def test_evaluation_surface_cannot_supply_derived_sandbox_operation_evidence() -> None:
    source = (
        __import__("pathlib").Path("frontend/src/features/evaluation/EvaluationSurface.tsx")
        .read_text(encoding="utf-8")
    )

    assert "expected_operation_ids" not in source
    assert "evaluation-operation" not in source


def test_delivery_evidence_targets_the_persisted_channel_row_not_chat_copy() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )

    assert 'section.channels-home li[data-status=\'ready\'] > div > span' in source
    assert 'page.get_by_text(f"/{slug}", exact=True)' not in source
    assert 'slug = f"medusa-shopping-{run_id[-6:].casefold()}"' in source
    assert 'CHAT_PROMPTS["enter_delivery"].format(slug=slug)' in source
    assert 'CHAT_PROMPTS["create_channel"].format(slug=slug)' in source


def test_guided_continuation_waits_for_the_product_to_finish_enabling_it() -> None:
    source = Path("scripts/run_horizontal_product_journey.py").read_text(encoding="utf-8")
    segment = source[source.index("async def _open_agent_area_for_mode("):source.index("async def _open_bound_agent_area(")]
    assert "for _ in range(300):" in segment
    assert "if await action.is_enabled():" in segment
    assert "did not become enabled" in segment
    assert "is disabled" not in segment
    assert "if await target_heading.is_visible():" in segment
    assert "return" in segment


def test_chat_only_credential_step_stays_in_the_private_surface_form() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )
    handoff = source.index('"exact reviewed effective API version is approved"')
    private_form = source.index("await _save_profile_exact(", handoff)
    curation = source.index('CHAT_PROMPTS["curate_api"]', private_form)
    segment = source[handoff:curation]

    assert 'CHAT_PROMPTS["configure_connection"]' not in segment
    assert "_save_profile_exact" in segment
    assert "sources.save_api_connection" not in segment


def test_file_first_source_handoff_uses_the_created_agent_without_origin_guessing() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )
    flow = source[source.index('CHAT_PROMPTS["attach_source"]') - 1000:source.index("attached_revision =")]

    assert 'CHAT_PROMPTS["attach_source"]' in flow
    assert 'ChatOperationAlternatives(' in flow
    assert '("agents.return_from_source", "agents.attach_source")' in flow
    assert '"agents.choose_existing_for_source"' in flow
    assert 'name="Use an existing Agent", exact=True' in flow
    assert 'name="Attach Source", exact=True' in flow
    assert 'get_by_label("Ready Workspace Source", exact=True)' not in flow
    assert 'agents.attach_created_source' not in flow
    assert 'workspace.open_agents' not in flow


def test_surface_file_acceptance_is_visibly_separate_from_analysis() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )
    helper = source[
        source.index("async def _surface_add_and_analyze_api"):
        source.index("async def _create_agent_from_surface")
    ]

    assert 'hub.locator(".sources-header-actions").get_by_role(' in helper
    assert helper.index('name="Add API definition"') < helper.index(
        'name="Analyze API operations"'
    )
    assert 'get_by_text("Not started", exact=True)' in helper
    assert '"00-api-definition-saved-before-analysis"' in helper


def test_source_identity_comes_from_one_exact_ready_owner_observation() -> None:
    observations = {
        "sourceInventory": [{
            "source_id": "source-identity1",
            "revision": {
                "revision_id": "revision-ident1",
                "job_id": "job-identity-1",
                "state": "ready",
            },
        }]
    }

    assert asyncio.run(_observed_source_ids(observations)) == {
        "sourceId": "source-identity1",
        "parentRevisionId": "revision-ident1",
        "jobId": "job-identity-1",
    }


def test_file_first_return_selects_the_inventory_row_not_duplicate_next_step() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )
    helper = source[
        source.index("async def _return_to_only_api_source"):
        source.index("def _asks_for_agent_choice")
    ]

    assert 'get_by_role("list", name="API sources", exact=True)' in helper
    assert 'rows.get_by_role("button", name="Open API source", exact=True)' in helper
    assert "row_count > 1" in helper
    assert "row_count == 1" in helper
    assert 'api.locator("#source-detail-title")' in helper


def test_surface_and_hybrid_modes_use_guided_cross_feature_continuations() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )

    for label in (
        "Continue to Builds",
        "Continue to Sandbox",
        "Continue to Evaluation",
        "Continue to Channels",
        "View Operations",
    ):
        assert f'continuation="{label}"' in source


def test_public_write_driver_handles_operation_choice_before_input_detail() -> None:
    source = Path("scripts/run_horizontal_product_journey.py").read_text(encoding="utf-8")
    segment = source[
        source.index("async def _public_request_review("):
        source.index("async def _public_accept_review(")
    ]
    assert 'answer = "Use carts id line items."' in segment
    assert "operation_choice_sent" in segment
    assert "detail_sent" in segment
    assert "unsupported additional clarification" in segment


def test_visible_architecture_inspector_cannot_collide_with_product_surface_readiness() -> None:
    assert FEATURE_SURFACE_SELECTORS == {
        "Agent Designer": "section.designer-home",
        "Agent Builds": "section.builder-home",
        "Agent Sandbox": "section.sandbox-home",
        "Evaluation": "section.evaluation-home",
        "Channels and Deployment": "section.channels-home",
        "Operations": "section.operations-home",
    }
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )
    helpers = source[
        source.index("async def _open_agent_area("):
        source.index("async def _wait_for_product_idle(")
    ]
    assert helpers.count("_feature_surface(page, heading)") == 3
    assert helpers.count('":scope > header"') == 2
    assert 'page.locator("section.agents-home").get_by_role(' in helpers


def test_chat_designer_proposal_is_adopted_without_a_duplicate_surface_action() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )
    start = source.index('CHAT_PROMPTS["enter_design"]')
    end = source.index('await page.get_by_label("Goal"', start)
    flow = source[start:end]

    assert '("agents.open_designer", "designer.propose")' in flow
    assert 'if args.mode == "chat":\n                pass' in flow
    assert flow.index('if args.mode == "chat"') < flow.index('elif args.mode == "hybrid"')
    assert flow.count('name="Propose design", exact=True') == 1


def test_horizontal_video_keeps_public_runtime_in_the_uncut_primary_page() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )

    assert 'choices=("surface", "chat", "hybrid")' in source
    assert "context.expect_page()" not in source
    assert "page.goto(urljoin(args.url, hosted_href))" in source
    assert 'Find products matching "Medusa T-Shirt".' in source
    assert 'answer = "Use carts id line items."' in source
    assert "setpts" not in source
    assert ".playbackRate" not in source
    assert "playbackRate =" not in source
    assert '"heading", name="Corpus Workspace", exact=True' in source
    assert '"heading", name="Workspace Home", exact=True' not in source
    assert 'response.casefold().startswith("should i use ")' in source
    assert 'name="ToolRouter clarification subagent", exact=True' in source
    assert '"deployed Agent keeps owner-only runtime diagnostics out of the public session"' in source
    assert '"Evaluation shows the immutable build RouteDeck NavGraph it evaluated"' in source
    assert '"active deployment shows its exact immutable RouteDeck NavGraph"' in source
    assert '"Operations shows owner-only deployed RouteDeck and ToolRouter evidence"' in source
    assert 'name="Deployed ToolRouter clarification subagent", exact=True' in source
    assert 'name=f"RouteDeck NavGraph for build {ids[\'buildId\']}"' in source
    operations_start = source.index('deployed_runtime = page.get_by_role(')
    operations_end = source.index('if args.mode in {"chat", "hybrid"}:', operations_start)
    operations_flow = source[operations_start:operations_end]
    assert operations_flow.index("await deployed_navgraph.scroll_into_view_if_needed()") < operations_flow.index(
        '"11b-deployed-runtime-plumbing"'
    )
    assert operations_flow.index("await deployed_toolrouter.scroll_into_view_if_needed()") < operations_flow.index(
        '"11c-deployed-toolrouter"'
    )
    assert "navgraph_visible and toolrouter_visible" in operations_flow
    assert 'page.locator("#operations-title").scroll_into_view_if_needed()' in source
    assert 'page.locator(".agent-sources").get_by_text(' in source
    assert "await attached_revision.scroll_into_view_if_needed(timeout=30_000)" in source
    assert 'rows = inventory.get_by_role("listitem")' in source
    assert "exactly one matching API Source row" not in source
    assert '"02-designer-intent-source"' in source
    assert '"02a-designer-design-system"' in source
    assert '"02b-designer-navgraph"' in source
    assert '"02c-designer-navgraph-selection"' in source
    assert '"02d-designer-mobile"' in source
    assert '"11c-deployed-toolrouter"' in source


def test_designer_owner_task_can_publish_bounded_three_mode_evidence() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )

    assert 'choices=("designer", "builder", "evaluation")' in source
    assert 'if args.stop_after == "designer":' in source
    assert "raise CampaignCheckpointReached" in source
    assert "DESIGNER_CHECKPOINT_EXPECTED_CHECKS = 12" in source
    assert 'name="Maximize surface", exact=True' in source
    assert 'name="Agent intent and Source intelligence", exact=True' in source
    assert 'name="Proposed design system", exact=True' in source
    assert 'name="Proposed RouteDeck NavGraph preview", exact=True' in source
    assert "data-node-tone=\"reachable\"" in source
    assert 'get_attribute("aria-label")' in source
    assert 'set_viewport_size({"width": 390, "height": 844})' in source
    assert 'get_by_role("button", name="Agent", exact=True).click()' in source
    assert 'name="Create a new Agent", exact=True' in source
    assert source.count('get_by_role("button", name="Agent", exact=True).click()') >= 2
    assert 'elif args.mode == "hybrid":' in source
    assert 'get_by_label("Ready Workspace Source", exact=True).select_option' not in source
    assert 'name="Agent design blueprint", exact=True' in source
    assert 'CHAT_PROMPTS["generate_design_feature"]' in source
    assert '"designer.generate_feature"' in source
    assert "_fill_designer_feature_and_generate" in source
    assert '"button", name="Generate design proposal", exact=True' in source
    assert '"Customize the Agent goal, behaviors, and policies", exact=True' in source
    assert source.index('"Customize the Agent goal, behaviors, and policies", exact=True') < source.index(
        'get_by_label("Goal", exact=True).fill'
    )
    assert 'locator(".designer-home__status").get_by_text(' in source
    assert '"Revision 2", exact=True' in source
    assert '"Revision 3", exact=True' in source
    assert 'get_by_text("2 immutable revisions", exact=True)' not in source
    assert '"button", name="Build requested", exact=True' in source
    assert 'get_by_text("Build pending", exact=True)' not in source
    assert 'get_by_role("button", name="Connection", exact=True).click()' in source
    assert 'get_by_role("button", name="Operations", exact=True).click()' in source
    assert 'get_by_role("button", name="Graph", exact=True).click()' in source
    assert 'semantic_graph.wait_for(state="visible", timeout=30_000)' in source
    assert 'panel.get_by_text(name, exact=True).wait_for' not in source
    assert 'rows = inventory.get_by_role("listitem")' in source


def test_evaluation_owner_task_publishes_a_bounded_maximized_feature_film() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )

    assert 'EVALUATION_CHECKPOINT_EXPECTED_CHECKS = 23' in source
    assert 'if parsed.stop_after == "evaluation" and parsed.mode != "surface":' in source
    assert 'destination=directory / "builder-sandbox-evaluation-maximized.webm"' in source
    assert '"playbackRate": 1.0' in source
    assert '"maximizedSurface": True' in source
    assert 'name=f"Initial evaluation coverage for build {ids[\'buildId\']}"' in source
    assert 'name="Start runtime", exact=True' in source
    assert '"Sandbox returns a meaningful real Medusa product"' in source
    assert 'has_text="Generated coverage"' in source
    assert 'get_by_text("Draft coverage", exact=True)' in source
    assert 'run_case_name = "Run exact case"' in source
    assert '"generatedDraftStatus": generated_status' in source
    assert 'if args.stop_after == "evaluation":\n                if video_clock_started is not None:' in source


def test_builder_owner_task_publishes_only_the_durable_assembly_milestone() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )

    assert "BUILDER_CHECKPOINT_EXPECTED_CHECKS = 15" in source
    assert 'destination=directory / "builder-assembly-maximized.webm"' in source
    assert 'page.locator(".builder-home li[data-status=\'queued\']")' in source
    assert 'page.locator(".builder-home li[data-status=\'running\']")' in source
    assert 'item.get("operationId") == "builder.assemble"' in source
    assert 'item.get("outcome") == "queued"' in source
    assert '"Builder queues one durable assembly attempt without inline completion"' in source
    assert 'if args.stop_after == "builder":' in source
    assert '"playbackRate": 1.0' in source
    assert '"maximizedSurface": True' in source


def test_horizontal_video_proves_split_surface_and_returns_same_workflow_to_dock() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )
    helper = source[
        source.index("async def _prove_split_surface"):
        source.index("async def _capture")
    ]

    assert 'name="Maximize surface", exact=True' in helper
    assert 'get_attribute("data-surface-layout") == "split"' in helper
    assert 'locator("[data-agent-conversation]")' in helper
    assert 'locator("[data-agent-surface-dock]")' in helper
    assert '"01b-source-chat-split"' in helper
    assert 'name="Return to dock", exact=True' in helper
    assert 'get_attribute("data-surface-layout") == "dock"' in helper


def test_each_visual_proof_has_a_readable_normal_speed_hold() -> None:
    class Page:
        calls: list[tuple[str, object]] = []

        async def wait_for_timeout(self, milliseconds: int) -> None:
            self.calls.append(("hold", milliseconds))

        async def screenshot(self, *, path, full_page: bool) -> None:
            self.calls.append(("screenshot", (path.name, full_page)))

    output: list[str] = []
    page = Page()

    directory = __import__("pathlib").Path.cwd() / "artifacts" / "capture-test"
    asyncio.run(_capture(page, directory, output, "proof-state"))

    assert page.calls == [
        ("hold", 2_500),
        ("screenshot", ("proof-state.png", False)),
        ("hold", 2_500),
    ]


def test_chat_verifier_uses_durable_event_boundary_after_every_turn() -> None:
    source = (
        __import__("pathlib").Path("scripts/run_horizontal_product_journey.py")
        .read_text(encoding="utf-8")
    )
    dispatch = source[source.index("async def _chat_dispatch"):source.index("async def _chat_operation_after")]

    assert dispatch.index("_refresh_chat_evidence_inspector(page, trace)") < dispatch.index(
        "before_sequence = max("
    )
    assert dispatch.rindex("_refresh_chat_evidence_inspector(page, trace)") < dispatch.index(
        "_chat_operations_after("
    )
    assert 'urlsplit(response.url).path == "/api/routedeck/inspect"' in source
    assert 'urlsplit(request.url).path == "/api/routedeck/chat"' in dispatch
    assert "expect_request_finished" not in dispatch
    assert "pending_chat_finished" not in dispatch
    assert dispatch.index("chat_response = await pending_chat.value") < dispatch.index(
        "_wait_for_inspected_chat_turn("
    )
    assert dispatch.index("_wait_for_inspected_chat_turn(") < dispatch.index(
        "await _wait_for_agent_idle(page)"
    )
