import { useCallback, useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { FormEvent } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import type { RouteDeckPrivateFormBinding } from "@routedeck/react";
import { ArrowLeft, ArrowRight, FileJson, Plus, RefreshCcw, Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, FieldDescription, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";

import { SourceClient, type SourceView } from "./sourceClient";
import { ApiGraphPanel } from "./ApiGraphPanel";
import { ApiConnectionPanel } from "./ApiConnectionPanel";
import { ApiOperationCurationPanel } from "./ApiOperationCurationPanel";
import type { ContractRevisionStore } from "./contractRevisionStore";
import { resultMessage } from "./ApiContractRevisionPanel";
import { useRouteDeckSessionVersion } from "../../routedeck/RouteDeckSessionVersionContext";


export function SourceHubSurface({
  dispatchAffordance,
  props: surfaceProps,
  sourceClient,
  privateForm,
  contractRevisionStore,
  view = "api",
}: RouteDeckSurfaceComponentProps & {
  sourceClient: SourceClient;
  privateForm: RouteDeckPrivateFormBinding | null;
  contractRevisionStore: ContractRevisionStore;
  view?: "hub" | "api";
}) {
  const sessionVersion = useRouteDeckSessionVersion();
  const [sources, setSources] = useState<readonly SourceView[]>([]);
  const handoffAgentRef = typeof surfaceProps.return_agent_ref === "string" ? surfaceProps.return_agent_ref : null;
  const handoffMode = surfaceProps.agent_handoff_mode === "create" || surfaceProps.agent_handoff_mode === "inspect"
    ? surfaceProps.agent_handoff_mode
    : null;
  const selectedFromHandoff = typeof surfaceProps.selected_source_id === "string" ? surfaceProps.selected_source_id : null;
  const selectedRevisionFromHandoff = typeof surfaceProps.selected_source_revision_id === "string" ? surfaceProps.selected_source_revision_id : null;
  const [selectedId, setSelectedId] = useState<string | null>(selectedFromHandoff);
  const [showIntake, setShowIntake] = useState(view === "api" && surfaceProps.mode === "create");
  const [name, setName] = useState("");
  const [definition, setDefinition] = useState<File | null>(null);
  const [description, setDescription] = useState<File | null>(null);
  const [busy, setBusy] = useState<"loading" | "opening" | "upload" | "process" | "retry" | "return" | "attach" | "agent" | "contract" | "planning" | null>("loading");
  const [error, setError] = useState<string | null>(null);
  const contractSnapshot = useSyncExternalStore(
    contractRevisionStore.subscribe,
    contractRevisionStore.snapshot,
  );

  const refresh = useCallback(async () => {
    let current = await sourceClient.list();
    if (selectedFromHandoff !== null && selectedRevisionFromHandoff !== null) {
      const historical = await sourceClient.get(selectedFromHandoff, selectedRevisionFromHandoff);
      current = [
        ...current.filter((item) => item.source_id !== historical.source_id),
        historical,
      ];
    }
    setSources(current);
    setSelectedId((selected) =>
      selected !== null && current.some((source) => source.source_id === selected)
        ? selected
        : current.at(-1)?.source_id ?? null,
    );
    return current;
  }, [selectedFromHandoff, selectedRevisionFromHandoff, sourceClient]);

  useEffect(() => {
    let active = true;
    void refresh()
      .catch((caught) => active && setError(errorMessage(caught)))
      .finally(() => active && setBusy(null));
    return () => { active = false; };
  }, [refresh, sessionVersion]);

  useEffect(() => {
    if (contractSnapshot.approvalSequence > 0) {
      void refresh().catch((caught) => setError(errorMessage(caught)));
    }
  }, [contractSnapshot.approvalSequence, refresh]);

  useEffect(() => {
    if (surfaceProps.mode === "create") setShowIntake(true);
    if (selectedFromHandoff !== null) setSelectedId(selectedFromHandoff);
  }, [selectedFromHandoff, surfaceProps.mode]);

  const hasActive = sources.some(({ revision }) =>
    revision.state === "queued" || revision.state === "running"
  );
  useEffect(() => {
    if (!hasActive) return;
    const timer = window.setInterval(() => {
      void refresh().catch((caught) => setError(errorMessage(caught)));
    }, 1500);
    return () => window.clearInterval(timer);
  }, [hasActive, refresh]);

  const selected = useMemo(
    () => sources.find((source) => source.source_id === selectedId) ?? null,
    [selectedId, sources],
  );

  async function openIntake() {
    setBusy("opening");
    setError(null);
    try {
      const result = await dispatchAffordance("open_api_creation", {});
      if (!isCompleted(result, "opened")) throw new Error("API source creation could not be opened.");
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(null);
    }
  }

  async function openApiSource(source: SourceView) {
    setBusy("opening");
    setError(null);
    try {
      const result = await dispatchAffordance("open_api_source", {
        source_id: source.source_id,
        source_revision_id: source.revision.revision_id,
      });
      if (!isCompleted(result, "opened")) throw new Error("The API Source could not be opened.");
    } catch (caught) {
      setError(errorMessage(caught));
      setBusy(null);
    }
  }

  async function returnToSourceHub() {
    setBusy("return");
    setError(null);
    try {
      const result = await dispatchAffordance("return_to_source_hub", {});
      if (!isCompleted(result, "opened")) throw new Error("Source Hub could not be opened.");
    } catch (caught) {
      setError(errorMessage(caught));
      setBusy(null);
    }
  }

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (definition === null) return;
    setBusy("upload");
    setError(null);
    try {
      await sourceClient.stageApiDefinition(name.trim(), definition, description);
      const result = await dispatchAffordance("accept_staged_api", {});
      if (!isCompleted(result, "accepted")) {
        throw new Error("The API definition could not be added.");
      }
      const staged = await sourceClient.currentStagedApiDefinition();
      if (staged?.source_id === null || staged?.source_id === undefined) {
        throw new Error("The added API definition is unavailable.");
      }
      setShowIntake(false);
      setName("");
      setDefinition(null);
      setDescription(null);
      await refresh();
      setSelectedId(staged.source_id);
    } catch (caught) {
      setError(errorMessage(caught));
      await refresh().catch(() => undefined);
    } finally {
      setBusy(null);
    }
  }

  async function processApi() {
    if (selected === null || selected.revision.state !== "accepted") return;
    setBusy("process");
    setError(null);
    try {
      const result = await dispatchAffordance("process_api", {
        source_id: selected.source_id,
      });
      if (!isCompleted(result, "queued")) {
        throw new Error("API analysis could not be started.");
      }
      await refresh();
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(null);
    }
  }

  async function retry() {
    if (selected === null) return;
    setBusy("retry");
    setError(null);
    try {
      const result = await dispatchAffordance("retry_processing", {
        source_id: selected.source_id,
      });
      if (!isCompleted(result, "queued")) throw new Error("Source processing could not be retried.");
      await refresh();
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(null);
    }
  }

  async function returnHome() {
    setBusy("return");
    setError(null);
    try {
      const result = await dispatchAffordance("return_to_home", {});
      if (!isCompleted(result, "opened")) throw new Error("Workspace Home could not be opened.");
    } catch (caught) {
      setError(errorMessage(caught));
      setBusy(null);
    }
  }

  async function returnToAgent() {
    if (handoffAgentRef === null) return;
    setBusy("return");
    setError(null);
    try {
      const result = await dispatchAffordance("return_to_agent", { agent_ref: handoffAgentRef });
      if (!isCompleted(result, "opened")) throw new Error("The selected Agent could not be reopened.");
    } catch (caught) {
      setError(errorMessage(caught));
      setBusy(null);
    }
  }

  async function attachAndReturn() {
    if (handoffAgentRef === null || selected === null || selected.revision.state !== "ready") return;
    setBusy("attach");
    setError(null);
    try {
      const result = await dispatchAffordance("attach_created_source", {
        agent_ref: handoffAgentRef,
        source_id: selected.source_id,
      });
      if (!isCompleted(result, "attached")) throw new Error("The ready Source could not be attached.");
    } catch (caught) {
      setError(errorMessage(caught));
      setBusy(null);
    }
  }

  async function openAgentInventory() {
    setBusy("agent");
    setError(null);
    try {
      const result = await dispatchAffordance("open_agent_inventory", {});
      if (!isCompleted(result, "opened")) {
        throw new Error(resultMessage(result, "The Agent inventory could not be opened."));
      }
    } catch (caught) {
      setError(errorMessage(caught));
      setBusy(null);
    }
  }

  async function openAgentCreation() {
    setBusy("agent");
    setError(null);
    try {
      const result = await dispatchAffordance("open_agent_creation", {});
      if (!isCompleted(result, "opened")) {
        throw new Error(resultMessage(result, "Agent creation could not be opened."));
      }
    } catch (caught) {
      setError(errorMessage(caught));
      setBusy(null);
    }
  }

  async function proposeContractRevision() {
    if (selected === null || selected.revision.state !== "ready") return;
    setBusy("contract");
    setError(null);
    try {
      const result = await dispatchAffordance("propose_contract_revision", {
        source_id: selected.source_id,
        revision_id: selected.revision.revision_id,
      });
      if (!isCompleted(result, "proposed")) {
        throw new Error(resultMessage(result, "The API update proposal could not be prepared."));
      }
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(null);
    }
  }

  async function openRoutePlanner() {
    setBusy("planning");
    setError(null);
    try {
      const result = await dispatchAffordance("prepare_routed_api_test", {});
      if (!isCompleted(result, "opened")) {
        throw new Error(resultMessage(result, "The route planner could not be opened."));
      }
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(null);
    }
  }

  if (view === "hub") {
    const nextSource = sources.find(({ revision }) => revision.state !== "ready") ?? sources.at(-1) ?? null;
    return (
      <section className="sources-debug source-hub" aria-labelledby="source-hub-title">
        <header className="sources-debug-header">
          <div><p>Workspace sources</p><h1 id="source-hub-title">Source Hub</h1><span>See what is ready, what needs attention, and where to continue.</span></div>
          <div className="sources-header-actions">
            <Button type="button" disabled={busy !== null} onClick={() => void openIntake()}><Plus data-icon="inline-start" /> Add API source</Button>
            <Button type="button" variant="outline" disabled={busy !== null} onClick={() => void (handoffAgentRef === null ? returnHome() : returnToAgent())}><ArrowLeft data-icon="inline-start" /> {handoffAgentRef === null ? "Back to Home" : "Back to Agent"}</Button>
          </div>
        </header>
        {error === null ? null : <p className="sources-debug-error" role="alert">{error}</p>}
        <section className="source-hub-next" aria-labelledby="source-hub-next-title">
          <div><p>Next step</p><h2 id="source-hub-next-title">{nextSource === null ? "Add your first API source" : nextStep(nextSource)}</h2><span>{nextSource === null ? "Add an OpenAPI or Swagger definition. Nothing is analyzed until you choose to start." : nextSource.display_name}</span></div>
          {nextSource === null ? <Button type="button" onClick={() => void openIntake()}>Add API source</Button> : <Button type="button" variant="outline" onClick={() => void openApiSource(nextSource)}>Open API source <ArrowRight data-icon="inline-end" /></Button>}
        </section>
        <div className="source-hub-table" role="list" aria-label="API sources">
          {busy === "loading" ? <p role="status">Loading sources…</p> : null}
          {busy !== "loading" && sources.length === 0 ? <div className="sources-workbench-empty"><FileJson aria-hidden="true" /><h2>No API sources yet</h2><p>Add a definition when you are ready.</p></div> : null}
          {sources.map((source) => (
            <article key={source.source_id} role="listitem" className="source-hub-row">
              <FileJson aria-hidden="true" />
              <div><strong>{source.display_name}</strong><span>{source.revision.original_filename}</span></div>
              <div><em data-state={source.revision.state}>{sourceStatus(source)}</em><small>{nextStep(source)}</small></div>
              <Button type="button" variant="outline" disabled={busy !== null} onClick={() => void openApiSource(source)}>Open API source</Button>
            </article>
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="sources-debug api-source-workspace" aria-labelledby="source-hub-title">
      <header className="sources-debug-header">
        <div>
          <p>Source Hub / API Source</p>
          <h1 id="source-hub-title">{showIntake ? "Add API source" : selected?.display_name ?? "API source"}</h1>
          <span>Definition, analysis, graph, operations, connection, and attachment stay in one guided workflow.</span>
        </div>
        <div className="sources-header-actions">
          <Button type="button" variant="outline" disabled={busy !== null} onClick={() => void returnToSourceHub()}>
            <ArrowLeft data-icon="inline-start" /> Source Hub
          </Button>
        </div>
      </header>

      {error === null ? null : <p className="sources-debug-error" role="alert">{error}</p>}
      {showIntake ? (
        <form className="source-intake" onSubmit={(event) => void upload(event)}>
          <h2>Add an API source</h2>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="source-name">Source name</FieldLabel>
              <Input id="source-name" required maxLength={128} value={name} onChange={(event) => setName(event.target.value)} />
            </Field>
            <Field>
              <FieldLabel htmlFor="source-file">OpenAPI or Swagger definition</FieldLabel>
              <Input id="source-file" required type="file" accept=".json,.yaml,.yml" onChange={(event) => setDefinition(event.target.files?.[0] ?? null)} />
            </Field>
            <Field>
              <FieldLabel htmlFor="source-description">Markdown description (optional)</FieldLabel>
              <Input id="source-description" type="file" accept=".md,.markdown,text/markdown" onChange={(event) => setDescription(event.target.files?.[0] ?? null)} />
              <FieldDescription>The definition and optional description stay in this Workspace version.</FieldDescription>
            </Field>
            <div className="sources-form-actions">
              <Button type="submit" disabled={busy !== null || definition === null}>
                <Upload data-icon="inline-start" />{busy === "upload" ? "Adding…" : "Add API definition"}
              </Button>
              <Button type="button" variant="outline" disabled={busy !== null} onClick={() => setShowIntake(false)}>Cancel</Button>
            </div>
          </FieldGroup>
        </form>
      ) : null}

      <div className="sources-debug-layout api-source-layout">
        <aside className="api-workflow-rail" aria-label="API Source workflow">
          <div><p>Guided setup</p><h2>{showIntake ? "New API source" : selected?.display_name ?? "API source"}</h2></div>
          <ol>
            {apiWorkflowSteps(showIntake ? null : selected, handoffMode).map((step) => (
              <li key={step.label} data-step-state={step.state}>
                <span aria-hidden="true" />
                <div><strong>{step.label}</strong><small>{step.copy}</small></div>
              </li>
            ))}
          </ol>
          <p className="api-workflow-note">Nothing reaches the target API until you explicitly run an approved operation.</p>
        </aside>

        <main className="sources-workbench">
          {showIntake ? null : selected === null ? (
            <div className="sources-workbench-empty"><FileJson aria-hidden="true" /><h2>Open an API source from Source Hub</h2><p>Its exact saved version and analysis state will appear here.</p></div>
          ) : (
            <section className="source-detail" aria-labelledby="source-detail-title">
              <div><p>Selected API source</p><h2 id="source-detail-title">{selected.display_name}</h2><span>{selected.revision.original_filename}</span></div>
              <Separator />
              <dl className="source-detail-list">
                <div><dt>Status</dt><dd data-state={selected.revision.state}>{selected.revision.state}</dd></div>
                <div><dt>API version</dt><dd><code>{selected.revision.revision_id}</code></dd></div>
                {selected.revision.parent_revision_id == null ? null : (
                  <div><dt>Previous API version</dt><dd><code>{selected.revision.parent_revision_id}</code></dd></div>
                )}
                <div><dt>Analysis job</dt><dd><code>{selected.revision.job_id ?? "Not started"}</code></dd></div>
                <div><dt>Description</dt><dd>{selected.revision.description_filename ?? "None"}</dd></div>
                <div><dt>Updated</dt><dd>{new Date(selected.revision.updated_at).toLocaleString()}</dd></div>
              </dl>
              {selected.revision.state === "accepted" ? (
                <div className="source-ready">
                  <strong>Ready to analyze</strong>
                  <p>The API definition is saved. Analysis has not started.</p>
                  <Button type="button" disabled={busy !== null} onClick={() => void processApi()}>
                    {busy === "process" ? "Starting analysis…" : "Analyze API operations"}
                  </Button>
                </div>
              ) : null}
              {selected.revision.state === "queued" || selected.revision.state === "running" ? (
                <p role="status">Analysis is {selected.revision.state}. You can leave API Source and return later.</p>
              ) : null}
              {handoffAgentRef === null && selected.revision.state !== "failed" ? (
                <div className="source-agent-handoff">
                  <div>
                    <strong>Choose how to continue the Agent setup</strong>
                    <p>Use an existing Agent or create a new Agent while API analysis continues.</p>
                  </div>
                  <div className="sources-form-actions">
                    <Button type="button" variant="outline" disabled={busy !== null} onClick={() => void openAgentInventory()}>
                      Use an existing Agent
                    </Button>
                    <Button type="button" disabled={busy !== null} onClick={() => void openAgentCreation()}>
                      Create a new Agent
                    </Button>
                  </div>
                </div>
              ) : null}
              {selected.revision.state === "failed" ? (
                <div className="source-failure" role="alert">
                  <strong>{selected.revision.failure_code ?? "Processing failed"}</strong>
                  <p>{selected.revision.failure_message ?? "The real processing attempt failed."}</p>
                  <Button type="button" disabled={busy !== null} onClick={() => void retry()}>
                    <RefreshCcw data-icon="inline-start" />{busy === "retry" ? "Queuing retry…" : "Retry processing"}
                  </Button>
                </div>
              ) : null}
              {selected.revision.state === "ready" ? (
                <>
                  <div className="source-ready"><strong>Ready</strong><p>The ToolRouter graph and analysis for this API version are available.</p></div>
                  {selected.revision.summary.revision_kind === "reviewed_api_contract" ? (
                    <div className="source-ready contract-approved">
                      <strong>Validated API version</strong>
                      <p>This immutable API version retains its previous version and inherited ToolRouter evidence.</p>
                      <Button type="button" disabled={busy !== null} onClick={() => void openRoutePlanner()}>
                        {busy === "planning" ? "Opening planner…" : "Plan routed operation"}
                      </Button>
                    </div>
                  ) : (
                    <div className="source-contract-action">
                      <div>
                        <strong>Review API changes</strong>
                        <p>Prepare the validated API changes locally. This does not call the target API.</p>
                      </div>
                      <Button type="button" disabled={busy !== null} onClick={() => void proposeContractRevision()}>
                        {busy === "contract" ? "Preparing review…" : "Review API changes"}
                      </Button>
                    </div>
                  )}
                  {handoffMode === "create" && handoffAgentRef !== null ? (
                    <div className="source-agent-handoff">
                      <div><strong>Ready to attach</strong><p>Attach this exact API version to the selected Agent.</p></div>
                      <Button type="button" disabled={busy !== null} onClick={() => void attachAndReturn()}>
                        {busy === "attach" ? "Attaching…" : "Attach and return to Agent"}
                      </Button>
                    </div>
                  ) : null}
                  <ApiGraphPanel
                    sourceId={selected.source_id}
                    sourceClient={sourceClient}
                    dispatchAffordance={dispatchAffordance}
                  />
                  <ApiOperationCurationPanel
                    key={`${selected.source_id}:${selected.revision.revision_id}`}
                    sourceId={selected.source_id}
                    sourceRevisionId={selected.revision.revision_id}
                    sourceClient={sourceClient}
                    dispatchAffordance={dispatchAffordance}
                  />
                  {privateForm === null ? null : <ApiConnectionPanel
                    sourceId={selected.source_id}
                    sourceRevisionId={selected.revision.revision_id}
                    safeCheckEnabled={
                      selected.revision.summary.revision_kind === "reviewed_api_contract"
                      && selected.revision.summary.final_canonical_sha256
                        === "6fca793be700dfb8bf511c2217d72cf97abf2f6cba08fbc2cd26ef0369b8f3f6"
                    }
                    sourceClient={sourceClient}
                    privateForm={privateForm}
                    dispatchAffordance={dispatchAffordance}
                  />}
                </>
              ) : null}
            </section>
          )}
        </main>
      </div>
    </section>
  );
}


function isCompleted(value: unknown, outcome: string): boolean {
  if (value === null || typeof value !== "object") return false;
  const result = value as { outcome?: unknown; status?: unknown };
  return result.outcome === outcome || result.status === "completed";
}


function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "The Sources action failed.";
}

function sourceStatus(source: SourceView): string {
  switch (source.revision.state) {
    case "accepted": return "Ready to analyze";
    case "queued": return "Analysis queued";
    case "running": return "Analyzing";
    case "ready": return "Ready";
    case "failed": return "Needs attention";
  }
}

function nextStep(source: SourceView): string {
  switch (source.revision.state) {
    case "accepted": return "Analyze API operations";
    case "queued":
    case "running": return "Wait for analysis to finish";
    case "failed": return "Review the failure and retry";
    case "ready": return "Review the graph and select operations";
  }
}

function apiWorkflowSteps(
  source: SourceView | null,
  handoffMode: "create" | "inspect" | null,
): ReadonlyArray<{ label: string; copy: string; state: "current" | "complete" | "upcoming" }> {
  const analyzed = source?.revision.state === "ready";
  const analysisActive = source !== null && !analyzed;
  return [
    {
      label: "1. Definition",
      copy: source === null ? "Add an OpenAPI or Swagger file" : "Definition saved",
      state: source === null ? "current" : "complete",
    },
    {
      label: "2. Analyze",
      copy: analyzed ? "Analysis complete" : source?.revision.state === "accepted" ? "Ready when you choose" : analysisActive ? sourceStatus(source) : "After the definition is saved",
      state: analyzed ? "complete" : analysisActive ? "current" : "upcoming",
    },
    { label: "3. Semantic graph", copy: analyzed ? "Inspect the full graph and replay" : "Available after analysis", state: analyzed ? "current" : "upcoming" },
    { label: "4. Operations", copy: analyzed ? "Include or exclude every operation" : "Available after analysis", state: "upcoming" },
    { label: "5. Connection", copy: analyzed ? "Save and safely verify access" : "Available after analysis", state: "upcoming" },
    { label: "6. Attach", copy: handoffMode === "create" ? "Return this exact version to the Agent" : "Attach from the selected Agent", state: "upcoming" },
  ];
}
