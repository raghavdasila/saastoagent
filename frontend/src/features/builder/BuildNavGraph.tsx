import { decodeFrontendContract, type FrontendContract } from "@routedeck/core";
import { NavGraphInspector } from "@routedeck/react";
import { memo, useMemo, useState } from "react";

import { presentNavGraphContract, presentNavGraphNodeTitle, presentSemanticLabel } from "@/lib/navgraphPresentation";
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
  const frontendContract = useMemo(() => parseFrontendContract(build.frontend_contract), [build.frontend_contract]);
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
  if (build.navgraph_hash === null || graph === null) return <p role="alert">The exact immutable RouteDeck NavGraph is unavailable for this build.</p>;
  if (frontendContract === null) return <p role="alert">The exact RouteDeck frontend contract is unavailable for this build.</p>;
  const presentedContract = presentNavGraphContract(frontendContract);
  const entryNodeId = frontendContract.entry_node_id;
  const selectedNode = graph.nodes.find((node) => node.id === (focusedNodeId ?? entryNodeId))
    ?? graph.nodes.find((node) => node.id === entryNodeId)
    ?? graph.nodes[0];
  const totals = graph.nodes.reduce(
    (result, node) => ({
      capabilities: result.capabilities + node.capabilities.length,
      operations: result.operations + node.operations.length,
      policies: result.policies + node.policy_refs.length,
      surfaces: result.surfaces + surfaceCount(node.surfaces),
    }),
    { capabilities: 0, operations: 0, policies: 0, surfaces: 0 },
  );

  const currentNode = frontendContract.nodes[entryNodeId];
  const legalOperationIds = currentNode?.operation_ids ?? [];
  const reachableNodeIds = Array.from(new Set(frontendContract.transitions
    .filter((transition) => transition.source === entryNodeId && legalOperationIds.includes(transition.operation_id))
    .map((transition) => transition.target)));
  const activeSurfaceIds = currentNode === undefined ? [] : surfaceIds(currentNode.surfaces);

  return <section className="build-navgraph" aria-label={`RouteDeck NavGraph for build ${build.id}`}>
    <header>
      <div><p>Immutable Agent application</p><h3>Runtime map</h3><span>Explore the exact navigation, capabilities, and supervised tools compiled for this build.</span></div>
      <code title={build.navgraph_hash}>{build.navgraph_hash.slice(0, 16)}…</code>
    </header>
    {topologyHash(graph.nodes[0]?.public_metadata) === null ? null : <p>Designer topology <code>{topologyHash(graph.nodes[0]!.public_metadata)!.slice(0, 16)}…</code></p>}
    <dl className="build-navgraph__summary" aria-label="Compiled Agent map summary">
      <div><dt>Runtime areas</dt><dd>{graph.nodes.length}</dd></div>
      <div><dt>Transitions</dt><dd>{graph.transitions.length}</dd></div>
      <div><dt>Capabilities</dt><dd>{totals.capabilities}</dd></div>
      <div><dt>Supervised tools</dt><dd>{totals.operations}</dd></div>
      <div><dt>Policies</dt><dd>{totals.policies}</dd></div>
      <div><dt>Surfaces</dt><dd>{totals.surfaces}</dd></div>
    </dl>
    <div className="build-navgraph__inspector">
      <NavGraphInspector
        contract={presentedContract}
        currentNodeId={entryNodeId}
        reachableNodeIds={reachableNodeIds}
        activeSurfaceIds={activeSurfaceIds}
        legalOperationIds={legalOperationIds}
        canvasHeight="clamp(30rem, 62vh, 50rem)"
        showMiniMap={graph.nodes.length > 4}
        onFocusChange={setFocusedNodeId}
      />
    </div>
    {selectedNode === undefined ? null : <article className="build-navgraph__node" aria-live="polite">
      <header><div><p>{selectedNode.id === entryNodeId ? "Entry runtime area" : "Selected runtime area"}</p><h4>{presentNavGraphNodeTitle(selectedNode.id, selectedNode.title, entryNodeId)}</h4></div><code>{selectedNode.id}</code></header>
      <dl><div><dt>Policies</dt><dd>{selectedNode.policy_refs.length}</dd></div><div><dt>Suggested actions</dt><dd>{selectedNode.suggested_actions.length}</dd></div><div><dt>Surface slots</dt><dd>{surfaceCount(selectedNode.surfaces)}</dd></div></dl>
      <section aria-labelledby={`capabilities-${build.id}`}><h5 id={`capabilities-${build.id}`}>Capabilities</h5><ul>{selectedNode.capabilities.length === 0 ? <li><span>No capability is declared for this runtime area.</span></li> : selectedNode.capabilities.map((capability) => <li key={capability.id}><strong>{presentSemanticLabel(capability.title)}</strong><span>{capability.operations?.length ?? 0} supervised tools</span></li>)}</ul></section>
      <section aria-labelledby={`tools-${build.id}`}><h5 id={`tools-${build.id}`}>Supervised tools</h5><ul>{selectedNode.operations.length === 0 ? <li><span>No tool is available in this runtime area.</span></li> : selectedNode.operations.map((operation) => <li key={operation.id}>
          <strong>{String(operation.public_metadata.source_operation_id ?? operation.title)}</strong>
          <span>{String(operation.public_metadata.method ?? "")} {String(operation.public_metadata.path_template ?? "")}</span>
          <small>{presentSafety(operation.safety_class, operation.review_policy)}</small>
        </li>)}</ul></section>
    </article>}
  </section>;
});

function parseGraph(value: Readonly<Record<string, unknown>>): { readonly nodes: readonly GraphNode[]; readonly transitions: readonly GraphTransition[] } | null {
  if (!Array.isArray(value.nodes) || !Array.isArray(value.transitions)) return null;
  const nodes = value.nodes.filter(isGraphNode);
  const transitions = value.transitions.filter(isGraphTransition);
  return nodes.length === value.nodes.length && transitions.length === value.transitions.length ? { nodes, transitions } : null;
}

function parseFrontendContract(value: Readonly<Record<string, unknown>>): FrontendContract | null {
  try {
    return decodeFrontendContract(value);
  } catch {
    return null;
  }
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
function surfaceIds(value: object): string[] { return Object.values(value as Readonly<Record<string, unknown>>).flatMap((item) => typeof item === "string" ? [item] : Array.isArray(item) ? item.filter((entry): entry is string => typeof entry === "string") : []); }
function topologyHash(value: Readonly<Record<string, unknown>> | undefined): string | null { const topology = value?.designer_topology; return record(topology) && typeof topology.topology_hash === "string" ? topology.topology_hash : null; }
function presentSafety(safetyClass: string, reviewPolicy: string): string {
  const safety = safetyClass === "read_external"
    ? "Read-only API call"
    : safetyClass === "write_external"
      ? "API change"
      : presentSemanticLabel(safetyClass);
  return reviewPolicy === "required" ? `${safety} · owner review required` : safety;
}
