import { useCallback, useEffect, useMemo, useState, useSyncExternalStore } from "react";
import type { FormEvent } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import type { RouteDeckPrivateFormBinding } from "@routedeck/react";
import { ArrowLeft, FileJson, Plus, RefreshCcw, Upload } from "lucide-react";

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
}: RouteDeckSurfaceComponentProps & {
  sourceClient: SourceClient;
  privateForm: RouteDeckPrivateFormBinding;
  contractRevisionStore: ContractRevisionStore;
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
  const [showIntake, setShowIntake] = useState(false);
  const [name, setName] = useState("");
  const [definition, setDefinition] = useState<File | null>(null);
  const [description, setDescription] = useState<File | null>(null);
  const [busy, setBusy] = useState<"loading" | "opening" | "upload" | "retry" | "return" | "attach" | "contract" | "planning" | null>("loading");
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
    if (handoffMode === "create") setShowIntake(true);
    if (selectedFromHandoff !== null) setSelectedId(selectedFromHandoff);
  }, [handoffMode, selectedFromHandoff]);

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
      setShowIntake(true);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(null);
    }
  }

  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (definition === null) return;
    setBusy("upload");
    setError(null);
    try {
      const created = await sourceClient.uploadApi(name.trim(), definition, description);
      setSources((current) => [...current, created]);
      setSelectedId(created.source_id);
      setShowIntake(false);
      setName("");
      setDefinition(null);
      setDescription(null);
      await refresh();
    } catch (caught) {
      setError(errorMessage(caught));
      await refresh().catch(() => undefined);
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
        throw new Error(resultMessage(result, "The reviewed contract proposal could not be prepared."));
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

  return (
    <section className="sources-debug" aria-labelledby="source-hub-title">
      <header className="sources-debug-header">
        <div>
          <p>Workspace sources</p>
          <h1 id="source-hub-title">Source Hub</h1>
          <span>Upload an API definition, leave while it processes, and return to the persisted result.</span>
        </div>
        <div className="sources-header-actions">
          <Button type="button" disabled={busy !== null} onClick={() => void openIntake()}>
            <Plus data-icon="inline-start" /> Add API source
          </Button>
          <Button type="button" variant="outline" disabled={busy !== null} onClick={() => void (handoffAgentRef === null ? returnHome() : returnToAgent())}>
            <ArrowLeft data-icon="inline-start" /> {handoffAgentRef === null ? "Back to Home" : "Back to Agent"}
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
              <FieldDescription>The definition and optional description stay in this Workspace revision.</FieldDescription>
            </Field>
            <div className="sources-form-actions">
              <Button type="submit" disabled={busy !== null || definition === null}>
                <Upload data-icon="inline-start" />{busy === "upload" ? "Queuing…" : "Upload and process"}
              </Button>
              <Button type="button" variant="outline" disabled={busy !== null} onClick={() => setShowIntake(false)}>Cancel</Button>
            </div>
          </FieldGroup>
        </form>
      ) : null}

      <div className="sources-debug-layout">
        <aside className="sources-inventory" aria-label="Source inventory">
          <div className="sources-list-heading"><h2>API sources</h2><span>{sources.length}</span></div>
          {busy === "loading" ? <p role="status">Loading sources…</p> : null}
          {busy !== "loading" && sources.length === 0 ? <p className="sources-empty">No API sources yet.</p> : null}
          <ul className="sources-list">
            {sources.map((source) => (
              <li key={source.source_id}>
                <button type="button" data-selected={source.source_id === selectedId} onClick={() => setSelectedId(source.source_id)}>
                  <FileJson aria-hidden="true" />
                  <span><strong>{source.display_name}</strong><small>{source.revision.original_filename}</small></span>
                  <em data-state={source.revision.state}>{source.revision.state}</em>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <main className="sources-workbench">
          {selected === null ? (
            <div className="sources-workbench-empty"><FileJson aria-hidden="true" /><h2>Select a source</h2><p>Its exact persisted revision and processing state will appear here.</p></div>
          ) : (
            <section className="source-detail" aria-labelledby="source-detail-title">
              <div><p>Selected API source</p><h2 id="source-detail-title">{selected.display_name}</h2><span>{selected.revision.original_filename}</span></div>
              <Separator />
              <dl className="source-detail-list">
                <div><dt>Status</dt><dd data-state={selected.revision.state}>{selected.revision.state}</dd></div>
                <div><dt>Revision</dt><dd><code>{selected.revision.revision_id}</code></dd></div>
                {selected.revision.parent_revision_id == null ? null : (
                  <div><dt>Parent revision</dt><dd><code>{selected.revision.parent_revision_id}</code></dd></div>
                )}
                <div><dt>Job</dt><dd><code>{selected.revision.job_id ?? "Not queued"}</code></dd></div>
                <div><dt>Description</dt><dd>{selected.revision.description_filename ?? "None"}</dd></div>
                <div><dt>Updated</dt><dd>{new Date(selected.revision.updated_at).toLocaleString()}</dd></div>
              </dl>
              {selected.revision.state === "queued" || selected.revision.state === "running" ? (
                <p role="status">Processing is {selected.revision.state}. You can leave Source Hub and return later.</p>
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
                  <div className="source-ready"><strong>Ready</strong><p>The ToolRouter artifacts linked to this revision are available.</p></div>
                  {selected.revision.summary.revision_kind === "reviewed_api_contract" ? (
                    <div className="source-ready contract-approved">
                      <strong>Reviewed contract revision</strong>
                      <p>This immutable derivative retains its parent revision and inherited ToolRouter evidence.</p>
                      <Button type="button" disabled={busy !== null} onClick={() => void openRoutePlanner()}>
                        {busy === "planning" ? "Opening planner…" : "Plan routed operation"}
                      </Button>
                    </div>
                  ) : (
                    <div className="source-contract-action">
                      <div>
                        <strong>Reviewed local Medusa contract</strong>
                        <p>Prepare the locked derivative proposal locally. This does not call the target API.</p>
                      </div>
                      <Button type="button" disabled={busy !== null} onClick={() => void proposeContractRevision()}>
                        {busy === "contract" ? "Preparing proposal…" : "Prepare contract revision"}
                      </Button>
                    </div>
                  )}
                  {handoffMode === "create" && handoffAgentRef !== null ? (
                    <div className="source-agent-handoff">
                      <div><strong>Ready to attach</strong><p>Pin this exact revision to the selected Agent.</p></div>
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
                  <ApiConnectionPanel
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
                  />
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
