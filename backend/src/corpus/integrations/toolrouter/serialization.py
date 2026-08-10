from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np

from .engine.semantic_graph import (
    SemanticEdge,
    SemanticEvidence,
    SemanticGraph,
    SemanticNode,
    SemanticNodeCard,
)
from .engine.semantic_graph_retrieval import (
    DEFAULT_EDGE_TYPE_WEIGHTS,
    EmbeddingProvider,
    SemanticGraphIndex,
)
from .errors import ToolRouterArtifactError


def write_json_atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True),
        encoding="utf-8",
    )
    temporary.replace(path)


def write_graph(path: Path, graph: SemanticGraph) -> None:
    write_json_atomic(path, asdict(graph))


def read_graph(path: Path) -> SemanticGraph:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        nodes = [
            SemanticNode(
                **{
                    **row,
                    "evidence": [
                        SemanticEvidence(**evidence)
                        for evidence in row.get("evidence", [])
                    ],
                }
            )
            for row in payload["nodes"]
        ]
        edges = [
            SemanticEdge(
                **{
                    **row,
                    "evidence": [
                        SemanticEvidence(**evidence)
                        for evidence in row.get("evidence", [])
                    ],
                }
            )
            for row in payload["edges"]
        ]
        cards = [
            SemanticNodeCard(
                **{
                    **row,
                    "evidence": [
                        SemanticEvidence(**evidence)
                        for evidence in row.get("evidence", [])
                    ],
                }
            )
            for row in payload["cards"]
        ]
        return SemanticGraph(
            nodes=nodes,
            edges=edges,
            cards=cards,
            metadata=dict(payload.get("metadata") or {}),
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise ToolRouterArtifactError(
            f"The semantic graph artifact is invalid: {error}"
        ) from error


def write_embeddings(path: Path, embeddings: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("wb") as handle:
        np.save(handle, embeddings, allow_pickle=False)
    temporary.replace(path)


def read_index(
    *,
    graph_path: Path,
    embeddings_path: Path,
    embedding_provider: EmbeddingProvider,
) -> SemanticGraphIndex:
    graph = read_graph(graph_path)
    try:
        embeddings = np.load(embeddings_path, allow_pickle=False)
    except (OSError, ValueError) as error:
        raise ToolRouterArtifactError(
            f"The semantic embedding artifact is invalid: {error}"
        ) from error
    if embeddings.ndim != 2 or embeddings.shape[0] != len(graph.cards):
        raise ToolRouterArtifactError(
            "The semantic embedding rows do not match the persisted graph cards."
        )

    weights = dict(DEFAULT_EDGE_TYPE_WEIGHTS)
    adjacency: dict[str, list[tuple[str, str, float]]] = {}

    def add(source: str, target: str, edge_type: str, weight: float) -> None:
        adjacency.setdefault(source, []).append((target, edge_type, weight))

    for edge in graph.edges:
        weight = weights.get(edge.type, 0.25) * float(edge.confidence)
        add(edge.source, edge.target, edge.type, weight)
        add(edge.target, edge.source, f"reverse:{edge.type}", weight * 0.72)
    return SemanticGraphIndex(
        graph=graph,
        cards=list(graph.cards),
        embeddings=np.asarray(embeddings, dtype=np.float32),
        embedding_provider=embedding_provider,
        edge_type_weights=weights,
        adjacency=adjacency,
    )


def subset_index(
    index: SemanticGraphIndex,
    *,
    allowed_endpoint_ids: tuple[str, ...],
) -> SemanticGraphIndex:
    """Build an in-memory retrieval corpus for the exact accepted endpoints."""

    allowed = frozenset(allowed_endpoint_ids)
    if not allowed:
        raise ValueError("At least one allowed endpoint ID is required.")
    if len(allowed) != len(allowed_endpoint_ids):
        raise ValueError("Allowed endpoint IDs must be unique.")
    available = {
        card.endpoint_id for card in index.cards if card.endpoint_id is not None
    }
    if allowed - available:
        raise ValueError("Allowed endpoint IDs must exist in the persisted index.")

    nodes = [
        node
        for node in index.graph.nodes
        if node.endpoint_id is None or node.endpoint_id in allowed
    ]
    node_ids = {node.id for node in nodes}
    edges = [
        edge
        for edge in index.graph.edges
        if edge.source in node_ids and edge.target in node_ids
    ]
    card_rows = [
        row
        for row, card in enumerate(index.cards)
        if card.endpoint_id is None or card.endpoint_id in allowed
    ]
    cards = [index.cards[row] for row in card_rows]
    if not cards:
        raise ValueError("The allowed endpoint subset has no semantic cards.")

    adjacency: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
    for edge in edges:
        weight = index.edge_type_weights.get(edge.type, 0.25) * float(edge.confidence)
        adjacency[edge.source].append((edge.target, edge.type, weight))
        adjacency[edge.target].append(
            (edge.source, f"reverse:{edge.type}", weight * 0.72)
        )
    graph = SemanticGraph(
        nodes=nodes,
        edges=edges,
        cards=cards,
        metadata=dict(index.graph.metadata),
    )
    return SemanticGraphIndex(
        graph=graph,
        cards=cards,
        embeddings=np.asarray(index.embeddings[card_rows], dtype=np.float32),
        embedding_provider=index.embedding_provider,
        edge_type_weights=dict(index.edge_type_weights),
        adjacency=dict(adjacency),
    )


__all__ = [
    "read_graph",
    "read_index",
    "subset_index",
    "write_embeddings",
    "write_graph",
    "write_json_atomic",
]
