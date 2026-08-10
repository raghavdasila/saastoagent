import { useEffect, useState, useSyncExternalStore } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { Button } from "@/components/ui/button";
import { Field, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { completedOutcome } from "../agents/operationResult";
import type { AgentRuntimeClient } from "../builder/client";
import type { AgentBuildView, OperationsInteractionView } from "../builder/models";
import type { AgentStore } from "../agents/store";
import { useRouteDeckSessionVersion } from "../../routedeck/RouteDeckSessionVersionContext";
import { DeployedRuntimeEvidence } from "./DeployedRuntimeEvidence";


export function OperationsSurface({ dispatchAffordance, props, runtimeClient, agentStore }: RouteDeckSurfaceComponentProps & { runtimeClient: AgentRuntimeClient; agentStore: AgentStore }) {
  const sessionVersion = useRouteDeckSessionVersion();
  const agents = useSyncExternalStore(agentStore.subscribe, agentStore.snapshot);
  const selectedAgentRef = typeof props.selected_agent_ref === "string" ? props.selected_agent_ref : null;
  const selectedAgentId = agents.selectedId;
  const [interactions, setInteractions] = useState<readonly OperationsInteractionView[]>([]);
  const [builds, setBuilds] = useState<readonly AgentBuildView[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [setName, setSetName] = useState("Operations regressions");
  const [category, setCategory] = useState("deployed-interaction");
  const [difficulty, setDifficulty] = useState("medium");

  async function refresh() {
    if (selectedAgentId === null) {
      setInteractions([]);
      setBuilds([]);
      return;
    }
    const [operationInventory, buildInventory] = await Promise.all([
      runtimeClient.operations(selectedAgentId),
      runtimeClient.builds(selectedAgentId),
    ]);
    setInteractions(operationInventory.interactions);
    setBuilds(buildInventory.builds);
  }
  useEffect(() => { void agentStore.refresh(); }, [agentStore]);
  useEffect(() => {
    agentStore.syncSelectionFromHandle(selectedAgentRef);
  }, [agentStore, agents.agents, selectedAgentRef]);
  useEffect(() => { void refresh().catch((caught) => setError(message(caught))); }, [runtimeClient, selectedAgentId, sessionVersion]);

  async function promote(interaction: OperationsInteractionView) {
    setBusy(interaction.interaction_id); setError(null);
    try {
      const result = await dispatchAffordance("promote", {
        interaction_id: interaction.interaction_id, set_name: setName,
        title: interaction.input_summary.slice(0, 160) || "Deployed interaction",
        category, difficulty, mandatory: true,
      });
      const failure = completedOutcome(result, "promoted");
      if (failure !== null) setError(failure);
    } catch (caught) { setError(message(caught)); } finally { setBusy(null); }
  }

  async function returnToAgent() {
    if (selectedAgentRef === null) return;
    setBusy("return"); setError(null);
    try {
      const failure = completedOutcome(await dispatchAffordance("return_to_agent", { agent_ref: selectedAgentRef }), "opened");
      if (failure !== null) setError(failure);
    } catch (caught) { setError(message(caught)); } finally { setBusy(null); }
  }

  return <section className="operations-home" aria-labelledby="operations-title">
    <header><p>Owner activity</p><h1 id="operations-title">Operations</h1><span>Deployed Agent interactions and redacted execution evidence</span><Button type="button" variant="outline" disabled={busy !== null || selectedAgentRef === null} onClick={() => void returnToAgent()}>Back to Agent</Button></header>
    {error === null ? null : <p role="alert">{error}</p>}
    <div className="operations-promotion-controls">
      <Field><FieldLabel htmlFor="operations-set">Evaluation set</FieldLabel><Input id="operations-set" value={setName} onChange={(event) => setSetName(event.target.value)} /></Field>
      <Field><FieldLabel htmlFor="operations-category">Category</FieldLabel><Input id="operations-category" value={category} onChange={(event) => setCategory(event.target.value)} /></Field>
      <Field><FieldLabel htmlFor="operations-difficulty">Difficulty</FieldLabel><select id="operations-difficulty" value={difficulty} onChange={(event) => setDifficulty(event.target.value)}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></Field>
    </div>
    {selectedAgentId === null ? <p>Select an Agent to inspect Operations.</p> : interactions.length === 0 ? <p>No deployed Agent interactions yet.</p> : <ol>{interactions.map((interaction) => <li key={interaction.interaction_id}>
      <strong>{interaction.status}</strong><span>Build {interaction.build_id}</span><span>Deployment {interaction.deployment_id}</span>
      <p>{interaction.input_summary}</p><p>{interaction.output_summary}</p>
      <DeployedRuntimeEvidence interaction={interaction} build={builds.find((item) => item.id === interaction.build_id) ?? null} />
      <details><summary>Complete redacted execution trace</summary><ol>{interaction.events.map((event) => <li key={`${event.sequence}-${event.kind}`}><strong>{event.kind}</strong><code>{JSON.stringify(event.safe_data)}</code></li>)}</ol></details>
      <Button type="button" disabled={busy !== null || !setName.trim() || !category.trim()} onClick={() => void promote(interaction)}>Create evaluation case</Button>
    </li>)}</ol>}
  </section>;
}

function message(value: unknown) { return value instanceof Error ? value.message : "Agent Operations are unavailable."; }
