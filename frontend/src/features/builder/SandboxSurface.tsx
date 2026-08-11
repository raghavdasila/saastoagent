import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { Button } from "@/components/ui/button";
import { Field, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { AgentStore } from "../agents/store";
import { completedOutcome } from "../agents/operationResult";
import type { AgentRuntimeClient } from "./client";
import type { AgentBuildView, SandboxRunView } from "./models";
import { BuildNavGraph } from "./BuildNavGraph";
import { SandboxRuntimeEvidence } from "./SandboxRuntimeEvidence";
import { useRouteDeckSessionVersion } from "../../routedeck/RouteDeckSessionVersionContext";


export function SandboxSurface({ dispatchAffordance, props, agentStore, runtimeClient }: RouteDeckSurfaceComponentProps & { agentStore: AgentStore; runtimeClient: AgentRuntimeClient }) {
  const sessionVersion = useRouteDeckSessionVersion();
  const agents = useSyncExternalStore(agentStore.subscribe, agentStore.snapshot);
  const selectedRef = typeof props.selected_agent_ref === "string" ? props.selected_agent_ref : null;
  const selected = useMemo(() => agents.agents.find((item) => item.id === agents.selectedId) ?? null, [agents.agents, agents.selectedId]);
  const [builds, setBuilds] = useState<readonly AgentBuildView[]>([]);
  const [runs, setRuns] = useState<readonly SandboxRunView[]>([]);
  const [buildId, setBuildId] = useState("");
  const [request, setRequest] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const selectedBuild = useMemo(() => builds.find((item) => item.id === buildId) ?? null, [buildId, builds]);

  useEffect(() => { void agentStore.refresh(); }, [agentStore]);
  useEffect(() => { agentStore.syncSelectionFromHandle(selectedRef); }, [agentStore, agents.agents, selectedRef]);
  useEffect(() => {
    if (selected === null) return;
    let active = true;
    void Promise.all([runtimeClient.builds(selected.id), runtimeClient.sandbox(selected.id)]).then(([inventory, history]) => {
      if (!active) return;
      const ready = inventory.builds.filter((item) => item.status === "ready");
      setBuilds(ready); setBuildId((current) => ready.some((item) => item.id === current) ? current : ready[0]?.id ?? ""); setRuns(history.runs);
    }).catch((caught) => active && setError(message(caught)));
    return () => { active = false; };
  }, [runtimeClient, selected?.id, sessionVersion]);

  async function start() {
    if (selectedRef === null || selected === null || buildId === "" || request.trim() === "") return;
    setBusy(true); setError(null);
    try {
      const result = await dispatchAffordance("start", { agent_ref: selectedRef, build_id: buildId, message: request.trim() });
      const failure = completedOutcome(result, "started");
      if (failure !== null) setError(failure);
      else { setRuns((await runtimeClient.sandbox(selected.id)).runs); setRequest(""); }
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

  async function continueToEvaluation() {
    if (selectedRef === null) return;
    setBusy(true); setError(null);
    try {
      const failure = completedOutcome(
        await dispatchAffordance("continue_to_evaluation", { agent_ref: selectedRef }),
        "opened",
      );
      if (failure !== null) setError(failure);
    } catch (caught) { setError(message(caught)); } finally { setBusy(false); }
  }

  return <section className="sandbox-home" aria-labelledby="sandbox-title">
    <header><p>Selected Agent</p><h1 id="sandbox-title">Agent Sandbox</h1><span>{selected?.name ?? "Loading exact Agent…"}</span><Button type="button" variant="outline" disabled={busy || selectedRef === null} onClick={() => void returnToAgent()}>Back to Agent</Button></header>
    {error === null ? null : <p role="alert">{error}</p>}
    {builds.length === 0 ? <p>A ready immutable build is required before a Sandbox run can start.</p> : <>
      <Field><FieldLabel htmlFor="sandbox-build">Exact build</FieldLabel><select id="sandbox-build" value={buildId} onChange={(event) => setBuildId(event.target.value)}>{builds.map((item) => <option key={item.id} value={item.id}>{item.id}</option>)}</select></Field>
      {selectedBuild === null ? null : <BuildNavGraph build={selectedBuild} />}
      <Field><FieldLabel htmlFor="sandbox-request">Message</FieldLabel><Textarea id="sandbox-request" value={request} onChange={(event) => setRequest(event.target.value)} /></Field>
      <Button type="button" disabled={busy || request.trim() === ""} onClick={() => void start()}>Start isolated run</Button>
    </>}
    {runs.some((run) => run.status === "succeeded") ? <Button type="button" disabled={busy} onClick={() => void continueToEvaluation()}>Continue to Evaluation</Button> : null}
    <ol>{runs.map((run) => <li key={run.id} data-status={run.status}><strong>{run.status}</strong><span>Build {run.build_id}</span><span>{run.api_call_count} API calls</span>{run.final_response ? <p>{run.final_response}</p> : null}<SandboxRuntimeEvidence run={run} />{run.clarification === null ? null : <SandboxClarificationForm run={run} selectedAgentRef={selectedRef} busy={busy} dispatchAffordance={dispatchAffordance} onCompleted={async () => { if (selected !== null) setRuns((await runtimeClient.sandbox(selected.id)).runs); }} setBusy={setBusy} setError={setError} />}</li>)}</ol>
  </section>;
}

function SandboxClarificationForm({ run, selectedAgentRef, busy, dispatchAffordance, onCompleted, setBusy, setError }: {
  run: SandboxRunView;
  selectedAgentRef: string | null;
  busy: boolean;
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"];
  onCompleted(): Promise<void>;
  setBusy(value: boolean): void;
  setError(value: string | null): void;
}) {
  const clarification = run.clarification!;
  const [operationId, setOperationId] = useState(
    clarification.candidate_operation_ids.length === 1 ? clarification.candidate_operation_ids[0] : "",
  );
  const [answers, setAnswers] = useState<Record<string, string>>(() => Object.fromEntries(
    clarification.missing_input_names.map((name) => [name, ""]),
  ));
  const complete = operationId !== "" && clarification.missing_input_names.every((name) => (answers[name] ?? "").trim() !== "");

  async function resume() {
    if (!complete || selectedAgentRef === null) return;
    setBusy(true); setError(null);
    const message = clarification.missing_input_names.length === 1
      ? answers[clarification.missing_input_names[0]].trim()
      : operationId;
    try {
      const result = await dispatchAffordance("resume", {
        agent_ref: selectedAgentRef,
        run_id: run.id,
        message,
        selected_operation_id: operationId,
        answers: Object.fromEntries(Object.entries(answers).map(([name, value]) => [name, value.trim()])),
      });
      const failure = completedOutcome(result, "resumed");
      if (failure !== null) setError(failure); else await onCompleted();
    } catch (caught) { setError(messageOf(caught)); } finally { setBusy(false); }
  }

  return <section className="sandbox-clarification" aria-label={`Clarification for run ${run.id}`}>
    <h2>One detail is needed</h2><p>{clarification.question}</p>
    {clarification.candidate_operation_ids.length <= 1 ? null : <Field><FieldLabel htmlFor={`sandbox-operation-${run.id}`}>Operation</FieldLabel><select id={`sandbox-operation-${run.id}`} value={operationId} disabled={busy} onChange={(event) => setOperationId(event.target.value)}><option value="">Choose an operation</option>{clarification.candidate_choices.map((item) => <option key={item.operation_id} value={item.operation_id}>{item.label ?? item.operation_id}</option>)}</select></Field>}
    {clarification.missing_input_names.map((name) => <Field key={name}><FieldLabel htmlFor={`sandbox-answer-${run.id}-${name}`}>Value for {name}</FieldLabel><Input id={`sandbox-answer-${run.id}-${name}`} value={answers[name] ?? ""} disabled={busy} onChange={(event) => setAnswers((current) => ({ ...current, [name]: event.target.value }))} /></Field>)}
    <Button type="button" disabled={busy || !complete} onClick={() => void resume()}>Continue same run</Button>
  </section>;
}

function message(value: unknown) { return messageOf(value); }
function messageOf(value: unknown) { return value instanceof Error ? value.message : "Agent Sandbox is unavailable."; }
