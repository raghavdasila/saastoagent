from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ...errors import SourceArtifactError
from ...models import SourceState
from ...repository import LocalSourceRepository, SourceNotReady


class ApiGraphNodeView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    node_type: str
    label: str
    endpoint_id: str | None = None
    facets: dict[str, str] = Field(default_factory=dict)


class ApiGraphEdgeView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    source: str
    target: str
    type: str
    status: str
    confidence: float


class ApiSemanticGroupView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    label: str
    operation_ids: tuple[str, ...]


class ApiGraphPlaybackStageView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    status: str
    metrics: dict[str, int | float | bool | str]
    warning_codes: tuple[str, ...]


class ApiGraphTraceFrameView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    index: int
    event_type: str
    active_endpoint_id: str | None = None
    added_node_ids: tuple[str, ...]
    updated_node_ids: tuple[str, ...]
    added_edge_ids: tuple[str, ...]
    cumulative_nodes: int
    cumulative_edges: int


class ApiGraphView(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str
    revision_id: str
    artifact_revision_id: str
    assembler: str
    total_nodes: int
    total_edges: int
    nodes: tuple[ApiGraphNodeView, ...]
    edges: tuple[ApiGraphEdgeView, ...]
    semantic_groups: tuple[ApiSemanticGroupView, ...]
    playback: tuple[ApiGraphPlaybackStageView, ...]
    trace: tuple[ApiGraphTraceFrameView, ...]

    def operation_ids_for_group(
        self,
        group: ApiSemanticGroupView,
    ) -> tuple[str, ...]:
        nodes = {node.id: node for node in self.nodes}
        operation_ids: list[str] = []
        for node_id in group.operation_ids:
            node = nodes.get(node_id)
            operation_id = None if node is None else node.facets.get("operation_id")
            if (
                node is None
                or node.node_type != "api_operation"
                or not isinstance(operation_id, str)
                or not operation_id
            ):
                raise SourceArtifactError(
                    "The semantic group references an invalid API operation node."
                )
            operation_ids.append(operation_id)
        return tuple(operation_ids)


@dataclass(frozen=True)
class ApiGraphPresenter:
    repository: LocalSourceRepository

    def inspect(self, *, owner_key: str, source_id: str) -> ApiGraphView:
        source = self.repository.get(owner_key=owner_key, source_id=source_id)
        return self._inspect_source(
            source,
            self.repository.artifact_dir(
                owner_key=owner_key,
                source_id=source_id,
            ),
        )

    def inspect_exact(
        self,
        *,
        owner_key: str,
        source_id: str,
        revision_id: str,
    ) -> ApiGraphView:
        source = self.repository.get_revision(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=revision_id,
        )
        return self._inspect_source(
            source,
            self.repository.artifact_dir_exact(
                owner_key=owner_key,
                source_id=source_id,
                revision_id=revision_id,
            ),
        )

    def _inspect_source(self, source, artifact_dir: Path) -> ApiGraphView:
        if source.connector_key != "api":
            raise SourceNotReady("The selected source is not an API source.")
        if source.revision.state is not SourceState.READY:
            raise SourceNotReady(
                f"Source revision is {source.revision.state.value}, not ready."
            )
        path = artifact_dir / "graph" / "semantic_graph.json"
        graph = _load_object(path)
        raw_nodes = _list_of_objects(graph.get("nodes"), "graph nodes")
        raw_edges = _list_of_objects(graph.get("edges"), "graph edges")
        if len(raw_nodes) > 10_000 or len(raw_edges) > 40_000:
            raise SourceArtifactError("The semantic graph exceeds the product limit.")

        nodes = tuple(_node(value) for value in raw_nodes)
        edges = tuple(_edge(value) for value in raw_edges)
        metadata = _object(graph.get("metadata"), "graph metadata")
        return ApiGraphView(
            source_id=source.source_id,
            revision_id=source.revision.revision_id,
            artifact_revision_id=(
                source.revision.artifact_revision_id
                or source.revision.revision_id
            ),
            assembler=_required_string(metadata.get("assembler"), "graph assembler"),
            total_nodes=len(nodes),
            total_edges=len(edges),
            nodes=nodes,
            edges=edges,
            semantic_groups=_semantic_groups(nodes, edges),
            playback=_playback(metadata),
            trace=_trace(artifact_dir / "graph" / "graph_trace.jsonl", nodes, edges),
        )

    def inspect_stage(
        self,
        *,
        owner_key: str,
        source_id: str,
        revision_id: str,
        stage_id: str,
    ) -> ApiGraphPlaybackStageView:
        graph = self.inspect_exact(
            owner_key=owner_key,
            source_id=source_id,
            revision_id=revision_id,
        )
        for stage in graph.playback:
            if stage.id == stage_id:
                return stage
        raise SourceNotReady(
            "The recorded graph stage is unavailable for this source revision."
        )


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SourceArtifactError("The semantic graph artifact is unavailable.") from error
    return _object(value, "semantic graph")


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise SourceArtifactError(f"The {label} artifact is invalid.")
    return value


def _list_of_objects(value: Any, label: str) -> tuple[dict[str, Any], ...]:
    if not isinstance(value, list):
        raise SourceArtifactError(f"The {label} artifact is invalid.")
    return tuple(_object(item, label) for item in value)


def _required_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourceArtifactError(f"The {label} artifact is invalid.")
    return value


def _optional_string(value: Any, label: str) -> str | None:
    if value is None:
        return None
    return _required_string(value, label)


def _node(value: dict[str, Any]) -> ApiGraphNodeView:
    raw_facets = value.get("facets", {})
    facets = _object(raw_facets, "graph node facets")
    safe_facets: dict[str, str] = {}
    for key in ("method", "operation_class", "operation_id", "path", "resource"):
        candidate = facets.get(key)
        if isinstance(candidate, str) and candidate.strip():
            safe_facets[key] = candidate
    return ApiGraphNodeView(
        id=_required_string(value.get("id"), "graph node ID"),
        node_type=_required_string(value.get("node_type"), "graph node type"),
        label=_required_string(value.get("label"), "graph node label"),
        endpoint_id=_optional_string(value.get("endpoint_id"), "graph endpoint ID"),
        facets=safe_facets,
    )


def _edge(value: dict[str, Any]) -> ApiGraphEdgeView:
    confidence = value.get("confidence")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        raise SourceArtifactError("The graph edge confidence artifact is invalid.")
    source = _required_string(value.get("source"), "graph edge source")
    target = _required_string(value.get("target"), "graph edge target")
    edge_type = _required_string(value.get("type"), "graph edge type")
    edge_id = value.get("id")
    if edge_id is None:
        edge_id = f"{source}|{edge_type}|{target}"
    return ApiGraphEdgeView(
        id=_required_string(edge_id, "graph edge ID"),
        source=source,
        target=target,
        type=edge_type,
        status=_required_string(value.get("status"), "graph edge status"),
        confidence=float(confidence),
    )


def _semantic_groups(
    nodes: tuple[ApiGraphNodeView, ...],
    edges: tuple[ApiGraphEdgeView, ...],
) -> tuple[ApiSemanticGroupView, ...]:
    resources = {node.id: node for node in nodes if node.node_type == "resource"}
    operations_by_resource: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        if edge.type == "exposes" and edge.target in resources:
            operations_by_resource[edge.target].add(edge.source)
    return tuple(
        ApiSemanticGroupView(
            id=resource.id,
            label=resource.label,
            operation_ids=tuple(sorted(operations_by_resource.get(resource.id, set()))),
        )
        for resource in sorted(resources.values(), key=lambda item: (item.label, item.id))
    )


def _playback(metadata: dict[str, Any]) -> tuple[ApiGraphPlaybackStageView, ...]:
    conformance = _object(
        metadata.get("construction_conformance"),
        "graph construction conformance",
    )
    raw_order = conformance.get("stage_order")
    if not isinstance(raw_order, list) or not all(
        isinstance(value, str) and value for value in raw_order
    ):
        raise SourceArtifactError("The graph construction stage order is invalid.")
    stages = _object(conformance.get("stages"), "graph construction stages")
    output: list[ApiGraphPlaybackStageView] = []
    for stage_id in raw_order:
        stage = _object(stages.get(stage_id), f"graph construction stage {stage_id}")
        raw_metrics = _object(stage.get("metrics", {}), "graph stage metrics")
        metrics = {
            key: value
            for key, value in raw_metrics.items()
            if isinstance(value, (int, float, bool, str))
            and not isinstance(value, (dict, list))
        }
        raw_warnings = stage.get("warnings", [])
        if not isinstance(raw_warnings, list):
            raise SourceArtifactError("The graph stage warnings artifact is invalid.")
        warning_codes = tuple(
            code
            for warning in raw_warnings
            if isinstance(warning, Mapping)
            for code in [warning.get("code")]
            if isinstance(code, str) and code
        )
        output.append(
            ApiGraphPlaybackStageView(
                id=stage_id,
                status=_required_string(stage.get("status"), "graph stage status"),
                metrics=metrics,
                warning_codes=warning_codes,
            )
        )
    return tuple(output)


def _trace(
    path: Path,
    nodes: tuple[ApiGraphNodeView, ...],
    edges: tuple[ApiGraphEdgeView, ...],
) -> tuple[ApiGraphTraceFrameView, ...]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise SourceArtifactError("The graph construction trace is unavailable.") from error
    if not lines or len(lines) > 50_000:
        raise SourceArtifactError("The graph construction trace is invalid.")
    node_ids = {node.id for node in nodes}
    edge_ids = {edge.id for edge in edges}
    output: list[ApiGraphTraceFrameView] = []
    for index, line in enumerate(lines):
        try:
            event = _object(json.loads(line), "graph construction trace event")
        except json.JSONDecodeError as error:
            raise SourceArtifactError("The graph construction trace is invalid.") from error
        added_node_ids = _trace_ids(event.get("added_nodes", []), "node", "id")
        updated_node_ids = _trace_ids(
            event.get("updated_nodes", []),
            "updated node",
            "node_id",
        )
        added_edge_ids = _trace_ids(event.get("added_edges", []), "edge", "id")
        if not set((*added_node_ids, *updated_node_ids)).issubset(node_ids):
            raise SourceArtifactError("The graph construction trace references an unavailable node.")
        if not set(added_edge_ids).issubset(edge_ids):
            raise SourceArtifactError("The graph construction trace references an unavailable edge.")
        cumulative = _object(event.get("cumulative"), "graph construction trace cumulative counts")
        cumulative_nodes = cumulative.get("nodes")
        event_type = _required_string(
            event.get("type"),
            "graph construction event type",
        )
        cumulative_edges = cumulative.get(
            "edges" if event_type in {"cards_complete", "conformance_complete"} else "unique_edges"
        )
        if not isinstance(cumulative_nodes, int) or cumulative_nodes < 0:
            raise SourceArtifactError("The graph construction trace node count is invalid.")
        if not isinstance(cumulative_edges, int) or cumulative_edges < 0:
            raise SourceArtifactError("The graph construction trace edge count is invalid.")
        output.append(ApiGraphTraceFrameView(
            index=index,
            event_type=event_type,
            active_endpoint_id=_optional_string(event.get("active_endpoint_id"), "active endpoint ID"),
            added_node_ids=added_node_ids,
            updated_node_ids=updated_node_ids,
            added_edge_ids=added_edge_ids,
            cumulative_nodes=cumulative_nodes,
            cumulative_edges=cumulative_edges,
        ))
    return tuple(output)


def _trace_ids(value: Any, label: str, id_field: str) -> tuple[str, ...]:
    items = _list_of_objects(value, f"graph construction {label}s")
    return tuple(
        _required_string(
            item.get(id_field),
            f"graph construction {label} ID",
        )
        for item in items
    )


__all__ = ["ApiGraphPresenter", "ApiGraphView"]
