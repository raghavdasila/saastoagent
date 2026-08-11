import { useEffect, useRef, useState, useSyncExternalStore } from "react";
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [setName, setSetName] = useState("Operations regressions");
  const [category, setCategory] = useState("deployed-interaction");
  const [difficulty, setDifficulty] = useState("medium");
  const refreshGeneration = useRef(0);

  async function refresh() {
    const generation = ++refreshGeneration.current;
    if (selectedAgentId === null) {
      setInteractions([]);
      setBuilds([]);
      setLoading(true);
      return;
    }
    setLoading(true);
    try {
      const [operationInventory, buildInventory] = await Promise.all([
        runtimeClient.operations(selectedAgentId),
        runtimeClient.builds(selectedAgentId),
      ]);
      if (generation !== refreshGeneration.current) return;
      setInteractions(operationInventory.interactions);
      setBuilds(buildInventory.builds);
    } finally {
      if (generation === refreshGeneration.current) setLoading(false);
    }
  }
  useEffect(() => { void agentStore.refresh(); }, [agentStore]);
  useEffect(() => {
    agentStore.syncSelectionFromHandle(selectedAgentRef);
  }, [agentStore, agents.agents, selectedAgentRef]);
  useEffect(() => {
    void refresh().catch((caught) => setError(message(caught)));
    return () => { refreshGeneration.current += 1; };
  }, [runtimeClient, selectedAgentId, sessionVersion]);

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
    {loading ? <p className="operations-home__loading" role="status">Loading exact deployed interactions and immutable build lineageâ€¦</p> : null}
    {!loading ? <section className="operations-home__summary" aria-label="Operations summary"><div><span>Interactions</span><strong>{interactions.length}</strong></div><div><span>Successful</span><strong>{interactions.filter((item) => item.status === "succeeded").length}</strong></div><div><span>Evaluation candidates</span><strong>{interactions.filter(isEvaluationCandidate).length}</strong></div></section> : null}
    {selectedAgentId === null ? !loading ? <p>Select an Agent to inspect Operations.</p> : null : !loading && interactions.length === 0 ? <p>No deployed Agent interactions yet.</p> : <ol className="operations-home__interactions">{interactions.map((interaction) => <li key={interaction.interaction_id}>
      <header><div><span className="operations-home__status" data-status={interaction.status}>{interaction.status}</span><h2>{interaction.input_summary}</h2></div><span>Deployed interaction</span></header>
      <section className="operations-home__outcome" aria-label="Agent response"><p>Agent response</p><strong>{interaction.output_summary}</strong></section>
      <DeployedRuntimeEvidence interaction={interaction} build={builds.find((item) => item.id === interaction.build_id) ?? null} />
      <details className="operations-home__lineage"><summary>Exact immutable lineage</summary><dl><div><dt>Build</dt><dd>{interaction.build_id}</dd></div><div><dt>Deployment</dt><dd>{interaction.deployment_id}</dd></div><div><dt>Public session</dt><dd>{interaction.session_id}</dd></div></dl></details>
      <details><summary>Complete redacted execution trace</summary><ol>{interaction.events.map((event) => <li key={`${event.sequence}-${event.kind}`}><strong>{event.kind}</strong><code>{JSON.stringify(event.safe_data)}</code></li>)}</ol></details>
      {isEvaluationCandidate(interaction) ? <details className="operations-home__promotion"><summary>Create an Evaluation case from this interaction</summary><p>Reuse this successful real interaction as a versioned regression case for a future Agent build.</p><div className="operations-promotion-controls">
        <Field><FieldLabel htmlFor={`operations-set-${interaction.interaction_id}`}>Evaluation set</FieldLabel><Input id={`operations-set-${interaction.interaction_id}`} value={setName} onChange={(event) => setSetName(event.target.value)} /></Field>
        <Field><FieldLabel htmlFor={`operations-category-${interaction.interaction_id}`}>Category</FieldLabel><Input id={`operations-category-${interaction.interaction_id}`} value={category} onChange={(event) => setCategory(event.target.value)} /></Field>
        <Field><FieldLabel htmlFor={`operations-difficulty-${interaction.interaction_id}`}>Difficulty</FieldLabel><select id={`operations-difficulty-${interaction.interaction_id}`} value={difficulty} onChange={(event) => setDifficulty(event.target.value)}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></Field>
      </div><Button type="button" disabled={busy !== null || !setName.trim() || !category.trim()} onClick={() => void promote(interaction)}>Create Evaluation case</Button></details> : <p className="operations-home__not-promotable">This interaction has no completed API operation to promote.</p>}
    </li>)}</ol>}
  </section>;
}

function message(value: unknown) { return value instanceof Error ? value.message : "Agent Operations are unavailable."; }

function isEvaluationCandidate(interaction: OperationsInteractionView): boolean {
  return interaction.status === "succeeded" && interaction.events.some((event) => event.kind === "api.result");
}
