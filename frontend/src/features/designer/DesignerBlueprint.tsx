import type { FrontendContract } from "@routedeck/core";
import { NavGraphInspector } from "@routedeck/react";
import {
  ArrowRight,
  Blocks,
  Bot,
  Database,
  PanelsTopLeft,
  ShieldCheck,
  Sparkles,
  Wrench,
} from "lucide-react";
import { memo, useMemo, type ReactNode } from "react";

import { presentNavGraphContract, presentNavGraphNodeTitle } from "@/lib/navgraphPresentation";
import type { DesignContent, DesignTopology } from "./models";


export const DesignerBlueprint = memo(function DesignerBlueprint({ content, topology, sourceInputs }: { readonly content: DesignContent; readonly topology: DesignTopology | null; readonly sourceInputs: readonly Readonly<Record<string, unknown>>[] }) {
  const lineages = sourceInputs.map(sourceLineage).filter((item): item is SourceLineage => item !== null);
  const capabilities = topology?.capabilities ?? capabilitiesFromContent(content);
  const surfaces = topology === null ? [] : runtimeSurfaces(topology);
  return <section className="designer-blueprint" aria-label="Agent design blueprint">
    <header><div><p>RouteDeck Agent design</p><h2>{content.goal || "Untitled Agent goal"}</h2></div><span>Proposed · compiled only after approval</span></header>
    <dl className="designer-blueprint__summary" aria-label="Design summary">
      <div><dt>Runtime areas</dt><dd>{topology?.nodes.length ?? 0}</dd></div>
      <div><dt>Capabilities</dt><dd>{topology?.capabilities.length ?? content.capabilities.length}</dd></div>
      <div><dt>API tools</dt><dd>{topology?.operation_ids.length ?? content.tools.length}</dd></div>
      <div><dt>Policies</dt><dd>{content.policies.length + (content.instructions.trim() ? 1 : 0)}</dd></div>
    </dl>
    <section className="designer-studio__foundation" aria-label="Agent intent and Source intelligence">
      <article className="designer-studio__intent">
        <header><Bot aria-hidden="true" /><div><p>Agent definition</p><h3>Agent intent</h3></div></header>
        <div className="designer-studio__intent-details">
          <section><span>Goal</span><strong>{content.goal || "No Agent goal has been proposed."}</strong></section>
          <section><h4>Responsibilities</h4><p>{content.instructions}</p></section>
        </div>
      </article>
      <article className="designer-studio__sources">
        <header><Database aria-hidden="true" /><div><p>Exact design inputs</p><h3>Source intelligence</h3></div></header>
        {lineages.length === 0 ? <p>No Source intelligence is available for this proposal.</p> : <div>{lineages.map((lineage) => <section key={`${lineage.sourceId}:${lineage.revisionId}`}>
          <div className="designer-studio__source-title"><strong>{lineage.displayName ?? "API Source"}</strong><span>{lineage.groups.length} semantic groups</span></div>
          <div className="designer-studio__semantic-groups">{lineage.groups.map((group) => <article key={`${lineage.sourceId}:${group.label}`}>
            <strong>{semanticGroupTitle(group)}</strong>
            <span>{group.operationIds.map(humanizeIdentifier).join(", ")}</span>
          </article>)}</div>
          <small>API version {lineage.revisionId} · operation selection {lineage.curationId}</small>
        </section>)}</div>}
      </article>
    </section>
    <section className="designer-studio__system" aria-labelledby="designer-system-title">
      <header><div><p>Prepopulated from Agent and Source state</p><h3 id="designer-system-title">Proposed design system</h3></div><span>Review before approval</span></header>
      <div className="designer-studio__system-grid">
        <StudioList icon={<Sparkles aria-hidden="true" />} title="Proposed features" items={content.features} presentItem={(item) => presentDesignText(item, lineages)} />
        <StudioList icon={<Blocks aria-hidden="true" />} title="Proposed behaviors" items={content.behaviors} presentItem={(item) => presentDesignText(item, lineages)} />
        <StudioList icon={<ShieldCheck aria-hidden="true" />} title="Policies" items={content.policies} />
        <section className="designer-studio__panel designer-studio__capability-panel">
          <header><Wrench aria-hidden="true" /><div><p>Source-owned operation boundary</p><h3>Capabilities and tools</h3></div></header>
          {capabilities.length === 0 ? <p>Save the proposal to validate capability ownership.</p> : <div>{capabilities.map((capability) => <article key={capability.id}>
            <div><strong>{humanizeIdentifier(capability.title)}</strong><span>{capability.operation_ids.length} tools</span></div>
            <ul>{capability.operation_ids.map((operation) => <li key={operation}><span>{humanizeIdentifier(operation)}</span><code>{operation}</code></li>)}</ul>
          </article>)}</div>}
        </section>
        <section className="designer-studio__panel designer-studio__surface-panel">
          <header><PanelsTopLeft aria-hidden="true" /><div><p>Projected interaction UI</p><h3>Runtime surfaces</h3></div></header>
          {surfaces.length === 0 ? <p>Save the proposal to validate its runtime surfaces.</p> : <ul>{surfaces.map((surface) => <li key={surface.id}>
            <div><strong>{surface.title}</strong><span>{surface.role}</span></div><code>{surface.id}</code>
          </li>)}</ul>}
        </section>
      </div>
    </section>
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
  const reachableNodeIds = topology.transitions
    .filter((transition) => transition.source_node_id === topology.entry_node_id)
    .map((transition) => transition.target_node_id);
  return <section className="designer-navgraph" aria-label="Proposed RouteDeck NavGraph preview">
    <header><div><p>Exact Designer topology</p><h3>Proposed RouteDeck NavGraph</h3></div><code title={topology.topology_hash}>{topology.topology_hash.slice(0, 16)}…</code></header>
    <p>The same topology identity is compiled into the immutable build after approval. Select a runtime area to inspect its surfaces, tools, and legal transitions.</p>
    {topology.mode === "legacy_single_area" ? <p className="designer-navgraph__legacy" role="status">This immutable proposal predates capability-owned runtime areas. Its existing build remains reproducible; create a fresh proposal to use the current multi-area design.</p> : null}
    <div className="designer-navgraph__inspector">
      <NavGraphInspector
        contract={contract}
        currentNodeId={topology.entry_node_id}
        reachableNodeIds={reachableNodeIds}
        activeSurfaceIds={node.surface_ids}
        legalOperationIds={[...node.navigation_operation_ids, ...node.operation_ids]}
        canvasHeight={topology.nodes.length === 1 ? "16rem" : "clamp(22rem, 44vh, 32rem)"}
        showMiniMap={false}
      />
    </div>
    <div className="designer-navgraph__areas" aria-label="Runtime areas">{topology.nodes.map((runtimeNode) => <article key={runtimeNode.id}>
      <div><h4>{presentNavGraphNodeTitle(runtimeNode.id, runtimeNode.title, topology.entry_node_id)}</h4><span>{runtimeNode.id === topology.entry_node_id ? "Entry" : "Capability area"}</span></div>
      <p>{runtimeNode.capability_ids.length} capabilities · {runtimeNode.operation_ids.length} API tools · {runtimeNode.navigation_operation_ids.length} navigation actions</p>
    </article>)}</div>
    <div className="designer-navgraph__capabilities" aria-label="Proposed capability map">{topology.capabilities.map((capability) => <article key={capability.id}><div><h4>{capability.title}</h4><span>{capability.operation_ids.length} tools</span></div><ul>{capability.operation_ids.map((operation) => <li key={operation}>{operation}</li>)}</ul></article>)}</div>
  </section>;
}

function designFrontendContract(topology: DesignTopology): FrontendContract {
  const nodes = Object.fromEntries(topology.nodes.map((node) => [node.id, {
    id: node.id,
    title: node.title,
    route_template: node.route_template,
    deep_link_policy: "shareable" as const,
    conversation_input: { enabled: true, disabled_message: null },
    operation_ids: [...node.navigation_operation_ids, ...node.operation_ids],
    surfaces: surfaceSlots(node.surface_ids),
  }]));
  const surfaces = Object.fromEntries(Array.from(new Set(topology.nodes.flatMap((node) => node.surface_ids))).map((id) => [id, {
    id,
    component: id,
    lifecycle: "stable" as const,
    affordances: [],
    public_props_schema: {},
  }]));
  return presentNavGraphContract({
    name: "corpus-agent-design-preview",
    entry_node_id: topology.entry_node_id,
    nodes,
    surfaces,
    transitions: topology.transitions.map((transition) => ({
      source: transition.source_node_id,
      target: transition.target_node_id,
      operation_id: transition.operation_id,
      outcome: transition.outcome,
    })),
  });
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

function StudioList({ icon, title, items, presentItem = (item) => item }: { readonly icon: ReactNode; readonly title: string; readonly items: readonly string[]; readonly presentItem?: (item: string) => string }) {
  return <section className="designer-studio__panel">
    <header>{icon}<div><p>Owner-visible configuration</p><h3>{title}</h3></div></header>
    {items.length === 0 ? <p>None proposed.</p> : <ul>{items.map((item) => <li key={item}>{presentItem(item)}</li>)}</ul>}
  </section>;
}

function capabilitiesFromContent(content: DesignContent): DesignTopology["capabilities"] {
  return content.capabilities.map((value, index) => {
    const [title, rawOperations = ""] = value.split(":", 2);
    const operationIds = rawOperations.split(",").map((item) => item.trim()).filter(Boolean);
    return {
      id: `draft-capability-${index}`,
      title: title?.trim() || value,
      operation_ids: operationIds.length > 0 ? operationIds : content.tools,
      node_id: "draft",
    };
  });
}

function runtimeSurfaces(topology: DesignTopology): readonly RuntimeSurface[] {
  const seen = new Set<string>();
  return topology.nodes.flatMap((node) => node.surface_ids.flatMap((id) => {
    if (seen.has(id)) return [];
    seen.add(id);
    if (id.endsWith(".clarification")) return [{ id, title: "Clarification", role: "Conversational waiting" }];
    if (id.endsWith(".toolrouter_status")) return [{ id, title: "Tool routing status", role: "Routing evidence" }];
    if (id.endsWith(".delivery_status")) return [{ id, title: "Delivery status", role: "Visible runtime failure" }];
    return [{
      id,
      title: node.id === topology.entry_node_id ? "Agent workspace" : `${humanizeIdentifier(node.title)} workspace`,
      role: node.id === topology.entry_node_id ? "Primary interaction" : "Capability interaction",
    }];
  }));
}

function humanizeIdentifier(value: string): string {
  const separated = value
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[._-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return separated ? separated[0]!.toUpperCase() + separated.slice(1) : value;
}

function presentDesignText(value: string, lineages: readonly SourceLineage[]): string {
  let presented = value.replace(/[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+/g, (identifier) =>
    identifier.replaceAll("_", " "),
  );
  for (const group of lineages.flatMap((lineage) => lineage.groups)) {
    if (group.label && presented.includes(group.label)) {
      presented = presented.replaceAll(group.label, semanticGroupTitle(group));
    }
  }
  return presented;
}

function semanticGroupTitle(group: SourceLineage["groups"][number]): string {
  const explicitWords = /[\s._-]/.test(group.label) || /[a-z][A-Z]/.test(group.label);
  if (explicitWords || group.operationIds.length === 0) return humanizeIdentifier(group.label);
  return `${group.operationIds.map(humanizeIdentifier).join(" and ")} context`;
}

interface RuntimeSurface {
  readonly id: string;
  readonly title: string;
  readonly role: string;
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
