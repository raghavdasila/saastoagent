import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { Button } from "@/components/ui/button";
import { Field, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import type { AgentStore } from "../agents/store";
import { completedOutcome } from "../agents/operationResult";
import type { AgentRuntimeClient } from "../builder/client";
import type { AgentBuildView, EvaluationSetView, SandboxRunView } from "../builder/models";
import { BuildNavGraph } from "../builder/BuildNavGraph";
import { useRouteDeckSessionVersion } from "../../routedeck/RouteDeckSessionVersionContext";


export function EvaluationSurface({ dispatchAffordance, props, agentStore, runtimeClient }: RouteDeckSurfaceComponentProps & { agentStore: AgentStore; runtimeClient: AgentRuntimeClient }) {
  const sessionVersion = useRouteDeckSessionVersion();
  const agents = useSyncExternalStore(agentStore.subscribe, agentStore.snapshot);
  const selectedRef = typeof props.selected_agent_ref === "string" ? props.selected_agent_ref : null;
  const selected = useMemo(() => agents.agents.find((item) => item.id === agents.selectedId) ?? null, [agents.agents, agents.selectedId]);
  const [builds, setBuilds] = useState<readonly AgentBuildView[]>([]);
  const [runs, setRuns] = useState<readonly SandboxRunView[]>([]);
  const [sets, setSets] = useState<readonly EvaluationSetView[]>([]);
  const [buildId, setBuildId] = useState("");
  const [runId, setRunId] = useState("");
  const [setName, setSetName] = useState("Baseline");
  const [title, setTitle] = useState("Successful Sandbox interaction");
  const [category, setCategory] = useState("routing");
  const [difficulty, setDifficulty] = useState("easy");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh(agentId: string) {
    const [inventory, sandbox, evaluations] = await Promise.all([
      runtimeClient.builds(agentId), runtimeClient.sandbox(agentId), runtimeClient.evaluations(agentId),
    ]);
    const ready = inventory.builds.filter((item) => item.status === "ready");
    setBuilds(ready); setRuns(sandbox.runs.filter((item) => item.status === "succeeded")); setSets(evaluations.evaluation_sets);
    setBuildId((current) => ready.some((item) => item.id === current) ? current : ready[0]?.id ?? "");
  }

  useEffect(() => { void agentStore.refresh(); }, [agentStore]);
  useEffect(() => { agentStore.syncSelectionFromHandle(selectedRef); }, [agentStore, agents.agents, selectedRef]);
  useEffect(() => {
    if (selected === null) return;
    let active = true;
    void refresh(selected.id).catch((caught) => active && setError(message(caught)));
    return () => { active = false; };
  }, [runtimeClient, selected?.id, sessionVersion]);
  useEffect(() => {
    const availableRuns = runs.filter((item) => item.build_id === buildId);
    setRunId((current) => availableRuns.some((item) => item.id === current) ? current : availableRuns[0]?.id ?? "");
  }, [buildId, builds, runs]);

  async function createCase() {
    if (selectedRef === null || selected === null || !buildId || !runId) return;
    setBusy(true); setError(null);
    try {
      const result = await dispatchAffordance("create_case", {
        agent_ref: selectedRef, build_id: buildId, sandbox_run_id: runId,
        set_name: setName, title, category, difficulty,
        mandatory: true,
      });
      const failure = completedOutcome(result, "created");
      if (failure !== null) setError(failure); else await refresh(selected.id);
    } catch (caught) { setError(message(caught)); } finally { setBusy(false); }
  }

  async function runCase(caseId: string) {
    if (selectedRef === null || selected === null) return;
    setBusy(true); setError(null);
    try {
      const result = await dispatchAffordance("run_case", { agent_ref: selectedRef, case_id: caseId });
      const failure = completedOutcome(result, "evaluated");
      if (failure !== null) setError(failure); else await refresh(selected.id);
    } catch (caught) { setError(message(caught)); } finally { setBusy(false); }
  }

  async function returnToAgent() {
    if (selectedRef === null) return;
    setBusy(true); setError(null);
    try {
      const failure = completedOutcome(await dispatchAffordance("return_to_agent", { agent_ref: selectedRef }), "opened");
      if (failure !== null) setError(failure);
    } catch (caught) { setError(message(caught)); } finally { setBusy(false); }
  }

  const selectedBuild = builds.find((item) => item.id === buildId);
  return <section className="evaluation-home" aria-labelledby="evaluation-title">
    <header><p>Selected Agent</p><h1 id="evaluation-title">Evaluation</h1><span>{selected?.name ?? "Loading exact Agent…"}</span><Button type="button" variant="outline" disabled={busy || selectedRef === null} onClick={() => void returnToAgent()}>Back to Agent</Button></header>
    {error === null ? null : <p role="alert">{error}</p>}
    {builds.length === 0 ? <p>A ready immutable build and successful Sandbox interaction are required.</p> : <div className="evaluation-create">
      <Field><FieldLabel htmlFor="evaluation-build">Exact build</FieldLabel><select id="evaluation-build" value={buildId} onChange={(event) => setBuildId(event.target.value)}>{builds.map((item) => <option key={item.id} value={item.id}>{item.id}</option>)}</select></Field>
      <Field><FieldLabel htmlFor="evaluation-run">Sandbox interaction</FieldLabel><select id="evaluation-run" value={runId} onChange={(event) => setRunId(event.target.value)}>{runs.filter((item) => item.build_id === buildId).map((item) => <option key={item.id} value={item.id}>{item.final_response ?? item.id}</option>)}</select></Field>
      <Field><FieldLabel htmlFor="evaluation-set">Evaluation set</FieldLabel><Input id="evaluation-set" value={setName} onChange={(event) => setSetName(event.target.value)} /></Field>
      <Field><FieldLabel htmlFor="evaluation-title-input">Case title</FieldLabel><Input id="evaluation-title-input" value={title} onChange={(event) => setTitle(event.target.value)} /></Field>
      <Field><FieldLabel htmlFor="evaluation-category">Category</FieldLabel><Input id="evaluation-category" value={category} onChange={(event) => setCategory(event.target.value)} /></Field>
      <Field><FieldLabel htmlFor="evaluation-difficulty">Difficulty</FieldLabel><select id="evaluation-difficulty" value={difficulty} onChange={(event) => setDifficulty(event.target.value)}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></Field>
      <Button type="button" disabled={busy || !runId || !setName.trim() || !title.trim() || !category.trim()} onClick={() => void createCase()}>Create evaluation case</Button>
    </div>}
    {selectedBuild?.status === "ready" ? <BuildNavGraph build={selectedBuild} /> : null}
    <ul>{sets.map((set) => <li key={set.id}><h2>{set.name}</h2><p>{set.eligible === null ? "Not evaluated" : set.eligible ? "Eligible for deployment" : "Not eligible for deployment"}</p><ul>{set.cases.map((item) => <li key={item.id}><strong>{item.title}</strong><span>{item.category} · {item.difficulty}</span><span>{item.latest_status ?? "Not run"}</span><Button type="button" disabled={busy} onClick={() => void runCase(item.id)}>Run exact case</Button></li>)}</ul></li>)}</ul>
  </section>;
}

function message(value: unknown) { return value instanceof Error ? value.message : "Agent Evaluation is unavailable."; }
