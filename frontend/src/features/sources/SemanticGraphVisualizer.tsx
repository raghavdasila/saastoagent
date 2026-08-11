import { useEffect, useMemo, useRef, useState } from "react";
import cytoscape, { type Core } from "cytoscape";
import Graph from "graphology";
import type SigmaRenderer from "sigma";
import {
  ChevronLeft,
  ChevronRight,
  Focus,
  Maximize2,
  Minimize2,
  Pause,
  Play,
  RotateCcw,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import type { ApiGraphView } from "./sourceClient";

const NODE_STYLES: Readonly<Record<string, { color: string; size: number }>> = Object.freeze({
  api_operation: { color: "#2563eb", size: 7 },
  action: { color: "#7c3aed", size: 5 },
  resource: { color: "#0f766e", size: 6 },
  api_shape: { color: "#b26700", size: 5 },
  api_schema: { color: "#237796", size: 5 },
  api_inline_shape: { color: "#5a8da4", size: 3.5 },
  api_field: { color: "#94a3b8", size: 3.5 },
  permission: { color: "#b4261e", size: 5 },
  side_effect: { color: "#a44c86", size: 5 },
  doc_chunk: { color: "#64748b", size: 4 },
  example_query: { color: "#db2777", size: 4 },
});

type Selection =
  | { readonly kind: "node"; readonly id: string }
  | { readonly kind: "edge"; readonly id: string }
  | null;

function labelForZoom(ratio: number, nodeType: string) {
  if (ratio < 0.18) return true;
  if (ratio < 0.35) {
    return !["api_inline_shape", "api_field", "doc_chunk"].includes(nodeType);
  }
  if (ratio < 0.7) return ["api_operation", "resource", "permission"].includes(nodeType);
  return false;
}

export function SemanticGraphVisualizer({
  graph,
  selectedGroupId,
}: {
  graph: ApiGraphView;
  selectedGroupId: string | null;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const activeContainerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<SigmaRenderer | null>(null);
  const activeRendererRef = useRef<Core | null>(null);
  const graphRef = useRef<Graph | null>(null);
  const selectionRef = useRef<Selection>(null);
  const trace = graph.trace ?? [];
  const [mode, setMode] = useState<"accumulated" | "active">("accumulated");
  const [endpointId, setEndpointId] = useState("");
  const [frameIndex, setFrameIndex] = useState(Math.max(0, trace.length - 1));
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [selection, setSelection] = useState<Selection>(null);
  const [expanded, setExpanded] = useState(false);
  const [layoutState, setLayoutState] = useState<"calculating" | "ready" | "failed">("calculating");

  const nodeBirth = useMemo(() => birthIndex(trace, "added_node_ids"), [trace]);
  const edgeBirth = useMemo(() => birthIndex(trace, "added_edge_ids"), [trace]);
  const endpoints = useMemo(
    () => graph.nodes
      .filter((node) => node.node_type === "api_operation" && node.endpoint_id !== null)
      .sort((left, right) => left.label.localeCompare(right.label)),
    [graph.nodes],
  );
  const frame = trace[frameIndex] ?? trace.at(-1) ?? null;
  const addedThisFrame = useMemo(() => new Set(frame?.added_node_ids ?? []), [frame]);
  const updatedThisFrame = useMemo(() => new Set(frame?.updated_node_ids ?? []), [frame]);
  const edgeAddedThisFrame = useMemo(() => new Set(frame?.added_edge_ids ?? []), [frame]);
  const activeNodeId = frame?.active_endpoint_id == null
    ? null
    : graph.nodes.find(({ endpoint_id }) => endpoint_id === frame.active_endpoint_id)?.id ?? null;
  const selectedNode = selection?.kind === "node"
    ? graph.nodes.find(({ id }) => id === selection.id) ?? null
    : null;
  const selectedEdge = selection?.kind === "edge"
    ? graph.edges.find(({ id }) => id === selection.id) ?? null
    : null;
  const activeTopology = useMemo(() => {
    if (endpointId === "") return { nodeIds: new Set<string>(), edgeIds: new Set<string>() };
    const nodeIds = new Set(
      graph.nodes
        .filter((node) => node.endpoint_id === endpointId)
        .map((node) => node.id),
    );
    for (const edge of graph.edges) {
      if (nodeIds.has(edge.source) || nodeIds.has(edge.target)) {
        nodeIds.add(edge.source);
        nodeIds.add(edge.target);
      }
    }
    return {
      nodeIds,
      edgeIds: new Set(
        graph.edges
          .filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target))
          .map((edge) => edge.id),
      ),
    };
  }, [endpointId, graph.edges, graph.nodes]);

  useEffect(() => {
    setFrameIndex(Math.max(0, trace.length - 1));
    setPlaying(false);
    setSelection(null);
    setEndpointId("");
  }, [graph.revision_id, trace.length]);

  useEffect(() => {
    selectionRef.current = selection;
    rendererRef.current?.refresh();
  }, [selection]);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      if (mode === "accumulated") {
        rendererRef.current?.resize();
        rendererRef.current?.refresh();
        rendererRef.current?.getCamera().animatedReset({ duration: 300 });
      } else {
        activeRendererRef.current?.resize();
        activeRendererRef.current?.fit(undefined, 48);
      }
    });
    return () => window.cancelAnimationFrame(frame);
  }, [expanded, mode]);

  useEffect(() => {
    const close = (event: KeyboardEvent) => {
      if (event.key === "Escape") setExpanded(false);
    };
    window.addEventListener("keydown", close);
    return () => window.removeEventListener("keydown", close);
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (container === null) return;
    let cancelled = false;
    let renderer: SigmaRenderer | null = null;
    let worker: Worker | null = null;
    const semanticGraph = new Graph({ type: "directed", multi: false, allowSelfLoops: true });
    for (const [index, node] of graph.nodes.entries()) {
      const angle = (index / Math.max(1, graph.nodes.length)) * Math.PI * 2;
      const style = NODE_STYLES[node.node_type] ?? { color: "#64748b", size: 4 };
      semanticGraph.addNode(node.id, {
        x: Math.cos(angle),
        y: Math.sin(angle),
        label: node.label,
        rawLabel: node.label,
        size: style.size,
        color: style.color,
        baseColor: style.color,
        nodeType: node.node_type,
      });
    }
    for (const edge of graph.edges) {
      semanticGraph.addDirectedEdgeWithKey(edge.id, edge.source, edge.target, {
        color: edge.status === "observed" ? "#c7cfdd" : "#e2e8f0",
        baseColor: edge.status === "observed" ? "#c7cfdd" : "#e2e8f0",
        size: 0.7,
        label: edge.type,
        rawLabel: edge.type,
        type: "arrow",
      });
    }
    graphRef.current = semanticGraph;
    setLayoutState("calculating");
    if (typeof WebGL2RenderingContext === "undefined") {
      setLayoutState("ready");
      return () => { cancelled = true; graphRef.current = null; };
    }
    void import("sigma").then(({ default: Sigma }) => {
      if (cancelled) return;
      renderer = new Sigma(semanticGraph, container, {
        minCameraRatio: 0.0005,
        maxCameraRatio: 64,
        enableEdgeEvents: true,
        hideEdgesOnMove: false,
        hideLabelsOnMove: true,
        labelColor: { color: "#26394d" },
        labelDensity: 0.04,
        labelGridCellSize: 120,
        labelRenderedSizeThreshold: 6,
        renderEdgeLabels: true,
        stagePadding: 32,
        zIndex: true,
        nodeReducer: (id, data) => {
          const currentSelection = selectionRef.current;
          const selected = currentSelection?.kind === "node" && currentSelection.id === id;
          return {
            ...data,
            label: selected || labelForZoom(renderer?.getCamera().getState().ratio ?? 1, String(data.nodeType))
              ? data.rawLabel
              : "",
            highlighted: selected || Boolean(data.highlighted),
            size: Number(data.size) + (selected ? 3 : 0),
          };
        },
        edgeReducer: (id, data) => {
          const selected = selectionRef.current?.kind === "edge" && selectionRef.current.id === id;
          return {
            ...data,
            label: selected ? data.rawLabel : "",
            size: selected ? 3.5 : Number(data.size),
          };
        },
      });
      renderer.getCamera().on("updated", () => renderer?.refresh());
      renderer.on("clickNode", ({ node }) => setSelection({ kind: "node", id: node }));
      renderer.on("clickEdge", ({ edge }) => setSelection({ kind: "edge", id: edge }));
      renderer.on("clickStage", () => setSelection(null));
      rendererRef.current = renderer;
      worker = new Worker(new URL("./semanticGraphLayout.worker.ts", import.meta.url), { type: "module" });
      worker.onmessage = (event: MessageEvent<{ type?: string; positions?: Record<string, { x: number; y: number }> }>) => {
        if (event.data.type === "layout-error" || event.data.positions === undefined) {
          worker?.terminate(); worker = null; setLayoutState("failed"); return;
        }
        for (const [id, position] of Object.entries(event.data.positions)) {
          if (semanticGraph.hasNode(id)) semanticGraph.mergeNodeAttributes(id, position);
        }
        setLayoutState("ready");
        renderer?.refresh();
        renderer?.getCamera().animatedReset({ duration: 400 });
        worker?.terminate(); worker = null;
      };
      worker.onerror = () => { worker?.terminate(); worker = null; setLayoutState("failed"); };
      worker.postMessage({
        type: "layout",
        requestId: graph.revision_id,
        nodes: graph.nodes.map(({ id, node_type, facets }) => ({ id, node_type, facets })),
        edges: graph.edges.map(({ id, source, target }) => ({ id, source, target })),
      });
    });
    return () => {
      cancelled = true;
      worker?.terminate();
      renderer?.kill();
      rendererRef.current = null;
      graphRef.current = null;
    };
  }, [graph]);

  useEffect(() => {
    const semanticGraph = graphRef.current;
    const renderer = rendererRef.current;
    if (semanticGraph === null || renderer === null || mode !== "accumulated") return;
    semanticGraph.forEachNode((id, attributes) => {
      const born = (nodeBirth.get(id) ?? Number.MAX_SAFE_INTEGER) <= frameIndex;
      const highlighted = id === activeNodeId || id === selectedGroupId || addedThisFrame.has(id) || updatedThisFrame.has(id);
      semanticGraph.mergeNodeAttributes(id, {
        hidden: !born,
        highlighted,
        forceLabel: highlighted || selection?.kind === "node" && selection.id === id,
        zIndex: highlighted ? 2 : 0,
        color: addedThisFrame.has(id)
          ? "#16a34a"
          : updatedThisFrame.has(id)
            ? "#d97706"
            : attributes.baseColor,
      });
    });
    semanticGraph.forEachEdge((id, attributes, source, target) => {
      const born = (edgeBirth.get(id) ?? Number.MAX_SAFE_INTEGER) <= frameIndex;
      const visible = !semanticGraph.getNodeAttribute(source, "hidden") && !semanticGraph.getNodeAttribute(target, "hidden");
      semanticGraph.mergeEdgeAttributes(id, {
        hidden: !(born && visible),
        color: edgeAddedThisFrame.has(id) ? "#16a34a" : attributes.baseColor,
        size: edgeAddedThisFrame.has(id) ? 1.8 : 0.7,
      });
    });
    renderer.refresh();
  }, [activeNodeId, addedThisFrame, edgeAddedThisFrame, edgeBirth, frameIndex, mode, nodeBirth, selectedGroupId, selection, updatedThisFrame]);

  useEffect(() => {
    const container = activeContainerRef.current;
    if (mode !== "active" || endpointId === "" || container === null) return;
    const nodes = graph.nodes.filter(
      (node) => activeTopology.nodeIds.has(node.id)
        && (nodeBirth.get(node.id) ?? Number.MAX_SAFE_INTEGER) <= frameIndex,
    );
    const visibleNodeIds = new Set(nodes.map(({ id }) => id));
    const edges = graph.edges.filter(
      (edge) => activeTopology.edgeIds.has(edge.id)
        && visibleNodeIds.has(edge.source)
        && visibleNodeIds.has(edge.target)
        && (edgeBirth.get(edge.id) ?? Number.MAX_SAFE_INTEGER) <= frameIndex,
    );
    const renderer = cytoscape({
      container,
      elements: [
        ...nodes.map((node) => ({
          data: {
            id: node.id,
            label: node.label.length > 34 ? `${node.label.slice(0, 31)}…` : node.label,
            nodeType: node.node_type,
          },
        })),
        ...edges.map((edge) => ({
          data: {
            id: edge.id,
            source: edge.source,
            target: edge.target,
            label: edge.type,
          },
        })),
      ],
      style: [
        {
          selector: "node",
          style: {
            label: "data(label)",
            "font-size": 8,
            "text-wrap": "wrap",
            "text-max-width": "90px",
            "background-color": "#64748b",
            color: "#26324b",
            "text-valign": "bottom",
          },
        },
        ...Object.entries(NODE_STYLES).map(([type, style]) => ({
          selector: `node[nodeType = "${type}"]`,
          style: {
            "background-color": style.color,
            width: style.size * 2,
            height: style.size * 2,
          },
        })),
        {
          selector: "node:selected",
          style: {
            "border-color": "#0f172a",
            "border-width": 2,
          },
        },
        {
          selector: "edge",
          style: {
            width: 0.8,
            "line-color": "#b9c3d4",
            "target-arrow-color": "#b9c3d4",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            label: "data(label)",
            "font-size": 7,
            color: "#6d7890",
          },
        },
      ],
      layout: {
        name: "concentric",
        animate: (typeof window.matchMedia !== "function"
          || !window.matchMedia("(prefers-reduced-motion: reduce)").matches)
          && nodes.length < 220,
        animationDuration: 240,
        fit: true,
        padding: 48,
        avoidOverlap: true,
        minNodeSpacing: 52,
        spacingFactor: 1.18,
        startAngle: -Math.PI / 2,
      },
    });
    activeRendererRef.current = renderer;
    renderer.on("tap", "node", (event) => setSelection({ kind: "node", id: event.target.id() }));
    renderer.on("tap", "edge", (event) => setSelection({ kind: "edge", id: event.target.id() }));
    renderer.on("tap", (event) => {
      if (event.target === renderer) setSelection(null);
    });
    return () => {
      renderer.destroy();
      if (activeRendererRef.current === renderer) activeRendererRef.current = null;
    };
  }, [activeTopology, edgeBirth, endpointId, frameIndex, graph.edges, graph.nodes, mode, nodeBirth]);

  useEffect(() => {
    if (!playing || trace.length < 2) return;
    const timer = window.setInterval(() => {
      setFrameIndex((current) => {
        if (current >= trace.length - 1) { setPlaying(false); return current; }
        return current + 1;
      });
    }, Math.max(120, 2_000 / speed));
    return () => window.clearInterval(timer);
  }, [playing, speed, trace.length]);

  const visibleNodeCount = frame?.cumulative_nodes ?? graph.total_nodes;
  const visibleEdgeCount = frame?.cumulative_edges ?? graph.total_edges;
  const frameTitle = frame === null ? "Persisted semantic graph" : frame.event_type.replaceAll("_", " ");

  return (
    <section
      className="semantic-graph-visualizer"
      data-expanded={expanded}
      aria-label="Complete semantic graph and recorded construction replay"
    >
      <header className="semantic-graph-toolbar">
        <div><strong>ToolRouter graph construction</strong><span>Complete persisted graph · no sampling</span></div>
        <div className="semantic-graph-mode" role="group" aria-label="Graph view">
          <Button type="button" size="sm" variant={mode === "accumulated" ? "default" : "outline"} onClick={() => setMode("accumulated")}>Accumulated graph</Button>
          <Button type="button" size="sm" variant={mode === "active" ? "default" : "outline"} onClick={() => setMode("active")}>Operation neighborhood</Button>
          <Button type="button" size="sm" variant="outline" onClick={() => {
            if (mode === "accumulated") rendererRef.current?.getCamera().animatedReset({ duration: 300 });
            else activeRendererRef.current?.fit(undefined, 48);
          }}><Focus data-icon="inline-start" /> Fit graph</Button>
          <Button type="button" size="sm" variant="outline" aria-label={expanded ? "Exit graph full screen" : "Open graph full screen"} onClick={() => setExpanded((value) => !value)}>{expanded ? <Minimize2 /> : <Maximize2 />}{expanded ? "Exit full screen" : "Full screen"}</Button>
        </div>
      </header>
      <div className="semantic-graph-filter">
        {mode === "active" ? (
          <label>
            Operation
            <select aria-label="Active API operation" value={endpointId} onChange={(event) => { setEndpointId(event.target.value); setSelection(null); }}>
              <option value="">Choose an operation…</option>
              {endpoints.map((endpoint) => (
                <option key={endpoint.id} value={endpoint.endpoint_id ?? ""}>{endpoint.label} · {endpoint.facets.operation_id ?? endpoint.endpoint_id}</option>
              ))}
            </select>
          </label>
        ) : (
          <span>{visibleNodeCount} of {graph.total_nodes} nodes · {visibleEdgeCount} of {graph.total_edges} edges</span>
        )}
        <div className="semantic-graph-legend" aria-label="Graph legend">
          {Object.entries(NODE_STYLES).filter(([type]) => graph.nodes.some((node) => node.node_type === type)).map(([type, style]) => (
            <span key={type}><i style={{ background: style.color }} />{type.replaceAll("_", " ")}</span>
          ))}
        </div>
      </div>
      <div className="semantic-graph-stage">
        <div ref={containerRef} className="semantic-graph-canvas" data-renderer="sigma" data-visible={mode === "accumulated"} data-layout={layoutState} role="img" aria-label="Semantic graph visualization" />
        <div ref={activeContainerRef} className="semantic-graph-canvas" data-renderer="cytoscape" data-visible={mode === "active"} role="img" aria-label="API operation neighborhood visualization" />
        {mode === "accumulated" && layoutState === "calculating" ? <div className="semantic-graph-empty">Laying out {graph.total_nodes} nodes and {graph.total_edges} edges…</div> : null}
        {mode === "accumulated" && layoutState === "failed" ? <div className="semantic-graph-empty" role="alert">The graph layout failed. The persisted graph remains unchanged.</div> : null}
        {mode === "active" && endpointId === "" ? <div className="semantic-graph-empty">Choose an operation to inspect its exact neighborhood.</div> : null}
        <aside className="semantic-node-inspector" aria-live="polite">
          <p>Selected graph item</p>
          {selectedNode !== null ? (
            <><h4>{selectedNode.label}</h4><dl><div><dt>Type</dt><dd>{selectedNode.node_type.replaceAll("_", " ")}</dd></div><div><dt>Endpoint</dt><dd>{selectedNode.endpoint_id ?? "Shared context"}</dd></div>{Object.entries(selectedNode.facets).map(([key, value]) => <div key={key}><dt>{key.replaceAll("_", " ")}</dt><dd>{value}</dd></div>)}</dl></>
          ) : selectedEdge !== null ? (
            <><h4>{selectedEdge.type.replaceAll("_", " ")}</h4><dl><div><dt>From</dt><dd>{graph.nodes.find(({ id }) => id === selectedEdge.source)?.label ?? selectedEdge.source}</dd></div><div><dt>To</dt><dd>{graph.nodes.find(({ id }) => id === selectedEdge.target)?.label ?? selectedEdge.target}</dd></div><div><dt>Status</dt><dd>{selectedEdge.status}</dd></div><div><dt>Confidence</dt><dd>{selectedEdge.confidence}</dd></div></dl></>
          ) : <span>Select a node or relationship to inspect it.</span>}
        </aside>
      </div>
      <div className="semantic-event-ledger" aria-live="polite">
        <div><span>Recorded event</span><strong>{frameTitle}</strong></div>
        <dl>
          <div><dt>Nodes added</dt><dd>{frame?.added_node_ids.length ?? 0}</dd></div>
          <div><dt>Nodes updated</dt><dd>{frame?.updated_node_ids.length ?? 0}</dd></div>
          <div><dt>Edges added</dt><dd>{frame?.added_edge_ids.length ?? 0}</dd></div>
          <div><dt>Graph now</dt><dd>{visibleNodeCount} / {visibleEdgeCount}</dd></div>
        </dl>
      </div>
      <footer className="semantic-playback">
        <div className="semantic-playback-meta"><strong>{trace.length === 0 ? "Persisted graph" : `${frameIndex + 1} / ${trace.length}`}</strong><span>{frameTitle}</span><span>2 seconds per frame at 1×</span></div>
        <input aria-label="Construction event" type="range" min={0} max={Math.max(0, trace.length - 1)} value={frameIndex} onChange={(event) => { setPlaying(false); setFrameIndex(Number(event.target.value)); }} />
        <div className="semantic-playback-controls">
          <Button type="button" size="icon" variant="outline" aria-label="Restart construction replay" disabled={frameIndex === 0} onClick={() => { setPlaying(false); setFrameIndex(0); }}><RotateCcw /></Button>
          <Button type="button" size="icon" variant="outline" aria-label="Previous construction event" disabled={frameIndex === 0} onClick={() => { setPlaying(false); setFrameIndex((value) => Math.max(0, value - 1)); }}><ChevronLeft /></Button>
          <Button type="button" size="icon" aria-label={playing ? "Pause construction replay" : "Play construction replay"} disabled={trace.length < 2} onClick={() => { if (frameIndex >= trace.length - 1) setFrameIndex(0); setPlaying((value) => !value); }}>{playing ? <Pause /> : <Play />}</Button>
          <Button type="button" size="icon" variant="outline" aria-label="Next construction event" disabled={frameIndex >= trace.length - 1} onClick={() => { setPlaying(false); setFrameIndex((value) => Math.min(trace.length - 1, value + 1)); }}><ChevronRight /></Button>
          <label>Speed<select aria-label="Replay speed" value={speed} onChange={(event) => setSpeed(Number(event.target.value))}><option value={0.5}>0.5×</option><option value={1}>1×</option><option value={2}>2×</option><option value={4}>4×</option><option value={8}>8×</option></select></label>
        </div>
      </footer>
    </section>
  );
}

function birthIndex(
  frames: ApiGraphView["trace"],
  field: "added_node_ids" | "added_edge_ids",
): ReadonlyMap<string, number> {
  const output = new Map<string, number>();
  for (const frame of frames) for (const id of frame[field]) if (!output.has(id)) output.set(id, frame.index);
  return output;
}
