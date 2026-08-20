import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { Button } from "@/components/ui/button";
import { Field, FieldLabel } from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";
import type { AgentSelectionStore } from "../agents/contracts";
import { completedOutcome } from "@/shared/routedeck/operationResult";
import type { AgentRuntimeClient } from "./client";
import type {
  AgentBuildView,
  EvaluationSetView,
  PlaygroundInteractionView,
  SandboxDeploymentCollectionView,
  SandboxDiagnosticsView,
} from "./models";
import { BuildNavGraph } from "@/shared/agent/BuildNavGraph";
import { useRouteDeckSessionVersion } from "../../routedeck/RouteDeckSessionVersionContext";

type Tab = "deployment" | "playground" | "evaluations" | "diagnostics";

export function SandboxSurface({ dispatchAffordance, props, agentStore, runtimeClient }: RouteDeckSurfaceComponentProps & { agentStore: AgentSelectionStore; runtimeClient: AgentRuntimeClient }) {
  const sessionVersion = useRouteDeckSessionVersion();
  const agents = useSyncExternalStore(agentStore.subscribe, agentStore.snapshot);
  const selectedRef = typeof props.selected_agent_ref === "string" ? props.selected_agent_ref : null;
  const selected = useMemo(() => agents.agents.find((item) => item.id === agents.selectedId) ?? null, [agents.agents, agents.selectedId]);
  const [tab, setTab] = useState<Tab>("deployment");
  const [builds, setBuilds] = useState<readonly AgentBuildView[]>([]);
  const [buildId, setBuildId] = useState("");
  const [sandbox, setSandbox] = useState<SandboxDeploymentCollectionView | null>(null);
  const [evaluationSets, setEvaluationSets] = useState<readonly EvaluationSetView[]>([]);
  const [conversation, setConversation] = useState<PlaygroundInteractionView | null>(null);
  const [sessionId, setSessionId] = useState("");
  const [messageText, setMessageText] = useState("");
  const [diagnostics, setDiagnostics] = useState<SandboxDiagnosticsView | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const activeDeployment = sandbox?.deployments.find((item) => item.id === sandbox.active_deployment_id) ?? null;
  const selectedBuild = builds.find((item) => item.id === buildId) ?? null;
  const compatibleSets = evaluationSets.filter((item) => item.build_id === activeDeployment?.build_id);

  async function refresh(agentId: string) {
    const [inventory, sandboxState, evaluations] = await Promise.all([
      runtimeClient.builds(agentId),
      runtimeClient.sandboxDeployment(agentId),
      runtimeClient.evaluations(agentId),
    ]);
    const ready = inventory.builds.filter((item) => item.status === "ready" && item.runtime_lifecycle !== "removed");
    setBuilds(ready);
    setBuildId((current) => ready.some((item) => item.id === current) ? current : ready[0]?.id ?? "");
    setSandbox(sandboxState);
    setEvaluationSets(evaluations.evaluation_sets);
    setSessionId((current) => sandboxState.playground_sessions.some((item) => item.session_id === current) ? current : sandboxState.playground_sessions[0]?.session_id ?? "");
  }

  useEffect(() => { void agentStore.refresh(); }, [agentStore]);
  useEffect(() => { agentStore.syncSelectionFromHandle(selectedRef); }, [agentStore, agents.agents, selectedRef]);
  useEffect(() => {
    if (selected === null) return;
    let active = true;
    setLoading(true);
    void refresh(selected.id)
      .catch((caught) => active && setError(message(caught)))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [runtimeClient, selected?.id, sessionVersion]);
  useEffect(() => {
    if (selected === null || sessionId === "") { setConversation(null); return; }
    let active = true;
    void runtimeClient.playgroundSession(selected.id, sessionId)
      .then((value) => { if (active) setConversation(value); })
      .catch((caught) => active && setError(message(caught)));
    return () => { active = false; };
  }, [runtimeClient, selected?.id, sessionId]);

  async function action(work: () => Promise<void>) {
    setBusy(true); setError(null);
    try { await work(); }
    catch (caught) { setError(message(caught)); }
    finally { setBusy(false); }
  }

  async function deploy() {
    if (selected === null || buildId === "") return;
    await action(async () => {
      await runtimeClient.deploySandbox(selected.id, buildId, `sandbox-${buildId}-${crypto.randomUUID()}`);
      await refresh(selected.id);
      setTab("deployment");
    });
  }

  async function startConversation() {
    if (selected === null || activeDeployment === null) return;
    await action(async () => {
      const value = await runtimeClient.createPlaygroundSession(selected.id);
      setConversation(value); setSessionId(value.session.session_id);
      await refresh(selected.id); setTab("playground");
    });
  }

  async function sendMessage() {
    if (selected === null || sessionId === "" || messageText.trim() === "") return;
    await action(async () => {
      setConversation(await runtimeClient.sendPlaygroundMessage(selected.id, sessionId, messageText.trim()));
      setMessageText("");
    });
  }

  async function resolveReview(reviewId: string, accepted: boolean) {
    if (selected === null || sessionId === "") return;
    await action(async () => {
      setConversation(await runtimeClient.resolvePlaygroundReview(selected.id, sessionId, reviewId, accepted));
    });
  }

  async function loadDiagnostics() {
    if (selected === null || sessionId === "") return;
    await action(async () => {
      setDiagnostics(await runtimeClient.sandboxDiagnostics(selected.id, sessionId));
      setTab("diagnostics");
    });
  }

  async function runSet(setId: string) {
    if (selected === null || activeDeployment === null) return;
    await action(async () => {
      await runtimeClient.runEvaluationSet(selected.id, setId, activeDeployment.id);
      await refresh(selected.id); setTab("evaluations");
    });
  }

  async function returnToAgent() {
    if (selectedRef === null) return;
    await action(async () => {
      const failure = completedOutcome(await dispatchAffordance("return_to_agent", { agent_ref: selectedRef }), "opened");
      if (failure !== null) throw new Error(failure);
    });
  }

  const review = pendingReview(conversation);
  return <section className="sandbox-home sandbox-deployment-shell" aria-labelledby="sandbox-title">
    <header><div><p>Private deployment</p><h1 id="sandbox-title">Agent Sandbox</h1><span>{selected?.name ?? "Loading exact Agent…"}</span></div><Button type="button" variant="outline" disabled={busy || selectedRef === null} onClick={() => void returnToAgent()}>Back to Agent</Button></header>
    <p>Sandbox uses the same deployed-Agent runtime as Delivery, with owner-only admission, sessions, diagnostics, and evidence.</p>
    <nav aria-label="Sandbox areas">{(["deployment", "playground", "evaluations", "diagnostics"] as const).map((item) => <Button key={item} type="button" variant={tab === item ? "default" : "outline"} onClick={() => setTab(item)}>{label(item)}</Button>)}</nav>
    {error === null ? null : <p role="alert">{error}</p>}
    {loading ? <p role="status">Loading exact Sandbox deployment…</p> : null}

    {tab === "deployment" && !loading ? <section aria-labelledby="sandbox-deployment-title">
      <h2 id="sandbox-deployment-title">Deployment</h2>
      <p>{activeDeployment === null ? "No build is deployed to Sandbox." : `Active build ${activeDeployment.build_id} · deployment ${activeDeployment.id}`}</p>
      <Field><FieldLabel htmlFor="sandbox-build">Ready immutable build</FieldLabel><select id="sandbox-build" value={buildId} disabled={busy} onChange={(event) => setBuildId(event.target.value)}><option value="">Choose a build</option>{builds.map((item) => <option key={item.id} value={item.id}>{item.id}</option>)}</select></Field>
      {selectedBuild === null ? null : <BuildNavGraph build={selectedBuild} />}
      <Button type="button" disabled={busy || buildId === "" || activeDeployment?.build_id === buildId} onClick={() => void deploy()}>{activeDeployment === null ? "Deploy to Sandbox" : "Replace Sandbox deployment"}</Button>
      <h3>Deployment history</h3><ol>{sandbox?.deployments.map((item) => <li key={item.id} data-status={item.status}><strong>{item.status}</strong><span>Build {item.build_id}</span><span>{new Date(item.created_at).toLocaleString()}</span>{item.failure_message ? <p role="alert">{item.failure_message}</p> : null}</li>)}</ol>
    </section> : null}

    {tab === "playground" && !loading ? <section aria-labelledby="sandbox-playground-title">
      <header><div><h2 id="sandbox-playground-title">Playground</h2><p>Persistent private conversations pinned to their exact deployment.</p></div><Button type="button" disabled={busy || activeDeployment === null} onClick={() => void startConversation()}>New conversation</Button></header>
      <Field><FieldLabel htmlFor="sandbox-session">Conversation</FieldLabel><select id="sandbox-session" value={sessionId} disabled={busy} onChange={(event) => setSessionId(event.target.value)}><option value="">Choose a conversation</option>{sandbox?.playground_sessions.map((item) => <option key={item.session_id} value={item.session_id}>{new Date(item.created_at).toLocaleString()} · {item.build_id}</option>)}</select></Field>
      {conversation === null ? <p>Start or select a Playground conversation.</p> : <>
        <ol className="sandbox-conversation">{conversation.projection.messages.map((item, index) => <li key={`${String(item.role)}-${index}`} data-role={String(item.role ?? "unknown")}><strong>{String(item.role ?? "Agent")}</strong><p>{String(item.content ?? "")}</p></li>)}</ol>
        {review === null ? null : <section aria-label="Review Sandbox Agent action"><h3>Review Agent action</h3><p>The action remains pending until the owner decides.</p><Button type="button" disabled={busy} onClick={() => void resolveReview(review, true)}>Approve action</Button><Button type="button" variant="outline" disabled={busy} onClick={() => void resolveReview(review, false)}>Reject action</Button></section>}
        <Field><FieldLabel htmlFor="sandbox-message">Message</FieldLabel><Textarea id="sandbox-message" value={messageText} disabled={busy} onChange={(event) => setMessageText(event.target.value)} /></Field><Button type="button" disabled={busy || messageText.trim() === ""} onClick={() => void sendMessage()}>Send message</Button><Button type="button" variant="outline" disabled={busy} onClick={() => void loadDiagnostics()}>Open diagnostics</Button>
      </>}
    </section> : null}

    {tab === "evaluations" && !loading ? <section aria-labelledby="sandbox-evaluations-title"><h2 id="sandbox-evaluations-title">Evaluations</h2><p>Evaluation owns results. Every case and explicit retry gets a fresh isolated session on the exact active Sandbox deployment.</p>{activeDeployment === null ? <p>Deploy a build before running an evaluation set.</p> : compatibleSets.length === 0 ? <p>No evaluation sets are defined for active build {activeDeployment.build_id}.</p> : <ol>{compatibleSets.map((item) => <li key={item.id}><div><strong>{item.name}</strong><span>{item.cases.length} cases</span></div><Button type="button" disabled={busy || item.cases.length === 0} onClick={() => void runSet(item.id)}>Run against Sandbox</Button><ol>{item.cases.map((evaluationCase) => <li key={evaluationCase.id}><span>{evaluationCase.title}</span><span>{evaluationCase.latest_run_attempt?.status ?? "not run"}</span>{evaluationCase.latest_run_attempt?.sandbox_session_id ? <small>Session {evaluationCase.latest_run_attempt.sandbox_session_id}</small> : null}</li>)}</ol></li>)}</ol>}</section> : null}

    {tab === "diagnostics" && !loading ? <section aria-labelledby="sandbox-diagnostics-title"><h2 id="sandbox-diagnostics-title">Private diagnostics</h2>{sessionId === "" ? <p>Select a Playground conversation first.</p> : <><Button type="button" disabled={busy} onClick={() => void loadDiagnostics()}>Refresh diagnostics</Button>{diagnostics === null ? <p>Load the exact session diagnostics.</p> : <><p>Runtime revision {diagnostics.projection.revision}</p><pre>{JSON.stringify({ surfaces: diagnostics.projection.surfaces, interactions: diagnostics.interactions }, null, 2)}</pre></>}</>}</section> : null}
  </section>;
}

function pendingReview(value: PlaygroundInteractionView | null): string | null {
  if (value === null) return null;
  for (const surface of value.projection.surfaces) {
    if (surface.component !== "agent_runtime.write_review") continue;
    const props = surface.props;
    if (typeof props === "object" && props !== null && "review_id" in props && typeof props.review_id === "string") return props.review_id;
  }
  return null;
}

function label(value: Tab) { return value[0].toUpperCase() + value.slice(1); }
function message(value: unknown) { return value instanceof Error ? value.message : "Agent Sandbox is unavailable."; }
