from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class EvaluationPlanError(RuntimeError):
    pass


class EvaluationActionRuntime(Protocol):
    def setup(self, adapter_id: str) -> dict[str, Any]: ...

    def send_authored_message(self, message: str) -> dict[str, Any]: ...

    def send_adaptive_message(self) -> dict[str, Any]: ...

    def invoke_suggested_action(
        self,
        *,
        step: dict[str, Any],
        binding: dict[str, Any],
    ) -> dict[str, Any]: ...

    def submit_surface(
        self,
        *,
        step: dict[str, Any],
        binding: dict[str, Any],
    ) -> dict[str, Any]: ...

    def checkpoint(
        self,
        *,
        label: str,
        state_assertions: list[str],
        binding: dict[str, Any],
    ) -> dict[str, Any]: ...


@dataclass
class ActionPlanExecution:
    setup: dict[str, Any]
    steps: list[dict[str, Any]] = field(default_factory=list)

    @property
    def checkpoints(self) -> list[dict[str, Any]]:
        return [item for item in self.steps if item["kind"] == "checkpoint"]


class EvaluationActionPlanExecutor:
    """Execute Studio-authored steps through manifest-bound runtime adapters."""

    def execute(
        self,
        *,
        definition: dict[str, Any],
        binding: dict[str, Any],
        runtime: EvaluationActionRuntime,
    ) -> ActionPlanExecution:
        plan = _object(definition.get("actionPlan"), "actionPlan")
        steps = _list(plan.get("steps"), "actionPlan.steps")
        setup_adapter = _string(binding.get("setupAdapter"), "setupAdapter")
        step_bindings = _object(binding.get("steps"), "steps")
        checkpoint_bindings = _object(
            binding.get("checkpoints", {}),
            "checkpoints",
        )
        executable_ids = {
            _string(step.get("id"), "actionPlan.steps[].id")
            for step in steps
            if step.get("kind") in {"suggested-action", "surface-submit"}
        }
        if set(step_bindings) != executable_ids:
            raise EvaluationPlanError(
                "Manifest executable-step bindings do not exactly match the action plan: "
                f"expected {sorted(executable_ids)}, observed {sorted(step_bindings)}"
            )
        checkpoint_ids = {
            _string(step.get("id"), "actionPlan.steps[].id")
            for step in steps
            if step.get("kind") == "checkpoint"
        }
        if checkpoint_bindings and set(checkpoint_bindings) != checkpoint_ids:
            raise EvaluationPlanError(
                "Manifest checkpoint bindings do not exactly match the action plan: "
                f"expected {sorted(checkpoint_ids)}, observed "
                f"{sorted(checkpoint_bindings)}"
            )

        execution = ActionPlanExecution(setup=runtime.setup(setup_adapter))
        authored_message = definition.get("input", definition.get("openingMessage"))
        for index, raw_step in enumerate(steps):
            step = _object(raw_step, f"actionPlan.steps[{index}]")
            step_id = _string(step.get("id"), f"actionPlan.steps[{index}].id")
            kind = _string(step.get("kind"), f"actionPlan.steps[{index}].kind")
            if kind == "message":
                source = _string(step.get("source"), f"{step_id}.source")
                if source == "authored-input":
                    if not isinstance(authored_message, str) or not authored_message.strip():
                        raise EvaluationPlanError(
                            f"{step_id} requires non-empty input or openingMessage"
                        )
                    evidence = runtime.send_authored_message(authored_message)
                elif source == "adaptive-tester":
                    evidence = runtime.send_adaptive_message()
                else:
                    raise EvaluationPlanError(
                        f"{step_id} has unsupported message source {source!r}"
                    )
            elif kind == "suggested-action":
                evidence = runtime.invoke_suggested_action(
                    step=step,
                    binding=_object(step_bindings[step_id], f"steps.{step_id}"),
                )
            elif kind == "surface-submit":
                evidence = runtime.submit_surface(
                    step=step,
                    binding=_object(step_bindings[step_id], f"steps.{step_id}"),
                )
            elif kind == "checkpoint":
                evidence = runtime.checkpoint(
                    label=_string(step.get("label"), f"{step_id}.label"),
                    state_assertions=[
                        _string(value, f"{step_id}.stateAssertions[]")
                        for value in _list(
                            step.get("stateAssertions"),
                            f"{step_id}.stateAssertions",
                        )
                    ],
                    binding=_object(
                        checkpoint_bindings.get(step_id, {}),
                        f"checkpoints.{step_id}",
                    ),
                )
            else:
                raise EvaluationPlanError(
                    f"{step_id} has unsupported action kind {kind!r}"
                )
            execution.steps.append(
                {"id": step_id, "kind": kind, "evidence": evidence}
            )
        if not execution.checkpoints:
            raise EvaluationPlanError("An action plan must execute at least one checkpoint")
        return execution


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvaluationPlanError(f"{path} must be an object")
    return value


def _list(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise EvaluationPlanError(f"{path} must be a list")
    return value


def _string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvaluationPlanError(f"{path} must be a non-empty string")
    return value


__all__ = [
    "ActionPlanExecution",
    "EvaluationActionPlanExecutor",
    "EvaluationActionRuntime",
    "EvaluationPlanError",
]
