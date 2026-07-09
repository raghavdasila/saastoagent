from __future__ import annotations

from typing import Any

from backend.core.schemas import CorpusContextLens, CorpusGraphState
from routedeck_core import RouteDeckManifest, RouteDeckProjection, build_runtime_snapshot


def build_graph_introspection(
    manifest: RouteDeckManifest,
    *,
    state: CorpusGraphState,
    lens: CorpusContextLens,
    projection: RouteDeckProjection,
    valid_actions: list[dict[str, Any]],
    blocked_actions: list[dict[str, str]],
    guard_explanations: list[dict[str, Any]],
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runtime_snapshot = build_runtime_snapshot(
        manifest,
        current_node=state.node,
        valid_actions=valid_actions,
        blocked_actions=blocked_actions,
        executed_nodes=state.executed_nodes,
        diagnostics=diagnostics or {},
    )
    return {
        "current_node": state.node,
        "reachable_nodes": runtime_snapshot["reachable_nodes"],
        "legal_operations": [operation.model_dump(mode="json") for operation in projection.legal_operations],
        "blocked_operations": blocked_actions,
        "guard_explanations": guard_explanations,
        "surface_projection": {
            name: surface.model_dump(mode="json") for name, surface in projection.surfaces.items()
        },
        "route_trace": {
            "executed_nodes": list(state.executed_nodes),
            "replace_path": diagnostics.get("replace_path") if diagnostics else None,
        },
        "runtime_snapshot": runtime_snapshot,
        "context_lens": lens.model_dump(mode="json"),
    }
