import { memo } from "react";
import { ArrowRight } from "lucide-react";

import type { DesignContent, DesignTopology } from "./models";


export const DesignerBlueprint = memo(function DesignerBlueprint({ content, topology, sourceInputs }: { readonly content: DesignContent; readonly topology: DesignTopology | null; readonly sourceInputs: readonly Readonly<Record<string, unknown>>[] }) {
  const lineages = sourceInputs.map(sourceLineage).filter((item): item is SourceLineage => item !== null);
  return <section className="designer-blueprint" aria-label="Agent design blueprint">
    <header><div><p>RouteDeck design topology</p><h2>{content.goal || "Untitled Agent goal"}</h2></div><span>Proposed · compiled at build</span></header>
    <div className="designer-blueprint__flow" role="region" aria-label="Proposed RouteDeck topology">
      <BlueprintColumn title="Features" items={content.features} tone="feature" />
      <FlowArrow label="provides" />
      <BlueprintColumn title="Capabilities" items={content.capabilities} tone="capability" />
      <FlowArrow label="permits" />
      <BlueprintColumn title="Tools" items={content.tools} tone="tool" />
    </div>
    <div className="designer-blueprint__rails">
      <BlueprintColumn title="Behaviors" items={content.behaviors} tone="behavior" />
      <BlueprintColumn title="Policies" items={content.policies} tone="policy" />
    </div>
    {topology === null ? <p role="status">Save the customization to validate and refresh the exact RouteDeck NavGraph preview.</p> : <TopologyPreview topology={topology} />}
    <section className="designer-blueprint__lineage" aria-label="Immutable Source lineage">
      <h3>Immutable Source lineage</h3>
      {lineages.length === 0 ? <p>No Source lineage is available.</p> : <div>{lineages.map((lineage) => <article key={`${lineage.sourceId}:${lineage.revisionId}`}>
        <strong>{lineage.sourceId}</strong>
        <span>Revision {lineage.revisionId}</span>
        <span>Curation {lineage.curationId}</span>
        {lineage.groups.map((group) => <p key={`${lineage.sourceId}:${group.label}`}><b>{group.label}</b> · {group.operationIds.join(", ")}</p>)}
      </article>)}</div>}
    </section>
    <article><h3>Compiled instruction</h3><p>{content.instructions}</p></article>
  </section>;
});

function TopologyPreview({ topology }: { readonly topology: DesignTopology }) {
  const node = topology.nodes[0];
  return <section className="designer-navgraph" aria-label="Compiled RouteDeck NavGraph preview">
    <header><div><p>Exact build topology</p><h3>RouteDeck NavGraph preview</h3></div><code title={topology.topology_hash}>{topology.topology_hash.slice(0, 16)}…</code></header>
    <svg viewBox="0 0 720 220" role="img" aria-label={`${topology.nodes.length} proposed NavGraph nodes`}>
      <g transform="translate(100 42)"><rect width="520" height="132" rx="18" /><foreignObject x="20" y="14" width="480" height="46"><div className="designer-navgraph__title">{node.title}</div></foreignObject><text x="20" y="76">{node.id}</text><text x="20" y="99">{node.capability_ids.length} capabilities · {node.operation_ids.length} tools</text><text x="20" y="122">{node.policy_count} policies · {node.surface_ids.length} surfaces</text></g>
    </svg>
    <div>{topology.capabilities.map((capability) => <article key={capability.id}><h4>{capability.title}</h4><code>{capability.id}</code><ul>{capability.operation_ids.map((operation) => <li key={operation}>{operation}</li>)}</ul></article>)}</div>
  </section>;
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
  readonly groups: readonly { readonly label: string; readonly operationIds: readonly string[] }[];
}

function sourceLineage(value: Readonly<Record<string, unknown>>): SourceLineage | null {
  const sourceId = typeof value.source_id === "string" ? value.source_id : null;
  const revisionId = typeof value.source_revision_id === "string" ? value.source_revision_id : null;
  const curationId = typeof value.curation_id === "string" ? value.curation_id : null;
  if (sourceId === null || revisionId === null || curationId === null) return null;
  const groups = Array.isArray(value.semantic_groups) ? value.semantic_groups.flatMap((entry) => {
    if (typeof entry !== "object" || entry === null) return [];
    const candidate = entry as Readonly<Record<string, unknown>>;
    if (typeof candidate.label !== "string" || !Array.isArray(candidate.operation_ids) || !candidate.operation_ids.every((item) => typeof item === "string")) return [];
    return [{ label: candidate.label, operationIds: candidate.operation_ids as readonly string[] }];
  }) : [];
  return { sourceId, revisionId, curationId, groups };
}
