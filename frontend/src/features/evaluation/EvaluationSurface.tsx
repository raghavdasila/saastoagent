import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { Button } from "@/components/ui/button";
import { Field, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import type { AgentStore } from "../agents/store";
import { completedOutcome } from "../agents/operationResult";
import type { AgentRuntimeClient } from "../builder/client";
import type { AgentBuildView, EvaluationCaseView, EvaluationSetView, SandboxRunView } from "../builder/models";
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
  const [generatedSetName, setGeneratedSetName] = useState("Generated coverage");
  const [title, setTitle] = useState("Successful Sandbox interaction");
  const [category, setCategory] = useState("routing");
  const [difficulty, setDifficulty] = useState("easy");
  const [editing, setEditing] = useState<EvaluationCaseView | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh(agentId: string) {
    const [inventory, sandbox, evaluations] = await Promise.all([
      runtimeClient.builds(agentId), runtimeClient.sandbox(agentId), runtimeClient.evaluations(agentId),
    ]);
    const ready = inventory.builds.filter((item) => item.status === "ready" && item.runtime_lifecycle !== "removed");
    setBuilds(ready);
    setRuns(sandbox.runs.filter((item) => item.status === "succeeded"));
    setSets(evaluations.evaluation_sets);
    setBuildId((current) => ready.some((item) => item.id === current) ? current : ready[0]?.id ?? "");
  }

  useEffect(() => { void agentStore.refresh(); }, [agentStore]);
  useEffect(() => { agentStore.syncSelectionFromHandle(selectedRef); }, [agentStore, agents.agents, selectedRef]);
  useEffect(() => {
    if (selected === null) { setLoading(true); return; }
    let active = true;
    setLoading(true);
    void refresh(selected.id)
      .catch((caught) => active && setError(message(caught)))
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [runtimeClient, selected?.id, sessionVersion]);
  useEffect(() => {
    if (selected === null || !sets.some((set) => set.generation_status === "queued" || set.generation_status === "running")) return;
    const interval = window.setInterval(() => void refresh(selected.id).catch((caught) => setError(message(caught))), 2000);
    return () => window.clearInterval(interval);
  }, [selected?.id, sets]);
  useEffect(() => {
    const availableRuns = runs.filter((item) => item.build_id === buildId);
    setRunId((current) => availableRuns.some((item) => item.id === current) ? current : availableRuns[0]?.id ?? "");
  }, [buildId, builds, runs]);

  async function dispatch(
    action: string,
    arguments_: { [key: string]: string | number | boolean | null | string[] },
    outcome: string,
  ) {
    if (selected === null) return false;
    setBusy(true); setError(null);
    try {
      const result = await dispatchAffordance(action, arguments_);
      const failure = completedOutcome(result, outcome);
      if (failure !== null) { setError(failure); return false; }
      await refresh(selected.id);
      return true;
    } catch (caught) { setError(message(caught)); return false; } finally { setBusy(false); }
  }

  async function createCase() {
    if (selectedRef === null || !buildId || !runId) return;
    await dispatch("create_case", {
      agent_ref: selectedRef, build_id: buildId, sandbox_run_id: runId,
      set_name: setName, title, category, difficulty, mandatory: true,
    }, "created");
  }

  async function generateSet() {
    if (selectedRef === null || !buildId) return;
    await dispatch("generate_set", {
      agent_ref: selectedRef, build_id: buildId,
      set_name: generatedSetName, categories: ["paraphrase"],
    }, "queued");
  }

  async function retryGeneration(evaluationSetId: string) {
    if (selectedRef === null) return;
    await dispatch("retry_generation", { agent_ref: selectedRef, evaluation_set_id: evaluationSetId }, "queued");
  }

  async function runCase(caseId: string) {
    if (selectedRef === null) return;
    await dispatch("run_case", { agent_ref: selectedRef, case_id: caseId }, "evaluated");
  }

  async function saveEdit() {
    if (selectedRef === null || editing === null) return;
    const saved = await dispatch("edit_case", {
      agent_ref: selectedRef, case_id: editing.id,
      expected_revision: editing.current_revision, title: editing.title,
      category: editing.category, difficulty: editing.difficulty,
      mandatory: editing.mandatory,
    }, "edited");
    if (saved) setEditing(null);
  }

  async function deleteCase(item: EvaluationCaseView) {
    if (selectedRef === null) return;
    setBusy(true); setError(null);
    try {
      const result = await dispatchAffordance("delete_case", {
        agent_ref: selectedRef, case_id: item.id,
        expected_revision: item.current_revision,
      });
      if (result.disposition !== "requires_review") {
        setError(result.failure?.public_message ?? "Corpus could not prepare the evaluation-case review.");
      }
    } catch (caught) { setError(message(caught)); } finally { setBusy(false); }
  }

  async function navigate(action: "return_to_agent" | "continue_to_builds" | "continue_to_channels") {
    if (selectedRef === null) return;
    await dispatch(action, { agent_ref: selectedRef }, "opened");
  }

  const selectedBuild = builds.find((item) => item.id === buildId);
  const selectedBuildRunning = selectedBuild?.runtime_lifecycle === "running";
  return <section className="evaluation-home" aria-labelledby="evaluation-title">
    <header><p>Selected Agent</p><h1 id="evaluation-title">Evaluation</h1><span>{selected?.name ?? "Loading exact Agent..."}</span><Button type="button" variant="outline" disabled={busy || selectedRef === null} onClick={() => void navigate("return_to_agent")}>Back to Agent</Button></header>
    <p>Generate, refine, and run evaluation coverage against one exact immutable build. Prior results remain attributable when a case changes.</p>
    {error === null ? null : <p role="alert">{error}</p>}
    {loading ? <section className="evaluation-loading" role="status" aria-live="polite">
      <strong>Loading exact Evaluation…</strong>
      <span>Resolving the selected Agent, immutable builds, Sandbox interactions, and evaluation history.</span>
    </section> : builds.length === 0 ? <section className="evaluation-prerequisite" aria-labelledby="evaluation-prerequisite-title">
      <div><p>Build prerequisite</p><h2 id="evaluation-prerequisite-title">A ready immutable build is required.</h2><span>Continue with this exact Agent in Builds. Corpus will not start or substitute a build.</span></div>
      <Button type="button" variant="outline" disabled={busy || selectedRef === null} onClick={() => void navigate("continue_to_builds")}>Continue to Builds</Button>
    </section> : <>
      <div className="evaluation-build-context">
        <Field><FieldLabel htmlFor="evaluation-build">Exact build</FieldLabel><select id="evaluation-build" value={buildId} onChange={(event) => setBuildId(event.target.value)}>{builds.map((item) => <option key={item.id} value={item.id}>{item.id} · {item.runtime_lifecycle}</option>)}</select></Field>
        <Field><FieldLabel htmlFor="evaluation-generated-set">Generated set name</FieldLabel><Input id="evaluation-generated-set" value={generatedSetName} onChange={(event) => setGeneratedSetName(event.target.value)} /></Field>
        <Button type="button" disabled={busy || !buildId || !generatedSetName.trim()} onClick={() => void generateSet()}>Generate with ToolRouter</Button>
        {!selectedBuildRunning ? <p>Generation is available from the immutable build. Run the draft runtime before executing cases.</p> : null}
      </div>
      <details className="evaluation-create">
        <summary>Add a case from a successful Sandbox interaction</summary>
        <Field><FieldLabel htmlFor="evaluation-run">Sandbox interaction</FieldLabel><select id="evaluation-run" value={runId} onChange={(event) => setRunId(event.target.value)}><option value="">Choose a successful interaction</option>{runs.filter((item) => item.build_id === buildId).map((item) => <option key={item.id} value={item.id}>{item.final_response ?? item.id}</option>)}</select></Field>
        <Field><FieldLabel htmlFor="evaluation-set">Evaluation set</FieldLabel><Input id="evaluation-set" value={setName} onChange={(event) => setSetName(event.target.value)} /></Field>
        <Field><FieldLabel htmlFor="evaluation-title-input">Case title</FieldLabel><Input id="evaluation-title-input" value={title} onChange={(event) => setTitle(event.target.value)} /></Field>
        <Field><FieldLabel htmlFor="evaluation-category">Category</FieldLabel><Input id="evaluation-category" value={category} onChange={(event) => setCategory(event.target.value)} /></Field>
        <Field><FieldLabel htmlFor="evaluation-difficulty">Difficulty</FieldLabel><select id="evaluation-difficulty" value={difficulty} onChange={(event) => setDifficulty(event.target.value)}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select></Field>
        <Button type="button" disabled={busy || !runId || !setName.trim() || !title.trim() || !category.trim()} onClick={() => void createCase()}>Add evaluation case</Button>
      </details>
    </>}
    {!loading && selectedBuild?.status === "ready" ? <BuildNavGraph build={selectedBuild} /> : null}
    {!loading && sets.some((set) => set.build_id === buildId && set.eligible === true) ? <Button type="button" disabled={busy} onClick={() => void navigate("continue_to_channels")}>Continue to Channels</Button> : null}
    <div className="evaluation-sets">{loading ? null : sets.filter((set) => set.build_id === buildId).map((set) => <article key={set.id} className="evaluation-set-card">
      <header><div><h2>{set.name}</h2><p>Generation: <strong>{generationLabel(set.generation_status)}</strong></p></div><p>{set.eligible === null ? "Not evaluated" : set.eligible ? "Eligible for deployment" : "Not eligible for deployment"}</p></header>
      {set.generation_failure_message ? <p role="alert">{set.generation_failure_message}</p> : null}
      {set.generation_status === "failed" ? <Button type="button" variant="outline" disabled={busy} onClick={() => void retryGeneration(set.id)}>Retry generation</Button> : null}
      <div className="evaluation-case-table" role="table" aria-label={`${set.name} evaluation cases`}>
        {set.cases.map((item) => <div key={item.id} role="row" data-removed={item.removed || undefined}>
          {editing?.id === item.id ? <>
            <Input aria-label="Edit case title" value={editing.title} onChange={(event) => setEditing({ ...editing, title: event.target.value })} />
            <Input aria-label="Edit case category" value={editing.category} onChange={(event) => setEditing({ ...editing, category: event.target.value })} />
            <select aria-label="Edit case difficulty" value={editing.difficulty} onChange={(event) => setEditing({ ...editing, difficulty: event.target.value })}><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select>
            <label><input type="checkbox" checked={editing.mandatory} onChange={(event) => setEditing({ ...editing, mandatory: event.target.checked })} /> Required</label>
            <Button type="button" disabled={busy} onClick={() => void saveEdit()}>Save revision</Button><Button type="button" variant="outline" onClick={() => setEditing(null)}>Cancel</Button>
          </> : <>
            <div role="cell"><strong>{item.title}</strong><span>{item.category} · {item.difficulty} · revision {item.current_revision}</span><span>{item.source_kind === "toolrouter" ? "ToolRouter generated" : "Recorded interaction"}</span></div>
            <div role="cell"><span>{item.latest_status ?? "Not run"}</span>{item.removed ? <span>Removed from future evaluation</span> : null}</div>
            {!item.removed ? <div role="cell" className="evaluation-case-actions"><Button type="button" disabled={busy || !selectedBuildRunning} onClick={() => void runCase(item.id)}>{item.source_kind === "toolrouter" && !item.runnable ? "Run generated case" : "Run exact case"}</Button><Button type="button" variant="outline" disabled={busy} onClick={() => setEditing(item)}>Edit</Button><Button type="button" variant="destructive" disabled={busy} onClick={() => void deleteCase(item)}>Remove</Button></div> : null}
          </>}
        </div>)}
      </div>
    </article>)}</div>
  </section>;
}

function generationLabel(value: EvaluationSetView["generation_status"]): string {
  if (value === "manual") return "Manually authored";
  if (value === "queued") return "Queued";
  if (value === "running") return "Generating";
  if (value === "ready") return "Generated";
  return "Failed";
}

function message(value: unknown) { return value instanceof Error ? value.message : "Agent Evaluation is unavailable."; }
