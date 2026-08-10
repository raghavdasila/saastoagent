import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Network } from "lucide-react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { Button } from "@/components/ui/button";

import {
  type ApiGraphEdge,
  type ApiGraphNode,
  type ApiGraphView,
  type SourceClient,
  SourceClientError,
} from "./sourceClient";


export function ApiGraphPanel({
  sourceId,
  sourceClient,
  dispatchAffordance,
}: {
  sourceId: string;
  sourceClient: SourceClient;
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"];
}) {
  const [graph, setGraph] = useState<ApiGraphView | null>(null);
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);
  const [selectedStage, setSelectedStage] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [selectionError, setSelectionError] = useState<string | null>(null);
  const [selectionPending, setSelectionPending] = useState(false);

  useEffect(() => {
    let active = true;
    setGraph(null);
    setError(null);
    void sourceClient.inspectApiGraph(sourceId)
      .then((value) => {
        if (!active) return;
        setGraph(value);
        setSelectedGroupId(value.semantic_groups.at(0)?.id ?? null);
        setSelectedStage(0);
      })
      .catch((caught) => {
        if (!active) return;
        setError(
          caught instanceof SourceClientError
            ? caught.message
            : "The persisted semantic graph could not be loaded.",
        );
      });
    return () => { active = false; };
  }, [sourceClient, sourceId]);

  const nodeTypeCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const node of graph?.nodes ?? []) {
      counts.set(node.node_type, (counts.get(node.node_type) ?? 0) + 1);
    }
    return [...counts.entries()].sort(([left], [right]) => left.localeCompare(right));
  }, [graph]);
  const selectedGroup = graph?.semantic_groups.find(({ id }) => id === selectedGroupId) ?? null;
  const operations = useMemo(() => {
    if (graph === null || selectedGroup === null) return [];
    const allowed = new Set(selectedGroup.operation_ids);
    return graph.nodes
      .filter((node) => allowed.has(node.id))
      .sort((left, right) => left.label.localeCompare(right.label));
  }, [graph, selectedGroup]);
  const stage = graph?.playback[selectedStage] ?? null;

  async function selectStage(index: number, stageId: string) {
    if (graph === null) return;
    setSelectionPending(true);
    setSelectionError(null);
    try {
      const result = await dispatchAffordance("select_graph_stage", {
        source_id: graph.source_id,
        revision_id: graph.revision_id,
        stage_id: stageId,
      });
      if (result.outcome !== "selected") {
        throw new Error("The graph stage could not be selected.");
      }
      setSelectedStage(index);
    } catch (caught) {
      setSelectionError(
        caught instanceof Error
          ? caught.message
          : "The graph stage could not be selected.",
      );
    } finally {
      setSelectionPending(false);
    }
  }

  return (
    <section className="api-graph-panel" aria-labelledby="api-graph-title">
      <div className="api-graph-heading">
        <div>
          <p>Persisted ToolRouter evidence</p>
          <h3 id="api-graph-title"><Network aria-hidden="true" /> Semantic graph</h3>
        </div>
        {graph === null ? null : (
          <span>{graph.total_nodes} nodes · {graph.total_edges} edges · {graph.assembler}</span>
        )}
      </div>
      {error === null ? null : <p role="alert" className="sources-debug-error">{error}</p>}
      {graph === null && error === null ? <p role="status">Loading the persisted graph…</p> : null}
      <GraphCanvas nodes={graph?.nodes ?? []} edges={graph?.edges ?? []} selectedNodeIds={selectedGroup === null ? [] : [selectedGroup.id, ...selectedGroup.operation_ids]} />
      {graph === null ? null : (
        <>
          {graph.artifact_revision_id === graph.revision_id ? null : (
            <p className="contract-no-call">
              ToolRouter evidence is inherited unchanged from parent revision <code>{graph.artifact_revision_id}</code>.
            </p>
          )}
          <div className="api-graph-type-counts" aria-label="Graph node types">
            {nodeTypeCounts.map(([type, count]) => (
              <span key={type}><strong>{count}</strong>{type.replaceAll("_", " ")}</span>
            ))}
          </div>

          <div className="api-graph-grid">
            <section aria-labelledby="semantic-groups-title">
              <h4 id="semantic-groups-title">Semantic groups</h4>
              {graph.semantic_groups.length === 0 ? (
                <p>No resource groups were emitted for this revision.</p>
              ) : (
                <div className="api-semantic-groups" role="list">
                  {graph.semantic_groups.map((group) => (
                    <Button
                      key={group.id}
                      type="button"
                      variant={group.id === selectedGroupId ? "default" : "outline"}
                      onClick={() => setSelectedGroupId(group.id)}
                    >
                      {group.label}<span>{group.operation_ids.length}</span>
                    </Button>
                  ))}
                </div>
              )}
              {selectedGroup === null ? null : (
                <div className="api-group-detail">
                  <strong>{selectedGroup.label}</strong>
                  <span>{operations.length} linked operations</span>
                  <ul>
                    {operations.map((operation) => (
                      <li key={operation.id}>
                        <code>{operation.facets.method ?? "API"}</code>
                        <span>{operation.label}</span>
                        <small>{operation.facets.operation_id ?? operation.endpoint_id}</small>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </section>

            <section aria-labelledby="graph-stage-title">
              <h4 id="graph-stage-title">Recorded construction stages</h4>
              {selectionError === null ? null : <p role="alert">{selectionError}</p>}
              <div className="api-playback-steps" role="list">
                {graph.playback.map((item, index) => (
                  <Button
                    key={item.id}
                    type="button"
                    size="sm"
                    variant={index === selectedStage ? "default" : "outline"}
                    disabled={selectionPending}
                    onClick={() => void selectStage(index, item.id)}
                  >
                    {index + 1}. {item.id}
                  </Button>
                ))}
              </div>
              {stage === null ? null : (
                <div className="api-playback-stage">
                  <div><strong>{stage.id}</strong><em data-state={stage.status}>{stage.status}</em></div>
                  <dl>
                    {Object.entries(stage.metrics).map(([key, value]) => (
                      <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{String(value)}</dd></div>
                    ))}
                  </dl>
                  {stage.warning_codes.length === 0 ? null : (
                    <p><AlertTriangle aria-hidden="true" />{stage.warning_codes.join(", ")}</p>
                  )}
                </div>
              )}
            </section>
          </div>
        </>
      )}
    </section>
  );
}

function GraphCanvas({ nodes, edges, selectedNodeIds }: { nodes: readonly ApiGraphNode[]; edges: readonly ApiGraphEdge[]; selectedNodeIds: readonly string[] }) {
  const selected = new Set(selectedNodeIds);
  const selectedNodes = nodes.filter(({ id }) => selected.has(id));
  const neighborIds = new Set(
    edges.flatMap(({ source, target }) =>
      selected.has(source) ? [target] : selected.has(target) ? [source] : [],
    ),
  );
  const neighbors = nodes.filter(
    ({ id }) => neighborIds.has(id) && !selected.has(id),
  );
  const visible = [...selectedNodes, ...neighbors, ...nodes]
    .filter((node, index, values) =>
      values.findIndex(({ id }) => id === node.id) === index,
    )
    .slice(0, 16);
  const visibleIds = new Set(visible.map(({ id }) => id));
  const positions = new Map(visible.map((node, index) => {
    const column = index % 4;
    const row = Math.floor(index / 4);
    return [node.id, { x: 28 + column * 174, y: 24 + row * 78 }] as const;
  }));
  const rows = Math.max(1, Math.ceil(visible.length / 4));
  const height = 48 + rows * 78;
  return <figure className="api-graph-canvas" aria-label="Semantic graph visualization">
    <svg viewBox={`0 0 720 ${height}`} role="img" aria-label="Semantic graph visualization">
      <title id="api-graph-visual-title">Semantic graph visualization</title>
      <desc id="api-graph-visual-description">The selected semantic group and its directly related persisted nodes. Selected operations are highlighted.</desc>
      {edges.filter(({ source, target }) => visibleIds.has(source) && visibleIds.has(target)).map((edge, index) => {
        const source = positions.get(edge.source)!; const target = positions.get(edge.target)!;
        return <line key={`${edge.source}-${edge.target}-${index}`} x1={source.x + 72} y1={source.y + 25} x2={target.x + 72} y2={target.y + 25} data-status={edge.status} />;
      })}
      {visible.map((node) => {
        const point = positions.get(node.id)!;
        return <g key={node.id} transform={`translate(${point.x} ${point.y})`} data-selected={selected.has(node.id)}>
          <rect width="144" height="50" rx="9" />
          <text className="api-graph-node-label" x="10" y="20">{node.label.slice(0, 22)}</text>
          <text className="api-graph-node-type" x="10" y="38">{node.node_type.replaceAll("_", " ").slice(0, 24)}</text>
        </g>;
      })}
    </svg>
    <figcaption>Showing {visible.length} nodes from the selected semantic group and its direct relationships · {nodes.length} total persisted nodes.</figcaption>
  </figure>;
}
