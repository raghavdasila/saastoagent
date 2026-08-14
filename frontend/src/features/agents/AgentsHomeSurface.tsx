import { useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { FormEvent } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { Archive, ArrowLeft, Bot, ExternalLink, FlaskConical, Hammer, Link2, Palette, Plus, RadioTower, Save, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type { AgentStore } from "./store";
import { completedOutcome } from "@/shared/routedeck/operationResult";
import type { SourceInventoryClient, SourceView } from "../sources/contracts";
import { useRouteDeckSessionVersion } from "../../routedeck/RouteDeckSessionVersionContext";

type AgentArea = "hub" | "designer" | "builds" | "sandbox" | "evaluation" | "channels";
type BusyAction = "create" | "save" | "return" | "select" | "attach" | "detach" | "source-create" | "source-open" | "archive" | "delete" | "area" | "build-source";

export function AgentsHomeSurface({
  dispatchAffordance,
  props: surfaceProps,
  store,
  sourceClient,
}: RouteDeckSurfaceComponentProps & { store: AgentStore; sourceClient: SourceInventoryClient }) {
  const sessionVersion = useRouteDeckSessionVersion();
  const snapshot = useSyncExternalStore(store.subscribe, store.snapshot);
  const selected = useMemo(
    () =>
      snapshot.agents.find((agent) => agent.id === snapshot.selectedId) ?? null,
    [snapshot.agents, snapshot.selectedId],
  );
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [instructions, setInstructions] = useState("");
  const [busy, setBusy] = useState<BusyAction | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [sources, setSources] = useState<readonly SourceView[]>([]);
  const [sourcesLoaded, setSourcesLoaded] = useState(false);
  const [sourceId, setSourceId] = useState("");
  const selectedAgentRef = typeof surfaceProps.selected_agent_ref === "string"
    ? surfaceProps.selected_agent_ref
    : null;
  const pendingSourceId = typeof surfaceProps.pending_source_id === "string"
    ? surfaceProps.pending_source_id
    : null;
  const pendingSourceRevisionId = typeof surfaceProps.pending_source_revision_id === "string"
    ? surfaceProps.pending_source_revision_id
    : null;
  const pendingSourceDisplayName = typeof surfaceProps.pending_source_display_name === "string"
    ? surfaceProps.pending_source_display_name
    : null;
  const selectedArea: AgentArea = surfaceProps.selected_agent_area === "designer" ||
    surfaceProps.selected_agent_area === "builds" ||
    surfaceProps.selected_agent_area === "sandbox" ||
    surfaceProps.selected_agent_area === "evaluation" ||
    surfaceProps.selected_agent_area === "channels"
    ? surfaceProps.selected_agent_area
    : "hub";

  useEffect(() => {
    void store.refresh();
  }, [sessionVersion, store]);

  useEffect(() => {
    store.syncSelectionFromHandle(selectedAgentRef);
  }, [selectedAgentRef, snapshot.agents, store]);

  useEffect(() => {
    setName(selected?.name ?? "");
    setDescription(selected?.description ?? "");
    setInstructions(selected?.instructions ?? "");
    setActionError(null);
  }, [selected?.id, selected?.current_version]);

  useEffect(() => {
    if (selected === null && pendingSourceId === null) return;
    setSourcesLoaded(false);
    void sourceClient.list()
      .then((next) => setSources(next))
      .catch((error) => setActionError(errorMessage(error)))
      .finally(() => setSourcesLoaded(true));
  }, [pendingSourceId, selected?.id, sessionVersion, sourceClient]);

  useEffect(() => {
    if (selected === null) return;
    void Promise.all([
      store.refreshAttachments(selected.id),
      store.refreshDependencies(selected.id),
      store.refreshBuilds(selected.id),
      store.refreshProductOverview(selected.id),
    ]).catch((error) => setActionError(errorMessage(error)));
  }, [selected?.id, sessionVersion, store]);

  const pendingSource = useMemo(
    () => pendingSourceId === null || pendingSourceRevisionId === null
      ? null
      : sources.find((source) =>
          source.source_id === pendingSourceId &&
          source.revision.revision_id === pendingSourceRevisionId &&
          source.revision.state === "ready"
        ) ?? null,
    [pendingSourceId, pendingSourceRevisionId, sources],
  );

  useEffect(() => {
    if (pendingSource !== null) setSourceId(pendingSource.source_id);
  }, [pendingSource]);

  async function selectAgent(agentId: string) {
    setBusy("select");
    setActionError(null);
    try {
      const result = await dispatchAffordance("select_agent", { agent_id: agentId });
      const failure = completedOutcome(result, "selected");
      if (failure !== null) setActionError(failure);
      else store.select(agentId);
    } catch (error) {
      setActionError(errorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  async function openCreate() {
    setBusy("create");
    setActionError(null);
    try {
      const result = await dispatchAffordance("open_create", {});
      const failure = completedOutcome(result, "opened");
      if (failure !== null) {
        setActionError(failure);
        setBusy(null);
      }
    } catch (error) {
      setActionError(errorMessage(error));
      setBusy(null);
    }
  }

  async function returnToWorkspace() {
    setBusy("return");
    setActionError(null);
    try {
      const result = await dispatchAffordance("return_to_workspace", {});
      const failure = completedOutcome(result, "opened");
      if (failure !== null) {
        setActionError(failure);
        setBusy(null);
      }
    } catch (error) {
      setActionError(errorMessage(error));
      setBusy(null);
    }
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selected === null) return;
    setBusy("save");
    setActionError(null);
    try {
      const result = await dispatchAffordance("save_changes", {
        agent_id: selected.id,
        expected_version: selected.current_version,
        name: name.trim(),
        description: description.trim(),
        instructions: instructions.trim(),
      });
      const failure = completedOutcome(result, "saved");
      if (failure !== null) {
        setActionError(failure);
      } else {
        await store.refresh();
      }
    } catch (error) {
      setActionError(errorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  async function attachSource() {
    if (selected === null || selectedAgentRef === null || sourceId === "") return;
    const source = sources.find((item) => item.source_id === sourceId);
    if (source === undefined || source.revision.state !== "ready") return;
    setBusy("attach");
    setActionError(null);
    try {
      const result = await dispatchAffordance("attach_source", {
        agent_ref: selectedAgentRef,
        source_id: sourceId,
        source_revision_id: source.revision.revision_id,
      });
      const failure = completedOutcome(result, "attached");
      if (failure !== null) setActionError(failure);
      else {
        setSourceId("");
        await Promise.all([
          store.refreshAttachments(selected.id),
          store.refreshDependencies(selected.id),
        ]);
      }
    } catch (error) {
      setActionError(errorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  async function detachSource(attachedSourceId: string) {
    if (selected === null || selectedAgentRef === null) return;
    setBusy("detach");
    setActionError(null);
    try {
      const result = await dispatchAffordance("detach_source", {
        agent_ref: selectedAgentRef,
        source_id: attachedSourceId,
      });
      const failure = completedOutcome(result, "detached");
      if (failure !== null) setActionError(failure);
      else {
        await Promise.all([
          store.refreshAttachments(selected.id),
          store.refreshDependencies(selected.id),
        ]);
      }
    } catch (error) {
      setActionError(errorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  async function createSource() {
    if (selectedAgentRef === null) return;
    setBusy("source-create");
    setActionError(null);
    try {
      const result = await dispatchAffordance("open_source_creation", { agent_ref: selectedAgentRef });
      const failure = completedOutcome(result, "opened");
      if (failure !== null) {
        setActionError(failure);
        setBusy(null);
      }
    } catch (error) {
      setActionError(errorMessage(error));
      setBusy(null);
    }
  }

  async function openAttached(source: string) {
    if (selectedAgentRef === null) return;
    setBusy("source-open");
    setActionError(null);
    try {
      const result = await dispatchAffordance("open_attached_source", {
        agent_ref: selectedAgentRef,
        source_id: source,
      });
      const failure = completedOutcome(result, "opened");
      if (failure !== null) {
        setActionError(failure);
        setBusy(null);
      }
    } catch (error) {
      setActionError(errorMessage(error));
      setBusy(null);
    }
  }

  async function requestLifecycleAction(action: "archive" | "delete") {
    if (selectedAgentRef === null) return;
    setBusy(action);
    setActionError(null);
    try {
      const result = await dispatchAffordance(
        action === "archive" ? "archive_agent" : "delete_agent",
        { agent_ref: selectedAgentRef },
      );
      if (result.disposition !== "requires_review") {
        if (selected !== null) await store.refreshDependencies(selected.id);
        setActionError(
          result.failure?.public_message ??
          "Corpus could not prepare the required lifecycle review. Reload and try again.",
        );
      }
    } catch (error) {
      setActionError(errorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  async function openArea(area: AgentArea) {
    if (selectedAgentRef === null) return;
    setBusy("area");
    setActionError(null);
    try {
      const affordance = area === "hub" ? "open_operations" : `open_${area}`;
      const result = await dispatchAffordance(affordance, { agent_ref: selectedAgentRef });
      const failure = completedOutcome(result, "opened");
      if (failure !== null) setActionError(failure);
    } catch (error) {
      setActionError(errorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  async function openBuildSource(buildId: string, sourceId: string, revisionId: string) {
    if (selectedAgentRef === null) return;
    setBusy("build-source");
    setActionError(null);
    try {
      const result = await dispatchAffordance("open_build_source_revision", {
        agent_ref: selectedAgentRef,
        build_id: buildId,
        source_id: sourceId,
        source_revision_id: revisionId,
      });
      const failure = completedOutcome(result, "opened");
      if (failure !== null) setActionError(failure);
    } catch (error) {
      setActionError(errorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  const eligibleSources = sources.filter(
    (source) => source.revision.state === "ready" &&
      !snapshot.attachments.some((attachment) =>
        attachment.source_id === source.source_id &&
        attachment.source_revision_id === source.revision.revision_id
      ),
  );
  const pendingSourceUnavailable = sourcesLoaded && pendingSourceId !== null && pendingSource === null;
  const productOverview = selected !== null && snapshot.productOverview !== null &&
      snapshot.productOverview.agent_id === selected.id &&
      snapshot.productOverview.agent_version === selected.current_version
    ? snapshot.productOverview
    : null;
  const pendingAlreadyAttached = pendingSource !== null && snapshot.attachments.some((attachment) =>
    attachment.source_id === pendingSource.source_id &&
    attachment.source_revision_id === pendingSource.revision.revision_id
  );
  const exactSelectionBound = selected !== null &&
    selectedAgentRef === `agent-${selected.id.replaceAll("-", "").slice(0, 20)}`;

  return (
    <section className="agents-home" aria-labelledby="agents-home-title">
      <header className="agents-heading">
        <div>
          <p>Workspace</p>
          <h1 id="agents-home-title">Agents</h1>
          <span>Persistent agent identities with immutable configuration history.</span>
        </div>
        <div>
          <Button
            type="button"
            variant="outline"
            disabled={busy !== null}
            onClick={() => void returnToWorkspace()}
          >
            <ArrowLeft data-icon="inline-start" />Back to Workspace
          </Button>
          <Button
            type="button"
            disabled={busy !== null}
            onClick={() => void openCreate()}
          >
            <Plus data-icon="inline-start" />Create agent
          </Button>
        </div>
      </header>

      {snapshot.error === null ? null : (
        <p className="agents-error" role="alert">{snapshot.error}</p>
      )}
      {actionError === null ? null : (
        <p className="agents-error" role="alert">{actionError}</p>
      )}
      {pendingSourceId === null || pendingSourceRevisionId === null ? null : (
        <div className="agent-pending-source" role="status">
          <div>
            <p>Pending attachment</p>
            <strong>{pendingSourceDisplayName ?? pendingSource?.display_name ?? "API Source"}</strong>
          </div>
          <span>API version <code>{pendingSourceRevisionId}</code></span>
          {pendingSourceUnavailable ? <small>The exact ready API version is no longer available. Nothing will be substituted.</small> : null}
          {pendingAlreadyAttached ? <small>This exact API version is already attached.</small> : null}
        </div>
      )}

      <div className="agents-layout">
        <aside aria-label="Agent inventory">
          <h2>Agent inventory <span>{snapshot.agents.length}</span></h2>
          {snapshot.loading && snapshot.agents.length === 0 ? (
            <p role="status">Loading agents…</p>
          ) : null}
          {!snapshot.loading && snapshot.agents.length === 0 ? (
            <div className="agents-empty">
              <Bot aria-hidden="true" />
              <strong>No agents yet</strong>
              <span>Create the first agent configuration for this Workspace.</span>
            </div>
          ) : null}
          <ul>
            {snapshot.agents.map((agent) => (
              <li key={agent.id}>
                <button
                  type="button"
                  data-selected={agent.id === snapshot.selectedId}
                  disabled={busy !== null}
                  onClick={() => void selectAgent(agent.id)}
                >
                  <Bot aria-hidden="true" />
                  <span><strong>{agent.name}</strong><small>Version {agent.current_version}</small></span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <main>
          {selected === null ? (
            <div className="agents-editor-empty">
              <Bot aria-hidden="true" />
              <h2>Select an agent</h2>
              <p>Its current configuration will appear here.</p>
            </div>
          ) : (
            <form onSubmit={(event) => void save(event)}>
              <header>
                <div><p>Current configuration</p><h2>{selected.name}</h2></div>
                <span>Version {selected.current_version}</span>
              </header>
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="agent-edit-name">Name</FieldLabel>
                  <Input id="agent-edit-name" required maxLength={120} value={name} onChange={(event) => setName(event.target.value)} />
                </Field>
                <Field>
                  <FieldLabel htmlFor="agent-edit-description">Description</FieldLabel>
                  <Input id="agent-edit-description" maxLength={500} value={description} onChange={(event) => setDescription(event.target.value)} />
                </Field>
                <Field>
                  <FieldLabel htmlFor="agent-edit-instructions">Instructions</FieldLabel>
                  <Textarea id="agent-edit-instructions" required maxLength={12000} value={instructions} onChange={(event) => setInstructions(event.target.value)} />
                </Field>
                <Button type="submit" disabled={busy !== null}>
                  <Save data-icon="inline-start" />
                  {busy === "save" ? "Saving…" : "Save new version"}
                </Button>
              </FieldGroup>
              <section className="agent-sources" aria-labelledby="agent-sources-title">
                <header>
                  <div><p>Source attachments</p><h3 id="agent-sources-title">Attached Sources</h3></div>
                  <Button type="button" variant="outline" disabled={busy !== null || !exactSelectionBound} onClick={() => void createSource()}>
                    <Plus data-icon="inline-start" /> Create and attach
                  </Button>
                </header>
                {!exactSelectionBound ? <p role="status">Select this Agent to manage its Source attachments.</p> : null}
                {snapshot.attachments.length === 0 ? <p>No Sources are attached to this Agent.</p> : (
                  <ul>
                    {snapshot.attachments.map((attachment) => (
                      <li key={attachment.source_id}>
                        <span><strong>{attachment.display_name}</strong><small>API version {attachment.source_revision_id}</small></span>
                        <div className="agent-source-actions">
                          <Button type="button" variant="outline" disabled={busy !== null || !exactSelectionBound} onClick={() => void openAttached(attachment.source_id)}>
                            <ExternalLink data-icon="inline-start" /> Open Source
                          </Button>
                          <Button
                            type="button"
                            variant="outline"
                            aria-label={`Detach ${attachment.display_name} API version ${attachment.source_revision_id}`}
                            disabled={busy !== null || !exactSelectionBound}
                            onClick={() => void detachSource(attachment.source_id)}
                          >
                            <Trash2 data-icon="inline-start" /> {busy === "detach" ? "Detaching…" : "Detach"}
                          </Button>
                        </div>
                      </li>
                    ))}
                  </ul>
                )}
                <div className="agent-source-picker">
                  <label htmlFor="agent-source-select">{pendingSourceId === null ? "Ready Workspace Source" : "Source selected from API setup"}</label>
                  <select id="agent-source-select" value={sourceId} disabled={busy !== null || !exactSelectionBound || pendingSourceId !== null} onChange={(event) => setSourceId(event.target.value)}>
                    <option value="">Select a ready Source</option>
                    {(pendingSourceId === null ? eligibleSources : pendingSource === null ? [] : [pendingSource]).map((source) => (
                      <option key={`${source.source_id}:${source.revision.revision_id}`} value={source.source_id}>
                        {sourceOptionLabel(source)}
                      </option>
                    ))}
                  </select>
                  <Button type="button" disabled={busy !== null || !exactSelectionBound || sourceId === "" || pendingSourceUnavailable || pendingAlreadyAttached} onClick={() => void attachSource()}>
                    <Link2 data-icon="inline-start" /> {busy === "attach" ? "Attaching…" : "Attach Source"}
                  </Button>
                </div>
              </section>
              <section className="agent-operations" aria-labelledby="agent-operations-title">
                <header>
                  <div><p>Selected agent</p><h3 id="agent-operations-title">Operations hub</h3></div>
                  <Button type="button" variant="outline" disabled={busy !== null || !exactSelectionBound} onClick={() => void openArea("hub")}>Operations</Button>
                </header>
                <p>Move between this Agent's Operations, Designer, Builds, Sandbox, Evaluation, and Channels areas without starting or changing work.</p>
                {productOverview === null ? <p role="status">Loading this Agent's current product lifecycle…</p> : (
                  <section className="agent-product-overview" aria-label="Selected Agent product overview">
                    <dl>
                      <div><dt>Sources</dt><dd>{productOverview.source_count} attached</dd></div>
                      <div><dt>Design</dt><dd>{productOverview.design_status}{productOverview.design_revision === null ? "" : ` · revision ${productOverview.design_revision}`}</dd></div>
                      <div><dt>Latest build</dt><dd>{productOverview.build_status ?? "None"}{productOverview.build_runtime_lifecycle === null ? "" : ` · ${productOverview.build_runtime_lifecycle}`}</dd></div>
                      <div><dt>Evaluation</dt><dd>{productOverview.evaluation_status ?? "None"} · {productOverview.evaluation_case_count} cases{productOverview.evaluation_eligible === null ? "" : productOverview.evaluation_eligible ? " · eligible" : " · not eligible"}</dd></div>
                      <div><dt>Hosted delivery</dt><dd>{productOverview.delivery_status}{productOverview.hosted_path === null ? "" : ` · ${productOverview.hosted_path}`}</dd></div>
                      <div><dt>Public interactions</dt><dd>{productOverview.operations_count}</dd></div>
                    </dl>
                    <p><strong>Recommended next step</strong><span>{productOverview.next_step}</span></p>
                  </section>
                )}
                <nav aria-label="Selected agent operations">
                  <Button type="button" variant="outline" disabled={busy !== null || !exactSelectionBound} onClick={() => void openArea("designer")}><Palette data-icon="inline-start" />Designer</Button>
                  <Button type="button" variant="outline" disabled={busy !== null || !exactSelectionBound} onClick={() => void openArea("builds")}><Hammer data-icon="inline-start" />Builds</Button>
                  <Button type="button" variant="outline" disabled={busy !== null || !exactSelectionBound} onClick={() => void openArea("sandbox")}><Bot data-icon="inline-start" />Sandbox</Button>
                  <Button type="button" variant="outline" disabled={busy !== null || !exactSelectionBound} onClick={() => void openArea("evaluation")}><FlaskConical data-icon="inline-start" />Evaluation</Button>
                  <Button type="button" variant="outline" disabled={busy !== null || !exactSelectionBound} onClick={() => void openArea("channels")}><RadioTower data-icon="inline-start" />Channels</Button>
                </nav>
                {selectedArea === "hub" ? <p role="status">Choose an area. Navigation alone creates no design, build, run, or evaluation.</p> : null}
                {selectedArea === "designer" ? <div role="region" aria-label="Agent Designer"><h4>Agent Designer</h4><p>{productOverview === null ? "Loading current design state…" : `Current design: ${productOverview.design_status}${productOverview.design_revision === null ? "." : ` revision ${productOverview.design_revision}.`}`}</p></div> : null}
                {selectedArea === "sandbox" ? <div role="region" aria-label="Agent Sandbox"><h4>Sandbox</h4><p>{productOverview?.build_status === "ready" ? `Latest build is ${productOverview.build_runtime_lifecycle ?? "ready"}.` : "A ready immutable build is required before a Sandbox run can start."}</p></div> : null}
                {selectedArea === "evaluation" ? <div role="region" aria-label="Agent Evaluation"><h4>Evaluation</h4><p>{productOverview === null ? "Loading current evaluation state…" : `${productOverview.evaluation_status ?? "No evaluation set"} · ${productOverview.evaluation_case_count} cases.`}</p></div> : null}
                {selectedArea === "channels" ? <div role="region" aria-label="Agent Channels"><h4>Channels</h4><p>{productOverview === null ? "Loading current hosted delivery state…" : `${productOverview.delivery_status}${productOverview.hosted_path === null ? "." : ` at ${productOverview.hosted_path}.`}`}</p></div> : null}
                {selectedArea === "builds" ? (
                  <div role="region" aria-label="Agent Builds">
                    <h4>Builds</h4>
                    {snapshot.builds.length === 0 ? <p>No historical builds exist for this Agent.</p> : (
                      <ul>
                        {snapshot.builds.map((build) => (
                          <li key={build.build_id}>
                            <strong>Build {build.build_id}</strong>
                            <span>Agent version {build.agent_version}</span>
                            {build.source_references.length === 0 ? <small>No Source revisions were captured.</small> : (
                              <ul>
                                {build.source_references.map((reference) => (
                                  <li key={`${build.build_id}:${reference.source_id}`}>
                                    <span><strong>{reference.display_name ?? "Unavailable Source"}</strong><small>API version {reference.source_revision_id}</small></span>
                                    <Button type="button" variant="outline" disabled={busy !== null || !exactSelectionBound || !reference.available} onClick={() => void openBuildSource(build.build_id, reference.source_id, reference.source_revision_id)}>
                                      <ExternalLink data-icon="inline-start" />Open API version
                                    </Button>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                ) : null}
              </section>
              <section className="agent-lifecycle" aria-labelledby="agent-lifecycle-title">
                <header>
                  <div><p>Consequential actions</p><h3 id="agent-lifecycle-title">Agent lifecycle</h3></div>
                </header>
                <p>Archive removes this Agent from the active inventory while preserving its record, configuration history, and Source attachments.</p>
                <p>Permanent deletion is available only when the current dependency inspection is clear. It never detaches or cascades through dependencies.</p>
                {snapshot.dependencies === null ? (
                  <p role="status">Checking current deletion dependencies…</p>
                ) : snapshot.dependencies.blocks_delete ? (
                  <p className="agent-lifecycle-blocker" role="status">
                    Delete blocked: {snapshot.dependencies.source_attachments.length} Source {snapshot.dependencies.source_attachments.length === 1 ? "attachment remains" : "attachments remain"}.
                  </p>
                ) : (
                  <p role="status">No current deletion blockers were found.</p>
                )}
                <div>
                  <Button type="button" variant="outline" disabled={busy !== null || !exactSelectionBound} onClick={() => void requestLifecycleAction("archive")}>
                    <Archive data-icon="inline-start" /> {busy === "archive" ? "Preparing review…" : "Archive Agent"}
                  </Button>
                  <Button
                    type="button"
                    variant="destructive"
                    disabled={busy !== null || !exactSelectionBound || snapshot.dependencies === null}
                    onClick={() => void requestLifecycleAction("delete")}
                  >
                    <Trash2 data-icon="inline-start" /> {busy === "delete" ? "Preparing review…" : "Delete permanently"}
                  </Button>
                </div>
              </section>
            </form>
          )}
        </main>
      </div>
    </section>
  );
}

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "The agent action failed.";
}

function sourceOptionLabel(source: SourceView): string {
  const filename = source.revision.original_filename;
  const updated = new Date(source.updated_at).toLocaleString();
  return `${source.display_name} · ${filename} · ${updated}`;
}
