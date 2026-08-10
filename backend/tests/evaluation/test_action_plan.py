from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from corpus.evaluation.action_plan import (
    EvaluationActionPlanExecutor,
    EvaluationPlanError,
)
from corpus.evaluation.http_action_runtime import (
    HttpEvaluationActionRuntime,
    _operation_result,
    _surface_prop,
)


@dataclass
class RuntimeProbe:
    calls: list[tuple[str, Any]] = field(default_factory=list)

    def setup(self, adapter_id: str):
        self.calls.append(("setup", adapter_id))
        return {"adapter": adapter_id}

    def send_authored_message(self, message: str):
        self.calls.append(("message", message))
        return {"sent": True}

    def send_adaptive_message(self):
        self.calls.append(("adaptive", None))
        return {"sent": True}

    def invoke_suggested_action(self, *, step, binding):
        self.calls.append(("suggested-action", (step["action"], binding["operation"])))
        return {"disposition": "completed"}

    def submit_surface(self, *, step, binding):
        self.calls.append(("surface-submit", (step["surface"], binding["operation"])))
        return {"disposition": "completed"}

    def checkpoint(self, *, label, state_assertions, binding):
        self.calls.append(("checkpoint", (label, state_assertions, binding)))
        return {"projection": {"current": {"node_id": "workspace.home"}}}


def test_action_plan_executes_messages_actions_surfaces_and_checkpoint_in_order() -> None:
    runtime = RuntimeProbe()
    definition = {
        "input": "Create my account.",
        "actionPlan": {
            "preconditions": ["A unique owner email exists."],
            "steps": [
                {"id": "opening", "kind": "message", "source": "authored-input"},
                {
                    "id": "submit",
                    "kind": "surface-submit",
                    "surface": "Create owner account surface",
                    "inputIntent": "Valid unique owner details.",
                },
                {
                    "id": "continue",
                    "kind": "suggested-action",
                    "behavior": "Create an owner account",
                    "action": "Continue to Workspace",
                },
                {
                    "id": "final",
                    "kind": "checkpoint",
                    "label": "Final product state",
                    "stateAssertions": ["The owner is authenticated."],
                },
            ],
        },
    }
    binding = {
        "setupAdapter": "lounge.public_unique_owner",
        "steps": {
            "submit": {
                "operation": "lounge.create_owner_account",
                "surface": "lounge.register",
                "payloadAdapter": "lounge.valid_unique_owner",
            },
            "continue": {"operation": "lounge.registration.continue_to_workspace"},
        },
        "checkpoints": {
            "final": {
                "node": "workspace.home",
                "authentication": "authenticated",
            }
        },
    }

    result = EvaluationActionPlanExecutor().execute(
        definition=definition,
        binding=binding,
        runtime=runtime,
    )

    assert [name for name, _ in runtime.calls] == [
        "setup",
        "message",
        "surface-submit",
        "suggested-action",
        "checkpoint",
    ]
    assert len(result.checkpoints) == 1


def test_action_plan_rejects_unbound_executable_step() -> None:
    definition = {
        "openingMessage": "Reset my password.",
        "actionPlan": {
            "steps": [
                {"id": "opening", "kind": "message", "source": "authored-input"},
                {
                    "id": "submit",
                    "kind": "surface-submit",
                    "surface": "Password reset request surface",
                    "inputIntent": "Unknown email.",
                },
                {
                    "id": "final",
                    "kind": "checkpoint",
                    "label": "Final",
                    "stateAssertions": ["No owner was created."],
                },
            ]
        },
    }

    with pytest.raises(EvaluationPlanError, match="exactly match"):
        EvaluationActionPlanExecutor().execute(
            definition=definition,
            binding={"setupAdapter": "lounge.public", "steps": {}},
            runtime=RuntimeProbe(),
        )


def test_feature_manifest_evaluation_adapters_are_backed_by_runtime_registry() -> None:
    import json
    from pathlib import Path

    repository = Path(__file__).resolve().parents[3]
    manifest = json.loads(
        (
            repository / "contracts/corpus-agent-design-routedeck-manifest.json"
        ).read_text(encoding="utf-8")
    )
    bindings = tuple(
        binding
        for feature in manifest["features"]
        for binding in feature.get("evaluationBindings", {}).values()
    )
    pending = tuple(
        binding
        for binding in bindings
        if binding.get("implementationStatus") == "pending_external_evidence"
    )
    executable = tuple(binding for binding in bindings if binding not in pending)
    setup_adapters = {
        binding["setupAdapter"]
        for binding in executable
    }
    payload_adapters = {
        step["payloadAdapter"]
        for binding in executable
        for step in binding["steps"].values()
        if "payloadAdapter" in step
    }

    assert pending
    assert all(
        isinstance(binding.get("externalEvidenceOwner"), str)
        and "setupAdapter" not in binding
        and "steps" not in binding
        for binding in pending
    )
    assert setup_adapters <= HttpEvaluationActionRuntime.registered_setup_adapters()
    assert payload_adapters <= HttpEvaluationActionRuntime.registered_payload_adapters()


def test_private_form_handle_uses_routedeck_public_value_projection_shape() -> None:
    surface = {
        "surface_id": "lounge.register",
        "props": [{"name": "form_handle", "value": "lounge-register"}],
    }

    assert _surface_prop(surface, "form_handle") == "lounge-register"


def test_failed_operation_http_status_remains_operation_evidence() -> None:
    import httpx

    response = httpx.Response(
        409,
        request=httpx.Request("POST", "http://corpus.test/api/routedeck/dispatch"),
        json={
            "disposition": "failed",
            "operation_id": "lounge.confirm_owner_email",
            "failure": {"code": "invalid_verification_token"},
        },
    )

    assert _operation_result(response)["disposition"] == "failed"
