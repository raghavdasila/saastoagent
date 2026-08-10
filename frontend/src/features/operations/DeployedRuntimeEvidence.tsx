import { memo } from "react";

import { BuildNavGraph } from "../builder/BuildNavGraph";
import type { AgentBuildView, OperationsInteractionView } from "../builder/models";

const ROUTING_EVENTS = new Set([
  "model.decision",
  "router.decision",
  "run.needs_input",
  "clarification.user_answer",
  "api.started",
  "api.result",
  "api.verification_result",
  "run.completed",
  "run.failed",
]);

export const DeployedRuntimeEvidence = memo(function DeployedRuntimeEvidence({
  interaction,
  build,
}: {
  readonly interaction: OperationsInteractionView;
  readonly build: AgentBuildView | null;
}) {
  const routed = interaction.events.filter((event) => ROUTING_EVENTS.has(event.kind));
  return <section className="deployed-runtime" aria-label={`Deployed RouteDeck evidence for interaction ${interaction.interaction_id}`}>
    <header>
      <div><p>Owner-only runtime evidence</p><h3>Deployed RouteDeck Agent</h3></div>
      <span>Session {interaction.session_id}</span>
    </header>
    {build === null
      ? <p>The exact immutable build NavGraph is unavailable.</p>
      : <BuildNavGraph build={build} />}
    <section className="deployed-runtime__router" aria-label="Deployed ToolRouter clarification subagent">
      <header><div><p>Safe decision provenance</p><h4>ToolRouter clarification subagent</h4></div><span>{routed.length} safe events</span></header>
      {routed.length === 0
        ? <p>No routing or clarification event was required for this interaction.</p>
        : <ol>{routed.map((event) => <li key={`${event.sequence}-${event.kind}`}>
          <span>{event.sequence}</span><strong>{eventLabel(event.kind)}</strong><code>{safeSummary(event.safe_data)}</code>
        </li>)}</ol>}
    </section>
  </section>;
});

function eventLabel(kind: string): string {
  return ({
    "model.decision": "Agent decision",
    "router.decision": "ToolRouter resolution",
    "run.needs_input": "Clarification requested",
    "clarification.user_answer": "Clarification answer",
    "api.started": "Supervised tool started",
    "api.result": "Supervised tool result",
    "api.verification_result": "Write verification result",
    "run.completed": "Interaction completed",
    "run.failed": "Interaction failed",
  } as Record<string, string>)[kind] ?? kind;
}

function safeSummary(value: Readonly<Record<string, unknown>>): string {
  const allowed = new Set(["resolution", "operation_id", "decision_type", "missing_params", "status", "http_status", "error_code"]);
  return JSON.stringify(Object.fromEntries(Object.entries(value).filter(([key]) => allowed.has(key))));
}
