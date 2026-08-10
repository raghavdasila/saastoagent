import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { AgentStore } from "../agents/store";
import { completedOutcome } from "../agents/operationResult";
import type { AgentRuntimeClient } from "../builder/client";
import type { AgentBuildView, ChannelView, DeploymentView } from "../builder/models";
import type { ChannelDraftStore } from "./channelDraftStore";
import { useRouteDeckSessionVersion } from "../../routedeck/RouteDeckSessionVersionContext";
import { BuildNavGraph } from "../builder/BuildNavGraph";


export function ChannelsSurface({ dispatchAffordance, props, agentStore, runtimeClient, draftStore }: RouteDeckSurfaceComponentProps & { agentStore: AgentStore; runtimeClient: AgentRuntimeClient; draftStore: ChannelDraftStore }) {
  const sessionVersion = useRouteDeckSessionVersion();
  const agents = useSyncExternalStore(agentStore.subscribe, agentStore.snapshot);
  const selectedRef = typeof props.selected_agent_ref === "string" ? props.selected_agent_ref : null;
  const selected = useMemo(() => agents.agents.find((item) => item.id === agents.selectedId) ?? null, [agents.agents, agents.selectedId]);
  const [channels, setChannels] = useState<readonly ChannelView[]>([]);
  const [deployments, setDeployments] = useState<readonly DeploymentView[]>([]);
  const [builds, setBuilds] = useState<readonly AgentBuildView[]>([]);
  const [eligibleBuildIds, setEligibleBuildIds] = useState<ReadonlySet<string>>(new Set());
  const draft = useSyncExternalStore(
    draftStore.subscribe,
    () => draftStore.get(selected?.id ?? ""),
  );
  const name = draft.name;
  const slug = draft.slug;
  const [channelId, setChannelId] = useState("");
  const [buildId, setBuildId] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    if (selected === null) return;
    const [channelInventory, deploymentInventory, buildInventory, evaluations] = await Promise.all([
      runtimeClient.channels(selected.id), runtimeClient.deployments(selected.id),
      runtimeClient.builds(selected.id), runtimeClient.evaluations(selected.id),
    ]);
    setChannels(channelInventory.channels);
    setDeployments(deploymentInventory.deployments);
    setBuilds(buildInventory.builds);
    setEligibleBuildIds(new Set(evaluations.evaluation_sets.filter((item) => item.eligible === true).map((item) => item.build_id)));
    setChannelId((current) => channelInventory.channels.some((item) => item.id === current) ? current : (channelInventory.channels[0]?.id ?? ""));
    setBuildId((current) => buildInventory.builds.some((item) => item.id === current) ? current : (buildInventory.builds.find((item) => evaluations.evaluation_sets.some((evaluation) => evaluation.build_id === item.id && evaluation.eligible === true))?.id ?? ""));
  }

  useEffect(() => { void agentStore.refresh(); }, [agentStore]);
  useEffect(() => { agentStore.syncSelectionFromHandle(selectedRef); }, [agentStore, agents.agents, selectedRef]);
  useEffect(() => {
    let active = true;
    void refresh().catch((caught) => active && setError(message(caught)));
    const reload = () => { if (active) void refresh().catch((caught) => setError(message(caught))); };
    window.addEventListener("corpus:channels-refresh", reload);
    return () => { active = false; window.removeEventListener("corpus:channels-refresh", reload); };
  }, [selected?.id, sessionVersion]);

  async function createChannel() {
    if (selectedRef === null || selected === null) return;
    const exactName = name.trim();
    const exactSlug = slug.trim();
    if (exactName === "" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(exactSlug)) {
      setError("Enter a name and a lowercase hosted address before creating the channel.");
      return;
    }
    const created = await act("create", { agent_ref: selectedRef, name: exactName, slug: exactSlug }, "created");
    if (created) {
      draftStore.clear(selected.id);
    }
  }

  async function deploy() {
    if (selectedRef === null || channelId === "" || buildId === "") return;
    await act("deploy", { agent_ref: selectedRef, channel_id: channelId, build_id: buildId }, "deployed");
  }

  async function rollback(deployment: DeploymentView) {
    if (selectedRef === null) return;
    await act("rollback", { agent_ref: selectedRef, channel_id: deployment.channel_id, deployment_id: deployment.id }, "rolled_back");
  }

  async function setEnabled(channel: ChannelView) {
    if (selectedRef === null) return;
    await act(
      "set_enabled",
      { agent_ref: selectedRef, channel_id: channel.id, enabled: !channel.enabled },
      "availability_set",
    );
  }

  async function returnToAgent() {
    if (selectedRef === null) return;
    setBusy(true); setError(null);
    try {
      const failure = completedOutcome(await dispatchAffordance("return_to_agent", { agent_ref: selectedRef }), "opened");
      if (failure !== null) setError(failure);
    } catch (caught) { setError(message(caught)); } finally { setBusy(false); }
  }

  async function act(affordance: string, values: Parameters<typeof dispatchAffordance>[1], outcome: string): Promise<boolean> {
    setBusy(true); setError(null);
    try {
      const result = await dispatchAffordance(affordance, values);
      const failure = completedOutcome(result, outcome);
      if (failure !== null) {
        setError(failure);
        return false;
      }
      await refresh();
      return true;
    } catch (caught) {
      setError(message(caught));
      return false;
    } finally { setBusy(false); }
  }

  const eligible = builds.filter((item) => item.status === "ready" && eligibleBuildIds.has(item.id));
  return <section className="channels-home" aria-labelledby="channels-title">
    <header><p>Selected Agent</p><h1 id="channels-title">Channels and Deployment</h1><span>{selected?.name ?? "Loading exact Agent…"}</span><Button type="button" variant="outline" disabled={busy || selectedRef === null} onClick={() => void returnToAgent()}>Back to Agent</Button></header>
    {error === null ? null : <p role="alert">{error}</p>}
    <fieldset disabled={busy || selectedRef === null}><legend>Create hosted Web channel</legend><label>Name<Input value={name} onInput={(event) => { if (selected !== null) draftStore.update(selected.id, { name: event.currentTarget.value }); }} /></label><label>Address<Input value={slug} onInput={(event) => { if (selected !== null) draftStore.update(selected.id, { slug: event.currentTarget.value.toLowerCase() }); }} /></label><Button type="button" disabled={name.trim() === "" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug.trim())} onClick={() => void createChannel()}>Create channel</Button></fieldset>
    <section aria-labelledby="deploy-title"><h2 id="deploy-title">Deploy eligible build</h2>
      <label>Channel<select value={channelId} onChange={(event) => setChannelId(event.target.value)}>{channels.filter((item) => item.status === "ready").map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label>Eligible build<select value={buildId} onChange={(event) => setBuildId(event.target.value)}>{eligible.map((item) => <option key={item.id} value={item.id}>Agent version {item.agent_version} · {item.id}</option>)}</select></label>
      <Button type="button" disabled={busy || selectedRef === null || channelId === "" || buildId === ""} onClick={() => void deploy()}>Review deployment</Button>
    </section>
    <ul>{channels.map((channel) => <li key={channel.id} data-status={channel.status}><strong>{channel.name}</strong><span>/{channel.slug}</span><span>{channel.active_deployment_id === null ? "Not deployed" : channel.enabled ? "Hosted Agent enabled" : "Hosted Agent disabled"}</span>{channel.active_deployment_id === null || !channel.enabled ? null : <a href={`/public/agents/${channel.slug}`} target="_blank" rel="noreferrer">Open hosted Agent</a>}{channel.status === "ready" ? <Button type="button" disabled={busy} onClick={() => void setEnabled(channel)}>{channel.enabled ? "Review disable" : "Review enable"}</Button> : null}</li>)}</ul>
    <h2>Deployment history</h2><ul>{deployments.map((deployment) => {
      const channel = channels.find((item) => item.id === deployment.channel_id);
      const active = channel?.active_deployment_id === deployment.id;
      const build = builds.find((item) => item.id === deployment.build_id) ?? null;
      return <li key={deployment.id} data-status={deployment.status}><strong>{deployment.status}</strong><span>Build {deployment.build_id}</span><span>{deployment.bundle_hash}</span>{active && build !== null ? <details open><summary>Active deployed RouteDeck NavGraph</summary><BuildNavGraph build={build} /></details> : null}{deployment.status === "ready" && !active ? <Button type="button" disabled={busy} onClick={() => void rollback(deployment)}>Review rollback</Button> : null}</li>;
    })}</ul>
  </section>;
}

function message(value: unknown) { return value instanceof Error ? value.message : "Channels and Deployment are unavailable."; }
