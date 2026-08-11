import type { FrontendContract } from "@routedeck/core";
import { NavGraphInspector } from "@routedeck/react";
import { ArrowRight } from "lucide-react";
import { memo, useMemo } from "react";

import type { DesignContent, DesignTopology } from "./models";


export const DesignerBlueprint = memo(function DesignerBlueprint({ content, topology, sourceInputs }: { readonly content: DesignContent; readonly topology: DesignTopology | null; readonly sourceInputs: readonly Readonly<Record<string, unknown>>[] }) {
  const lineages = sourceInputs.map(sourceLineage).filter((item): item is SourceLineage => item !== null);
  return <section className="designer-blueprint" aria-label="Agent design blueprint">
    <header><div><p>RouteDeck Agent design</p><h2>{content.goal || "Untitled Agent goal"}</h2></div><span>Proposed · compiled only after approval</span></header>
    <dl className="designer-blueprint__summary" aria-label="Design summary">
      <div><dt>Runtime areas</dt><dd>{topology?.nodes.length ?? 0}</dd></div>
      <div><dt>Capabilities</dt><dd>{topology?.capabilities.length ?? content.capabilities.length}</dd></div>
      <div><dt>API tools</dt><dd>{topology?.operation_ids.length ?? content.tools.length}</dd></div>
      <div><dt>Policies</dt><dd>{content.policies.length + (content.instructions.trim() ? 1 : 0)}</dd></div>
    </dl>
    {topology === null ? <p role="status">Save the customization to validate and refresh the exact RouteDeck NavGraph preview.</p> : <TopologyPreview topology={topology} />}
    <details className="designer-blueprint__mapping">
      <summary>Review feature, capability, policy, and tool mapping</summary>
      <div className="designer-blueprint__flow" role="region" aria-label="Proposed RouteDeck topology">
        <BlueprintColumn title="Features" items={content.features} tone="feature" />
        <FlowArrow label="provides" />
        <BlueprintColumn title="Capabilities" items={content.capabilities} tone="capability" />
        <FlowArrow label="permits" />
        <BlueprintColumn title="Tools" items={content.tools} tone="tool" />
      </div>
      <div className="designer-blueprint__rails"><BlueprintColumn title="Behaviors" items={content.behaviors} tone="behavior" /><BlueprintColumn title="Policies" items={content.policies} tone="policy" /></div>
    </details>
    <details className="designer-blueprint__lineage">
      <summary>Inspect immutable Source lineage</summary>
      <section aria-label="Immutable Source lineage">
        {lineages.length === 0 ? <p>No Source lineage is available.</p> : <div>{lineages.map((lineage) => <article key={`${lineage.sourceId}:${lineage.revisionId}`}>
          <strong>{lineage.displayName ?? lineage.sourceId}</strong>
          <span>Source {lineage.sourceId}</span>
          <span>API version {lineage.revisionId}</span>
          <span>Operation selection {lineage.curationId}</span>
          {lineage.groups.map((group) => <p key={`${lineage.sourceId}:${group.label}`}><b>{group.label}</b> · {group.operationIds.join(", ")}</p>)}
        </article>)}</div>}
      </section>
    </details>
    <details className="designer-blueprint__instruction"><summary>Inspect compiled Agent instruction</summary><p>{content.instructions}</p></details>
  </section>;
});

function TopologyPreview({ topology }: { readonly topology: DesignTopology }) {
  const node = topology.nodes[0];
  const contract = useMemo(() => designFrontendContract(topology), [topology]);
  if (node === undefined) return <p role="alert">The proposed RouteDeck NavGraph is unavailable.</p>;
  return <section className="designer-navgraph" aria-label="Proposed RouteDeck NavGraph preview">
    <header><div><p>Exact Designer topology</p><h3>Proposed RouteDeck NavGraph</h3></div><code title={topology.topology_hash}>{topology.topology_hash.slice(0, 16)}…</code></header>
    <p>The same topology identity is compiled into the immutable build after approval. Select the runtime area to inspect its surfaces, tools, and transitions.</p>
    <div className="designer-navgraph__inspector">
      <NavGraphInspector
        contract={contract}
        currentNodeId={topology.entry_node_id}
        reachableNodeIds={[topology.entry_node_id]}
        activeSurfaceIds={node.surface_ids}
        legalOperationIds={node.operation_ids}
        canvasHeight="clamp(24rem, 52vh, 38rem)"
        showMiniMap={topology.nodes.length > 1}
      />
    </div>
    <div className="designer-navgraph__capabilities" aria-label="Proposed capability map">{topology.capabilities.map((capability) => <article key={capability.id}><div><h4>{capability.title}</h4><span>{capability.operation_ids.length} tools</span></div><ul>{capability.operation_ids.map((operation) => <li key={operation}>{operation}</li>)}</ul></article>)}</div>
  </section>;
}

function designFrontendContract(topology: DesignTopology): FrontendContract {
  const nodes = Object.fromEntries(topology.nodes.map((node) => [node.id, {
    id: node.id,
    title: node.title,
    route_template: node.id === topology.entry_node_id ? "/" : `/${node.id.replaceAll(".", "/")}`,
    deep_link_policy: "shareable" as const,
    conversation_input: { enabled: true, disabled_message: null },
    operation_ids: [...node.operation_ids],
    surfaces: surfaceSlots(node.surface_ids),
  }]));
  const surfaces = Object.fromEntries(Array.from(new Set(topology.nodes.flatMap((node) => node.surface_ids))).map((id) => [id, {
    id,
    component: id,
    lifecycle: "stable" as const,
    affordances: [],
    public_props_schema: {},
  }]));
  return {
    name: "corpus-agent-design-preview",
    entry_node_id: topology.entry_node_id,
    nodes,
    surfaces,
    transitions: topology.nodes.flatMap((node) => node.operation_ids.map((operationId) => ({ source: node.id, target: node.id, operation_id: operationId, outcome: "observed" }))),
  };
}

function surfaceSlots(surfaceIds: readonly string[]) {
  const active = surfaceIds.find((id) => id.endsWith(".home")) ?? surfaceIds[0] ?? null;
  const rest = surfaceIds.filter((id) => id !== active);
  return {
    active,
    frame: [], peer: [], form: [], review: [], diagnostic: [],
    detail: rest.filter((id) => id.includes("clarification")),
    status: rest.filter((id) => id.includes("status") && !id.includes("delivery")),
    error: rest.filter((id) => id.includes("delivery")),
  };
}

function BlueprintColumn({ title, items, tone }: { readonly title: string; readonly items: readonly string[]; readonly tone: string }) {
  return <section className={`designer-blueprint__column designer-blueprint__column--${tone}`} aria-label={title}>
    <h3>{title}</h3>
    {items.length === 0 ? <p>None selected</p> : <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>}
  </section>;
}

function FlowArrow({ label }: { readonly label: string }) {
  return <div className="designer-blueprint__arrow" aria-hidden="true"><span>{label}</span><ArrowRight size={22} /></div>;
}

interface SourceLineage {
  readonly sourceId: string;
  readonly revisionId: string;
  readonly curationId: string;
  readonly displayName: string | null;
  readonly groups: readonly { readonly label: string; readonly operationIds: readonly string[] }[];
}

function sourceLineage(value: Readonly<Record<string, unknown>>): SourceLineage | null {
  const sourceId = typeof value.source_id === "string" ? value.source_id : null;
  const revisionId = typeof value.source_revision_id === "string" ? value.source_revision_id : null;
  const curationId = typeof value.curation_id === "string" ? value.curation_id : null;
  if (sourceId === null || revisionId === null || curationId === null) return null;
  const displayName = typeof value.display_name === "string" && value.display_name ? value.display_name : null;
  const groups = Array.isArray(value.semantic_groups) ? value.semantic_groups.flatMap((entry) => {
    if (typeof entry !== "object" || entry === null) return [];
    const candidate = entry as Readonly<Record<string, unknown>>;
    if (typeof candidate.label !== "string" || !Array.isArray(candidate.operation_ids) || !candidate.operation_ids.every((item) => typeof item === "string")) return [];
    return [{ label: candidate.label, operationIds: candidate.operation_ids as readonly string[] }];
  }) : [];
  return { sourceId, revisionId, curationId, displayName, groups };
}
