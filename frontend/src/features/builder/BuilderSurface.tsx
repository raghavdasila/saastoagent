import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { Button } from "@/components/ui/button";
import type { AgentStore } from "../agents/store";
import { completedOutcome } from "../agents/operationResult";
import type { DesignerClient } from "../designer/client";
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

  return <section className="builder-home" aria-labelledby="builder-title">
    <header><p>Selected Agent</p><h1 id="builder-title">Agent Builds</h1><span>{selected?.name ?? "Loading exact Agent…"}</span><Button type="button" variant="outline" disabled={busy || selectedRef === null} onClick={() => void returnToAgent()}>Back to Agent</Button></header>
    {error === null ? null : <p role="alert">{error}</p>}
    {requestId === null ? <p>An accepted design and explicit build request are required.</p> : <Button type="button" disabled={busy || builds.some((item) => item.build_request_id === requestId)} onClick={() => void assemble()}>Assemble accepted build</Button>}
    <ul>{builds.map((build) => <li key={build.id} data-status={build.status}><strong>{build.status}</strong><span>Build {build.id}</span><span>Agent version {build.agent_version}</span><span>{build.allowed_operation_ids.length} operations</span>{build.failure_message ? <p>{build.failure_message}</p> : null}{build.status === "ready" ? <BuildNavGraph build={build} /> : null}</li>)}</ul>
  </section>;
}

function message(value: unknown) { return value instanceof Error ? value.message : "Agent Builds are unavailable."; }
