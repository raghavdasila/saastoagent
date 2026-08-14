import { useEffect, useMemo, useRef, useState, useSyncExternalStore } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { AgentSelectionStore } from "../agents/contracts";
import { completedOutcome, stagedReview } from "@/shared/routedeck/operationResult";
import type { AgentRuntimeReader, AgentBuildView, ChannelView, DeploymentView } from "../builder/contracts";
import type { ChannelDraftStore } from "./channelDraftStore";
import { useRouteDeckSessionVersion } from "../../routedeck/RouteDeckSessionVersionContext";
import { BuildNavGraph } from "@/shared/agent/BuildNavGraph";


export function ChannelsSurface({ dispatchAffordance, props, agentStore, runtimeClient, draftStore }: RouteDeckSurfaceComponentProps & { agentStore: AgentSelectionStore; runtimeClient: AgentRuntimeReader; draftStore: ChannelDraftStore }) {
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const refreshGeneration = useRef(0);

  async function refresh() {
    const generation = ++refreshGeneration.current;
    if (selected === null) {
      setChannels([]); setDeployments([]); setBuilds([]); setEligibleBuildIds(new Set());
      setChannelId(""); setBuildId(""); setLoading(true);
      return;
    }
    setLoading(true);
    try {
      const [channelInventory, deploymentInventory, buildInventory, evaluations] = await Promise.all([
        runtimeClient.channels(selected.id), runtimeClient.deployments(selected.id),
        runtimeClient.builds(selected.id), runtimeClient.evaluations(selected.id),
      ]);
      if (generation !== refreshGeneration.current) return;
      setChannels(channelInventory.channels);
      setDeployments(deploymentInventory.deployments);
      setBuilds(buildInventory.builds);
      const nextEligibleBuildIds = new Set(
        evaluations.evaluation_sets
          .filter((item) => item.eligible === true)
          .map((item) => item.build_id),
      );
      setEligibleBuildIds(nextEligibleBuildIds);
      setChannelId((current) => channelInventory.channels.some((item) => item.id === current) ? current : (channelInventory.channels[0]?.id ?? ""));
      setBuildId((current) => {
        const deployable = (item: AgentBuildView) => (
          item.status === "ready"
          && item.runtime_lifecycle === "running"
          && nextEligibleBuildIds.has(item.id)
        );
        return buildInventory.builds.some(
          (item) => item.id === current && deployable(item),
        ) ? current : (buildInventory.builds.find(deployable)?.id ?? "");
      });
    } finally {
      if (generation === refreshGeneration.current) setLoading(false);
    }
  }

  useEffect(() => { void agentStore.refresh(); }, [agentStore]);
  useEffect(() => { agentStore.syncSelectionFromHandle(selectedRef); }, [agentStore, agents.agents, selectedRef]);
  useEffect(() => {
    let active = true;
    void refresh().catch((caught) => active && setError(message(caught)));
    const reload = () => { if (active) void refresh().catch((caught) => setError(message(caught))); };
    window.addEventListener("corpus:channels-refresh", reload);
    return () => { active = false; refreshGeneration.current += 1; window.removeEventListener("corpus:channels-refresh", reload); };
  }, [selected?.id, sessionVersion]);
  const hasActiveDeployment = deployments.some(
    (deployment) => deployment.status === "queued" || deployment.status === "running",
  );
  useEffect(() => {
    if (!hasActiveDeployment) return undefined;
    const timer = window.setInterval(() => {
      void refresh().catch((caught) => setError(message(caught)));
    }, 2_000);
    return () => window.clearInterval(timer);
  }, [hasActiveDeployment, selected?.id, sessionVersion]);

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
    await prepareReview(
      "deploy",
      { agent_ref: selectedRef, channel_id: channelId, build_id: buildId },
      "deployment.deploy",
    );
  }

  async function rollback(deployment: DeploymentView) {
    if (selectedRef === null) return;
    await prepareReview(
      "rollback",
      { agent_ref: selectedRef, channel_id: deployment.channel_id, deployment_id: deployment.id },
      "deployment.rollback",
    );
  }

  async function retryDeployment(deployment: DeploymentView) {
    if (selectedRef === null || deployment.status !== "failed") return;
    await prepareReview(
      "retry_deployment",
      { agent_ref: selectedRef, deployment_id: deployment.id },
      "deployment.retry",
    );
  }

  async function setEnabled(channel: ChannelView) {
    if (selectedRef === null) return;
    await prepareReview(
      "set_enabled",
      { agent_ref: selectedRef, channel_id: channel.id, enabled: !channel.enabled },
      "channels.set_enabled",
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

  async function continueToBuilds() {
    if (selectedRef === null) return;
    setBusy(true); setError(null);
    try {
      const failure = completedOutcome(
        await dispatchAffordance("continue_to_builds", { agent_ref: selectedRef }),
        "opened",
      );
      if (failure !== null) setError(failure);
    } catch (caught) { setError(message(caught)); } finally { setBusy(false); }
  }

  async function continueToOperations() {
    if (selectedRef === null) return;
    setBusy(true); setError(null);
    try {
      const failure = completedOutcome(
        await dispatchAffordance("continue_to_operations", { agent_ref: selectedRef }),
        "opened",
      );
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

  async function prepareReview(
    affordance: string,
    values: Parameters<typeof dispatchAffordance>[1],
    operationId: string,
  ): Promise<void> {
    setBusy(true); setError(null);
    try {
      const failure = stagedReview(await dispatchAffordance(affordance, values), operationId);
      if (failure !== null) setError(failure);
    } catch (caught) {
      setError(message(caught));
    } finally { setBusy(false); }
  }

  const evaluated = builds.filter(
    (item) => item.status === "ready" && eligibleBuildIds.has(item.id),
  );
  const eligible = evaluated.filter((item) => item.runtime_lifecycle === "running");
  const activeDeploymentCount = channels.filter((channel) => channel.active_deployment_id !== null).length;
  return <section className="channels-home" aria-labelledby="channels-title">
    <header><p>Selected Agent</p><h1 id="channels-title">Channels and Deployment</h1><span>{selected?.name ?? "Loading exact Agent…"}</span><Button type="button" variant="outline" disabled={busy || selectedRef === null} onClick={() => void returnToAgent()}>Back to Agent</Button></header>
    {error === null ? null : <p role="alert">{error}</p>}
    {loading ? <p className="channels-home__loading" role="status">Loading exact channel, build, evaluation, and deployment stateâ€¦</p> : null}
    <section className="channels-home__readiness" aria-labelledby="delivery-readiness-title" aria-busy={loading}>
      <div>
        <p className="channels-home__eyebrow">Publishing readiness</p>
        <h2 id="delivery-readiness-title">What is ready for customers</h2>
      </div>
      <dl>
        <div><dt>Hosted channels</dt><dd>{channels.length}</dd></div>
        <div><dt>Eligible builds</dt><dd>{eligible.length}</dd></div>
        <div><dt>Active deployments</dt><dd>{activeDeploymentCount}</dd></div>
      </dl>
      {!loading && eligible.length === 0 ? <div className="channels-home__blocked">
        {evaluated.length === 0 ? <><div><strong>No evaluated build is eligible to publish.</strong><span>Continue with this exact Agent in Evaluation. Corpus will not select or substitute another build.</span></div>
        <Button type="button" variant="outline" disabled={busy || selectedRef === null} onClick={() => void continueToEvaluation()}>Continue in Evaluation</Button></> : <><div><strong>The eligible build is not running.</strong><span>Continue with this exact Agent in Builds and start the approved build before returning here.</span></div>
        <Button type="button" variant="outline" disabled={busy || selectedRef === null} onClick={() => void continueToBuilds()}>Continue in Builds</Button></>}
      </div> : !loading ? <p className="channels-home__ready">A running evaluated build is ready to review for deployment.</p> : null}
    </section>
    <div className="channels-home__setup">
    <fieldset className="channels-home__step" disabled={loading || busy || selectedRef === null}><legend><span>1</span> Create hosted Web channel</legend><p>Name the public experience and reserve its Corpus-hosted address.</p><label>Name<Input value={name} onInput={(event) => { if (selected !== null) draftStore.update(selected.id, { name: event.currentTarget.value }); }} /></label><label>Address<Input value={slug} onInput={(event) => { if (selected !== null) draftStore.update(selected.id, { slug: event.currentTarget.value.toLowerCase() }); }} /></label><Button type="button" disabled={name.trim() === "" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug.trim())} onClick={() => void createChannel()}>Create hosted channel</Button></fieldset>
    <section className="channels-home__step" aria-labelledby="deploy-title"><div className="channels-home__step-title"><span>2</span><div><h2 id="deploy-title">Review eligible build</h2><p>Choose the exact evaluated build and channel. Deployment requires your approval.</p></div></div>
      <label>Channel<select value={channelId} onChange={(event) => setChannelId(event.target.value)}>{channels.length === 0 ? <option value="">Create a channel first</option> : channels.filter((item) => item.status === "ready").map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label>Eligible build<select disabled={loading} value={buildId} onChange={(event) => setBuildId(event.target.value)}>{loading ? <option value="">Loading evaluated builds…</option> : eligible.length === 0 ? <option value="">Finish Evaluation first</option> : eligible.map((item) => <option key={item.id} value={item.id}>{buildIdentity(item)}</option>)}</select></label>
      <Button type="button" disabled={loading || busy || selectedRef === null || channelId === "" || buildId === ""} onClick={() => void deploy()}>Review deployment</Button>
    </section>
    </div>
    {!loading && channels.length === 0 ? null : <section className="channels-home__inventory" aria-labelledby="hosted-agents-title"><div><p className="channels-home__eyebrow">Live destinations</p><h2 id="hosted-agents-title">Hosted Agents</h2></div><ul>{channels.map((channel) => <li key={channel.id} data-status={channel.status}><div><strong>{channel.name}</strong><span>/{channel.slug}</span></div><span>{channel.active_deployment_id === null ? "Waiting for first deployment" : channel.enabled ? "Public and available" : "Public access paused"}</span><div className="channels-home__actions">{channel.active_deployment_id === null || !channel.enabled ? null : <a href={`/public/agents/${channel.slug}`} target="_blank" rel="noreferrer">Open hosted Agent</a>}{channel.status === "ready" ? <Button type="button" variant="outline" disabled={busy} onClick={() => void setEnabled(channel)}>{channel.enabled ? "Review pause" : "Review resume"}</Button> : null}</div></li>)}</ul></section>}
    {!loading && deployments.length === 0 ? null : <section className="channels-home__inventory" aria-labelledby="deployment-history-title"><div><p className="channels-home__eyebrow">Immutable releases</p><h2 id="deployment-history-title">Deployment history</h2></div><ul>{deployments.map((deployment) => {
      const channel = channels.find((item) => item.id === deployment.channel_id);
      const active = channel?.active_deployment_id === deployment.id;
      const build = builds.find((item) => item.id === deployment.build_id) ?? null;
      return <li key={deployment.id} data-status={deployment.status}><div><strong>{active ? "Active deployment" : deployment.retry_of_deployment_id === null ? "Deployment attempt" : "Retried deployment attempt"}</strong><span>{channel?.name ?? "Hosted channel"} · {build === null ? "Build unavailable" : buildIdentity(build)}</span></div><span>{deploymentStatus(deployment)}</span>{active && build !== null ? <details open><summary>Deployed RouteDeck NavGraph</summary><BuildNavGraph build={build} /></details> : null}{deployment.status === "ready" && !active ? <Button type="button" variant="outline" disabled={busy} onClick={() => void rollback(deployment)}>Review rollback to this version</Button> : null}{deployment.status === "failed" ? <Button type="button" variant="outline" disabled={busy} onClick={() => void retryDeployment(deployment)}>Review new attempt</Button> : null}</li>;
    })}</ul></section>}
    {channels.some((channel) => channel.active_deployment_id !== null) ? <Button type="button" disabled={busy} onClick={() => void continueToOperations()}>View Operations</Button> : null}
  </section>;
}

function message(value: unknown) { return value instanceof Error ? value.message : "Channels and Deployment are unavailable."; }

function deploymentStatus(deployment: DeploymentView): string {
  if (deployment.status === "queued") return "Queued for publishing";
  if (deployment.status === "running") return "Publishing in the background";
  if (deployment.status === "ready") return "Published successfully";
  if (deployment.status === "failed") return deployment.failure_message ?? "Publishing failed";
  return "Deployment status unavailable";
}

function buildIdentity(build: AgentBuildView): string {
  return `Agent version ${build.agent_version} · Build attempt ${build.attempt_number} · ${new Date(build.created_at).toLocaleString()}`;
}
