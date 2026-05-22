from __future__ import annotations

from typing import Any

from routedeck_core import RouteDeckOperation

from backend.services.app_graph.manifest import ACTION_TARGETS


class CorpusOperationPolicy:
    """Maps Corpus app actions into generic RouteDeck operations."""

    def operation_for_action(self, action: Any) -> RouteDeckOperation:
        side_effect_categories = {"execution", "feedback", "learning"}
        execution_mode = "review" if action.kind == "form" or action.category in side_effect_categories else "auto"
        safety_class = "navigation"
        if action.category == "execution":
            safety_class = "write_external"
        elif action.category in {"feedback", "learning"}:
            safety_class = "draft"
        elif action.category == "auth":
            safety_class = "credential"

        required_args = [field.key for field in action.fields if field.required]
        missing_args = [
            field.key
            for field in action.fields
            if field.required and field.key not in (action.payload or {}) and getattr(field, "default", None) is None
        ]
        invocation_kind = getattr(action, "invocation_kind", None)
        if invocation_kind is None:
            if action.kind == "form":
                invocation_kind = "form"
            elif action.category == "navigation":
                invocation_kind = "surface"
            else:
                invocation_kind = "direct"

        can_dispatch_now = invocation_kind in {"direct", "surface"} and not missing_args and execution_mode != "blocked"
        return RouteDeckOperation(
            id=action.id,
            label=action.label,
            description=action.description,
            category=action.category,
            kind=action.kind,
            placement=action.placement,
            emphasis=action.emphasis,
            safety_class=safety_class,
            execution_mode=execution_mode,
            input_schema={"fields": [field.model_dump(mode="json") for field in action.fields]},
            payload=action.payload or {},
            invocation_kind=invocation_kind,
            can_dispatch_now=can_dispatch_now,
            required_args=required_args,
            missing_args=missing_args,
            guard=getattr(action, "disabled_reason", None),
            target_node=ACTION_TARGETS.get(action.id),
        )
