import { memo } from "react";

import type { SandboxRunView } from "./models";


export const SandboxRuntimeEvidence = memo(function SandboxRuntimeEvidence({ run }: { readonly run: SandboxRunView }) {
  const projection = parseProjection(run.routedeck_projection);
  const routing = run.events.filter((event) => ["model.decision", "router.decision", "run.needs_input", "clarification.user_answer", "api.started", "api.result", "run.completed", "run.failed"].includes(event.kind));
  return <section className="sandbox-runtime" aria-label={`RouteDeck runtime for run ${run.id}`}>
    <header><div><p>Isolated session</p><h3>RouteDeck runtime</h3></div><code>{run.runtime_session_id}</code></header>
    {projection === null ? <p>The persisted RouteDeck projection is unavailable.</p> : <div className="sandbox-runtime__projection">
      <dl><div><dt>Current node</dt><dd>{projection.current.node_id}</dd></div><div><dt>Legal operations</dt><dd>{projection.legal_operations.length}</dd></div><div><dt>Suggested actions</dt><dd>{projection.suggested_actions.length}</dd></div></dl>
      <div><section aria-label="Projected surfaces"><h4>Projected surfaces</h4><ul>{projection.surfaces.map((surface) => <li key={surface.surface_id}><strong>{surface.component}</strong><span>{surface.surface_id}</span></li>)}</ul></section>
      <section aria-label="Suggested actions"><h4>Suggested actions</h4>{projection.suggested_actions.length === 0 ? <p>No static action is legal in this state.</p> : <ul>{projection.suggested_actions.map((action) => <li key={action.action_id}>{action.label}</li>)}</ul>}</section></div>
    </div>}
    <section className="sandbox-runtime__router" aria-label="ToolRouter clarification subagent">
      <header><div><p>Resolution trace</p><h4>ToolRouter clarification subagent</h4></div><span>{routing.length} safe events</span></header>
      {routing.length === 0 ? <p>No routing decision was needed for this response.</p> : <ol>{routing.map((event) => <li key={`${event.sequence}-${event.kind}`}><span>{event.sequence}</span><strong>{eventLabel(event.kind)}</strong><code>{safeSummary(event.safe_data)}</code></li>)}</ol>}
    </section>
  </section>;
});

interface Projection {
  readonly current: { readonly node_id: string };
  readonly legal_operations: readonly unknown[];
  readonly suggested_actions: readonly { readonly action_id: string; readonly label: string }[];
  readonly surfaces: readonly { readonly surface_id: string; readonly component: string }[];
}

function parseProjection(value: Readonly<Record<string, unknown>>): Projection | null {
  if (!record(value.current) || typeof value.current.node_id !== "string" || !Array.isArray(value.legal_operations) || !Array.isArray(value.suggested_actions) || !record(value.surfaces)) return null;
  const actions = value.suggested_actions.filter((item): item is { action_id: string; label: string } => record(item) && typeof item.action_id === "string" && typeof item.label === "string");
  const surfaces = Object.values(value.surfaces).flatMap((item) => Array.isArray(item) ? item : item === null ? [] : [item]).filter((item): item is { surface_id: string; component: string } => record(item) && typeof item.surface_id === "string" && typeof item.component === "string");
  return actions.length === value.suggested_actions.length ? { current: { node_id: value.current.node_id }, legal_operations: value.legal_operations, suggested_actions: actions, surfaces } : null;
}

function eventLabel(kind: string): string { return ({ "model.decision": "Agent decision", "router.decision": "ToolRouter resolution", "run.needs_input": "Clarification requested", "clarification.user_answer": "Owner clarification", "api.started": "Supervised tool started", "api.result": "Supervised tool result", "run.completed": "Run completed", "run.failed": "Run failed" } as Record<string, string>)[kind] ?? kind; }
function safeSummary(value: Readonly<Record<string, unknown>>): string { const allowed = ["resolution", "operation_id", "decision_type", "candidates", "missing_params", "status", "http_status", "error_code"]; return JSON.stringify(Object.fromEntries(Object.entries(value).filter(([key]) => allowed.includes(key)))); }
function record(value: unknown): value is Readonly<Record<string, unknown>> { return typeof value === "object" && value !== null && !Array.isArray(value); }
