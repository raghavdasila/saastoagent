import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { Button } from "@/components/ui/button";
import type { AgentStore } from "../agents/store";
import { completedOutcome } from "../agents/operationResult";
import type { DesignerClient } from "../designer/client";
import type { AgentDesignView } from "../designer/models";
import type { AgentRuntimeClient } from "./client";
import type { AgentBuildView } from "./models";
import { BuildNavGraph } from "./BuildNavGraph";
import { useRouteDeckSessionVersion } from "../../routedeck/RouteDeckSessionVersionContext";


export function BuilderSurface({ dispatchAffordance, props, agentStore, designerClient, runtimeClient }: RouteDeckSurfaceComponentProps & { agentStore: AgentStore; designerClient: DesignerClient; runtimeClient: AgentRuntimeClient }) {
  const sessionVersion = useRouteDeckSessionVersion();
  const agents = useSyncExternalStore(agentStore.subscribe, agentStore.snapshot);
  const selectedRef = typeof props.selected_agent_ref === "string" ? props.selected_agent_ref : null;
  const selected = useMemo(() => agents.agents.find((item) => item.id === agents.selectedId) ?? null, [agents.agents, agents.selectedId]);
  const [builds, setBuilds] = useState<readonly AgentBuildView[]>([]);
  const [design, setDesign] = useState<AgentDesignView | null>(null);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { void agentStore.refresh(); }, [agentStore]);
  useEffect(() => { agentStore.syncSelectionFromHandle(selectedRef); }, [agentStore, agents.agents, selectedRef]);
  useEffect(() => {
    if (selected === null) return;
    let active = true;
    void Promise.all([designerClient.get(selected.id), runtimeClient.builds(selected.id)]).then(([design, inventory]) => {
      if (!active) return;
      setDesign(design);
      setRequestId(design?.build_request?.id ?? null);
      setBuilds(inventory.builds);
    }).catch((caught) => active && setError(message(caught)));
    return () => { active = false; };
  }, [designerClient, runtimeClient, selected?.id, sessionVersion]);

  async function assemble() {
    if (selectedRef === null || selected === null || requestId === null) return;
    setBusy(true); setError(null);
    try {
      const result = await dispatchAffordance("assemble", { agent_ref: selectedRef, build_request_id: requestId });
      const failure = completedOutcome(result, "assembled");
      if (failure !== null) setError(failure);
      else setBuilds((await runtimeClient.builds(selected.id)).builds);
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

  async function openSourcePrerequisite(sourceId: string) {
    if (selectedRef === null) return;
    setBusy(true); setError(null);
    try {
      const failure = completedOutcome(
        await dispatchAffordance("open_source_prerequisite", {
          agent_ref: selectedRef,
          source_id: sourceId,
          return_to: "builder",
          target_stage: "connection",
        }),
        "opened",
      );
      if (failure !== null) setError(failure);
    } catch (caught) { setError(message(caught)); } finally { setBusy(false); }
  }

  async function continueToSandbox() {
    if (selectedRef === null) return;
    setBusy(true); setError(null);
    try {
      const failure = completedOutcome(
        await dispatchAffordance("continue_to_sandbox", { agent_ref: selectedRef }),
        "opened",
      );
      if (failure !== null) setError(failure);
    } catch (caught) { setError(message(caught)); } finally { setBusy(false); }
  }

  async function changeRuntime(
    action: "run" | "pause" | "stop" | "delete",
    buildId: string,
  ) {
    if (selectedRef === null || selected === null) return;
    setBusy(true); setError(null);
    try {
      const result = await dispatchAffordance(action, {
        agent_ref: selectedRef,
        build_id: buildId,
      });
      if (action === "delete") {
        if (result.disposition !== "requires_review") {
          setError(result.failure?.public_message ?? "Corpus could not prepare the build removal review.");
        }
        return;
      }
      const failure = completedOutcome(
        result,
        action === "run" ? "running" : action === "pause" ? "paused" : "stopped",
      );
      if (failure !== null) setError(failure);
      else setBuilds((await runtimeClient.builds(selected.id)).builds);
    } catch (caught) { setError(message(caught)); } finally { setBusy(false); }
  }

  async function generateEvaluationSet(buildId: string) {
    if (selectedRef === null) return;
    setBusy(true); setError(null);
    try {
      const result = await dispatchAffordance("generate_evaluation_set", {
        agent_ref: selectedRef,
        build_id: buildId,
        set_name: "Generated coverage",
        categories: ["paraphrase"],
      });
      const failure = completedOutcome(result, "queued");
      if (failure !== null) setError(failure);
    } catch (caught) { setError(message(caught)); } finally { setBusy(false); }
  }

  const runningBuilds = builds.filter(
    (item) => item.status === "ready" && item.runtime_lifecycle === "running",
  );
  const currentRevision = design?.revisions.find(
    (item) => item.id === design.accepted_revision_id,
  ) ?? null;
  const sourceInputs = (currentRevision?.source_inputs ?? []).flatMap((item) => {
    const sourceId = typeof item.source_id === "string" ? item.source_id : null;
    const revisionId = typeof item.source_revision_id === "string" ? item.source_revision_id : null;
    return sourceId === null || revisionId === null ? [] : [{ sourceId, revisionId }];
  });
  const requestBuilds = requestId === null
    ? []
    : builds.filter((item) => item.build_request_id === requestId);
  const latestAttempt = requestBuilds.reduce<AgentBuildView | null>(
    (latest, item) => latest === null || item.attempt_number > latest.attempt_number ? item : latest,
    null,
  );
  const canAssemble = requestId !== null
    && !requestBuilds.some((item) => item.status === "ready" || item.status === "assembling");

  return <section className="builder-home" aria-labelledby="builder-title">
    <header><p>Selected Agent</p><h1 id="builder-title">Agent Builds</h1><span>{selected?.name ?? "Loading exact Agent…"}</span><Button type="button" variant="outline" disabled={busy || selectedRef === null} onClick={() => void returnToAgent()}>Back to Agent</Button></header>
    {error === null ? null : <p role="alert">{error}</p>}
    {requestId === null ? <p>An accepted design and explicit build request are required.</p> : <Button type="button" disabled={busy || !canAssemble} onClick={() => void assemble()}>{latestAttempt?.status === "failed" ? "Retry failed build" : "Assemble accepted build"}</Button>}
    {sourceInputs.length > 0 ? <section className="builder-prerequisites" aria-labelledby="builder-prerequisites-title">
      <div><p>Exact accepted-design inputs</p><h2 id="builder-prerequisites-title">Source setup</h2><span>Resolve the exact pinned API version. If its version changes, update the accepted design before retrying explicitly.</span></div>
      <ul>{sourceInputs.map((source) => <li key={`${source.sourceId}:${source.revisionId}`}>
        <div><strong>API Source {source.sourceId}</strong><span>API version {source.revisionId}</span></div>
        <Button type="button" variant="outline" disabled={busy} onClick={() => void openSourcePrerequisite(source.sourceId)}>Open API setup</Button>
      </li>)}</ul>
    </section> : null}
    {runningBuilds.length > 0 ? <Button type="button" disabled={busy} onClick={() => void continueToSandbox()}>Continue to Sandbox</Button> : null}
    <ul className="builder-build-list">{builds.map((build) => <li className="builder-build-card" key={build.id} data-status={build.status} data-runtime-lifecycle={build.runtime_lifecycle}>
      <div className="builder-build-card__heading">
        <div><p>Build attempt {build.attempt_number}</p><h2>Agent version {build.agent_version}</h2></div>
        <span className="builder-build-card__status">{build.status}</span>
      </div>
      <dl className="builder-build-card__facts">
        <div><dt>Runtime</dt><dd>{runtimeLabel(build.runtime_lifecycle)}</dd></div>
        <div><dt>Allowed operations</dt><dd>{build.allowed_operation_ids.length}</dd></div>
        <div><dt>Build identity</dt><dd><code>{build.id}</code></dd></div>
      </dl>
      {build.status === "ready" ? <p className="builder-runtime-state">
        {runtimeAvailabilityCopy(build.runtime_lifecycle)}
      </p> : null}
      {build.failure_message ? <p>{build.failure_message}</p> : null}
      {build.status === "ready" && build.runtime_lifecycle !== "removed" ? <div className="builder-runtime-actions">
        {build.runtime_lifecycle === "running" ? <Button type="button" variant="outline" disabled={busy} onClick={() => void generateEvaluationSet(build.id)}>Generate evaluation set</Button> : null}
        {build.runtime_lifecycle === "stopped" ? <Button type="button" disabled={busy} onClick={() => void changeRuntime("run", build.id)}>Start runtime</Button> : null}
        {build.runtime_lifecycle === "paused" ? <Button type="button" disabled={busy} onClick={() => void changeRuntime("run", build.id)}>Resume runtime</Button> : null}
        {build.runtime_lifecycle === "running" ? <Button type="button" variant="outline" disabled={busy} onClick={() => void changeRuntime("pause", build.id)}>Pause runtime</Button> : null}
        {build.runtime_lifecycle === "running" || build.runtime_lifecycle === "paused" ? <Button type="button" variant="outline" disabled={busy} onClick={() => void changeRuntime("stop", build.id)}>Stop runtime</Button> : null}
        <Button type="button" variant="destructive" disabled={busy || build.runtime_lifecycle !== "stopped"} onClick={() => void changeRuntime("delete", build.id)}>Delete build runtime</Button>
      </div> : null}
      {build.runtime_lifecycle === "removed" ? <p>The draft runtime was removed. Immutable build, Sandbox, Evaluation, deployment, and Operations history is retained.</p> : null}
      {build.status === "ready" ? <BuildNavGraph build={build} /> : null}
    </li>)}</ul>
  </section>;
}

function message(value: unknown) { return value instanceof Error ? value.message : "Agent Builds are unavailable."; }

function runtimeLabel(value: AgentBuildView["runtime_lifecycle"]): string {
  if (value === "running") return "Running";
  if (value === "paused") return "Paused";
  if (value === "stopped") return "Stopped";
  return "Removed";
}

function runtimeAvailabilityCopy(value: AgentBuildView["runtime_lifecycle"]): string {
  if (value === "running") return "Ready for new Sandbox, Evaluation, and deployment work.";
  if (value === "paused") return "Paused. New Sandbox, Evaluation, and deployment work is blocked until you resume this runtime.";
  if (value === "stopped") return "Stopped. Start this runtime before beginning new Sandbox, Evaluation, or deployment work.";
  return "Removed. Immutable build and activity history remain available.";
}
