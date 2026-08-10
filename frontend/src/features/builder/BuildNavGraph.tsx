import { memo, useMemo } from "react";

import type { AgentBuildView } from "./models";

interface GraphNode {
  readonly id: string;
  readonly title: string;
  readonly operations: readonly GraphOperation[];
  readonly capabilities: readonly { readonly id: string; readonly title: string; readonly operations?: readonly { readonly id: string }[] }[];
  readonly policy_refs: readonly { readonly id: string }[];
  readonly suggested_actions: readonly { readonly id: string; readonly label?: string | null }[];
  readonly surfaces: Readonly<Record<string, unknown>>;
  readonly public_metadata: Readonly<Record<string, unknown>>;
}

interface GraphOperation {
  readonly id: string;
  readonly title: string;
  readonly safety_class: string;
  readonly review_policy: string;
  readonly public_metadata: Readonly<Record<string, unknown>>;
}

interface GraphTransition {
  readonly source: { readonly id: string };
  readonly target: { readonly id: string };
  readonly operation: { readonly id: string };
  readonly outcome: string;
}

export const BuildNavGraph = memo(function BuildNavGraph({ build }: { readonly build: AgentBuildView }) {
  const graph = useMemo(() => parseGraph(build.compiled_navgraph), [build.compiled_navgraph]);
  if (build.navgraph_hash === null || graph === null) return <p>RouteDeck NavGraph unavailable for this build.</p>;
  const nodeById = new Map(graph.nodes.map((node, index) => [node.id, { node, index }]));
  return <section className="build-navgraph" aria-label={`RouteDeck NavGraph for build ${build.id}`}>
    <header>
      <div><p>Immutable RouteDeck application</p><h3>NavGraph</h3></div>
      <code title={build.navgraph_hash}>{build.navgraph_hash.slice(0, 16)}…</code>
    </header>
    {topologyHash(graph.nodes[0]?.public_metadata) === null ? null : <p>Designer topology <code>{topologyHash(graph.nodes[0]!.public_metadata)!.slice(0, 16)}…</code></p>}
    <svg viewBox={`0 0 ${Math.max(720, graph.nodes.length * 560 + 160)} 230`} role="img" aria-label={`${graph.nodes.length} NavGraph nodes and ${graph.transitions.length} transitions`}>
      <defs><marker id={`arrow-${build.id}`} markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" /></marker></defs>
      {graph.transitions.map((transition, index) => {
        const source = nodeById.get(transition.source.id)?.index ?? 0;
        const target = nodeById.get(transition.target.id)?.index ?? source;
        const x1 = 360 + source * 560;
        const x2 = 360 + target * 560;
        const loop = source === target;
        return <g key={`${transition.operation.id}-${index}`}>
          <path className="build-navgraph__edge" d={loop ? `M ${x1 + 250} 110 C ${x1 + 320} 30, ${x1 - 320} 30, ${x1 - 250} 110` : `M ${x1 + 250} 110 L ${x2 - 250} 110`} markerEnd={`url(#arrow-${build.id})`} />
          <text x={(x1 + x2) / 2} y={loop ? 34 : 96}>{transition.outcome}</text>
        </g>;
      })}
      {graph.nodes.map((node, index) => <g key={node.id} transform={`translate(${110 + index * 560} 72)`}>
        <rect width="500" height="96" rx="16" />
        <foreignObject x="16" y="10" width="468" height="36"><div className="build-navgraph__title">{node.title}</div></foreignObject>
        <text x="16" y="61">{node.id}</text>
        <text x="16" y="82">{node.operations.length} tools · {node.capabilities.length} capabilities</text>
      </g>)}
    </svg>
    <div className="build-navgraph__contracts">
      {graph.nodes.map((node) => <article key={node.id}>
        <h4>{node.title}</h4>
        <dl><div><dt>Policies</dt><dd>{node.policy_refs.length}</dd></div><div><dt>Suggested actions</dt><dd>{node.suggested_actions.length}</dd></div><div><dt>Surface slots</dt><dd>{surfaceCount(node.surfaces)}</dd></div></dl>
        <ul>{node.capabilities.map((capability) => <li key={capability.id}><strong>{capability.title}</strong><span>{capability.operations?.length ?? 0} tools</span></li>)}</ul>
        <ul>{node.operations.map((operation) => <li key={operation.id}>
          <strong>{String(operation.public_metadata.source_operation_id ?? operation.title)}</strong>
          <span>{String(operation.public_metadata.method ?? "")} {String(operation.public_metadata.path_template ?? "")}</span>
          <small>{operation.safety_class}{operation.review_policy === "required" ? " · review required" : ""}</small>
        </li>)}</ul>
      </article>)}
    </div>
  </section>;
});

function parseGraph(value: Readonly<Record<string, unknown>>): { readonly nodes: readonly GraphNode[]; readonly transitions: readonly GraphTransition[] } | null {
  if (!Array.isArray(value.nodes) || !Array.isArray(value.transitions)) return null;
  const nodes = value.nodes.filter(isGraphNode);
  const transitions = value.transitions.filter(isGraphTransition);
  return nodes.length === value.nodes.length && transitions.length === value.transitions.length ? { nodes, transitions } : null;
}

function isGraphNode(value: unknown): value is GraphNode {
  if (!record(value)) return false;
  return typeof value.id === "string" && typeof value.title === "string" && Array.isArray(value.operations) && value.operations.every(isGraphOperation) && Array.isArray(value.capabilities) && Array.isArray(value.policy_refs) && Array.isArray(value.suggested_actions) && record(value.surfaces) && record(value.public_metadata);
}

function isGraphOperation(value: unknown): value is GraphOperation {
  return record(value) && typeof value.id === "string" && typeof value.title === "string" && typeof value.safety_class === "string" && typeof value.review_policy === "string" && record(value.public_metadata);
}

function isGraphTransition(value: unknown): value is GraphTransition {
  return record(value) && record(value.source) && typeof value.source.id === "string" && record(value.target) && typeof value.target.id === "string" && record(value.operation) && typeof value.operation.id === "string" && typeof value.outcome === "string";
}

function record(value: unknown): value is Readonly<Record<string, unknown>> { return typeof value === "object" && value !== null && !Array.isArray(value); }
function surfaceCount(value: Readonly<Record<string, unknown>>): number { return Object.values(value).reduce<number>((total, item) => total + (Array.isArray(item) ? item.length : item === null ? 0 : 1), 0); }
function topologyHash(value: Readonly<Record<string, unknown>> | undefined): string | null { const topology = value?.designer_topology; return record(topology) && typeof topology.topology_hash === "string" ? topology.topology_hash : null; }
