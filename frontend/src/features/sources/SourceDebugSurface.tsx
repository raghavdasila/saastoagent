import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import {
  ArrowLeft,
  Braces,
  DatabaseZap,
  FileJson,
  FlaskConical,
  Search,
  Upload,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import {
  sourceClient,
  type EvalsetResult,
  type RetrievalResult,
  type SourceView,
} from "./sourceClient";


type BusyAction = "loading" | "upload" | "retrieval" | "evalset" | "return";


export function SourceDebugSurface({
  dispatchAffordance,
}: RouteDeckSurfaceComponentProps) {
  const [sources, setSources] = useState<readonly SourceView[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busy, setBusy] = useState<BusyAction | null>("loading");
  const [error, setError] = useState<string | null>(null);
  const [sourceName, setSourceName] = useState("");
  const [sourceFile, setSourceFile] = useState<File | null>(null);
  const [fileInputKey, setFileInputKey] = useState(0);
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState("5");
  const [traceMode, setTraceMode] = useState<"bounded" | "full">("bounded");
  const [providedParams, setProvidedParams] = useState("");
  const [retrieval, setRetrieval] = useState<RetrievalResult | null>(null);
  const [evalsetId, setEvalsetId] = useState("api-debug-v1");
  const [categories, setCategories] = useState("paraphrase");
  const [tasksPerCategory, setTasksPerCategory] = useState("1");
  const [evalset, setEvalset] = useState<EvalsetResult | null>(null);
  const selected = useMemo(
    () => sources.find((source) => source.source_id === selectedId) ?? null,
    [selectedId, sources],
  );

  useEffect(() => {
    let active = true;
    void sourceClient.list().then(
      (loaded) => {
        if (!active) return;
        setSources(loaded);
        setSelectedId(loaded.at(0)?.source_id ?? null);
        setBusy(null);
      },
      (caught: unknown) => {
        if (!active) return;
        setError(errorMessage(caught));
        setBusy(null);
      },
    );
    return () => {
      active = false;
    };
  }, []);

  async function uploadSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (sourceFile === null) {
      setError("Choose an OpenAPI JSON, YAML, or YML collection.");
      return;
    }
    setBusy("upload");
    setError(null);
    try {
      const created = await sourceClient.uploadApi(sourceName.trim(), sourceFile);
      setSources((current) => [...current, created]);
      setSelectedId(created.source_id);
      setSourceName("");
      setSourceFile(null);
      setFileInputKey((current) => current + 1);
      setRetrieval(null);
      setEvalset(null);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(null);
    }
  }

  async function runRetrieval(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selected === null) return;
    setBusy("retrieval");
    setError(null);
    setRetrieval(null);
    try {
      const parsedParams = parseProvidedParams(providedParams);
      setRetrieval(await sourceClient.retrieve(selected.source_id, {
        query: query.trim(),
        top_k: Number(topK),
        trace_mode: traceMode,
        provided_params: parsedParams,
      }));
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setBusy(null);
    }
  }

  async function generateEvalset(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selected === null) return;
    setBusy("evalset");
    setError(null);
    setEvalset(null);
    try {
      const parsedCategories = categories
        .split(",")
        .map((value) => value.trim())
        .filter(Boolean);
      if (parsedCategories.length === 0) {
        throw new Error("Enter at least one evalset category.");
      }
      setEvalset(await sourceClient.generateEvalset(selected.source_id, {
        evalset_id: evalsetId.trim(),
        categories: parsedCategories,
        tasks_per_category: Number(tasksPerCategory),
        max_generation_attempts: 2,
        max_review_attempts: 2,
      }));
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
      await dispatchAffordance("return_to_home", {});
    } catch (caught) {
      setError(errorMessage(caught));
      setBusy(null);
    }
  }

  return (
    <section className="sources-debug" aria-labelledby="sources-debug-title">
      <header className="sources-debug-header">
        <div>
          <p>Experimental integration surface</p>
          <h1 id="sources-debug-title">Sources</h1>
          <span>
            Upload an API connector input, inspect its resource-first graph,
            exercise GRAG retrieval, and generate independently reviewed evalsets.
          </span>
        </div>
        <Button
          type="button"
          variant="outline"
          disabled={busy !== null}
          onClick={() => void returnHome()}
        >
          <ArrowLeft data-icon="inline-start" />
          Back to Home
        </Button>
      </header>

      <p className="sources-debug-boundary">
        Debug evidence only: graph retrieval is experimental and generated
        evalset candidates are not human gold until manually audited.
      </p>

      {error === null ? null : <p className="sources-debug-error" role="alert">{error}</p>}

      <PipelineProgress
        source={selected}
        retrieval={retrieval}
        evalset={evalset}
        busy={busy}
      />

      <div className="sources-debug-layout">
        <aside className="sources-inventory" aria-label="Source inventory">
          <div className="sources-section-heading">
            <DatabaseZap aria-hidden="true" />
            <div><h2>API connector</h2><p>OpenAPI or Swagger JSON/YAML</p></div>
          </div>
          <form onSubmit={(event) => void uploadSource(event)}>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="source-name">Source name</FieldLabel>
                <Input
                  id="source-name"
                  value={sourceName}
                  maxLength={128}
                  required
                  placeholder="Billing API"
                  onChange={(event) => setSourceName(event.target.value)}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="source-file">OpenAPI collection</FieldLabel>
                <Input
                  key={fileInputKey}
                  id="source-file"
                  type="file"
                  required
                  accept=".json,.yaml,.yml,application/json,application/yaml,text/yaml"
                  onChange={(event) => setSourceFile(event.target.files?.[0] ?? null)}
                />
                <FieldDescription>
                  The original upload and generated artifacts stay owner-scoped.
                </FieldDescription>
              </Field>
              <Button type="submit" disabled={busy !== null}>
                <Upload data-icon="inline-start" />
                {busy === "upload" ? "Building graph…" : "Upload and build graph"}
              </Button>
            </FieldGroup>
          </form>
          <Separator />
          <div className="sources-list-heading">
            <h3>Uploaded sources</h3>
            <span>{sources.length}</span>
          </div>
          {busy === "loading" ? <p role="status">Loading sources…</p> : null}
          {busy !== "loading" && sources.length === 0 ? (
            <p className="sources-empty">No API sources uploaded yet.</p>
          ) : null}
          <ul className="sources-list">
            {sources.map((source) => (
              <li key={source.source_id}>
                <button
                  type="button"
                  data-selected={source.source_id === selectedId}
                  onClick={() => {
                    setSelectedId(source.source_id);
                    setRetrieval(null);
                    setEvalset(null);
                  }}
                >
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
            <div className="sources-workbench-empty">
              <Braces aria-hidden="true" />
              <h2>Select or upload an API source</h2>
              <p>The graph, retrieval trace, and evalset controls will appear here.</p>
            </div>
          ) : (
            <>
              <SourceOverview source={selected} />
              <Separator />
              <section className="sources-tool" aria-labelledby="retrieval-title">
                <div className="sources-section-heading">
                  <Search aria-hidden="true" />
                  <div><h2 id="retrieval-title">GRAG retrieval</h2><p>Query the persisted semantic graph</p></div>
                </div>
                <form onSubmit={(event) => void runRetrieval(event)}>
                  <FieldGroup>
                    <Field>
                      <FieldLabel htmlFor="retrieval-query">Retrieval query</FieldLabel>
                      <Input id="retrieval-query" required value={query} placeholder="Create a customer subscription" onChange={(event) => setQuery(event.target.value)} />
                    </Field>
                    <div className="sources-inline-fields">
                      <Field>
                        <FieldLabel htmlFor="retrieval-top-k">Top K</FieldLabel>
                        <Input id="retrieval-top-k" type="number" min="1" max="25" value={topK} onChange={(event) => setTopK(event.target.value)} />
                      </Field>
                      <Field>
                        <FieldLabel htmlFor="retrieval-trace">Trace</FieldLabel>
                        <select id="retrieval-trace" value={traceMode} onChange={(event) => setTraceMode(event.target.value as "bounded" | "full")}>
                          <option value="bounded">Bounded</option>
                          <option value="full">Full</option>
                        </select>
                      </Field>
                    </div>
                    <Field>
                      <FieldLabel htmlFor="retrieval-params">Provided parameters (JSON)</FieldLabel>
                      <Textarea id="retrieval-params" value={providedParams} placeholder={'{"customer_id":"cus_123"}'} onChange={(event) => setProvidedParams(event.target.value)} />
                    </Field>
                    <Button type="submit" disabled={busy !== null}>{busy === "retrieval" ? "Retrieving…" : "Run retrieval"}</Button>
                  </FieldGroup>
                </form>
                {retrieval === null ? null : <RetrievalEvidence result={retrieval} />}
              </section>
              <Separator />
              <section className="sources-tool" aria-labelledby="evalset-title">
                <div className="sources-section-heading">
                  <FlaskConical aria-hidden="true" />
                  <div><h2 id="evalset-title">Evalset factory</h2><p>Generator + independent reviewer</p></div>
                </div>
                <form onSubmit={(event) => void generateEvalset(event)}>
                  <FieldGroup>
                    <div className="sources-inline-fields">
                      <Field>
                        <FieldLabel htmlFor="evalset-id">Evalset ID</FieldLabel>
                        <Input id="evalset-id" required value={evalsetId} onChange={(event) => setEvalsetId(event.target.value)} />
                      </Field>
                      <Field>
                        <FieldLabel htmlFor="evalset-count">Tasks per category</FieldLabel>
                        <Input id="evalset-count" type="number" min="1" max="10" value={tasksPerCategory} onChange={(event) => setTasksPerCategory(event.target.value)} />
                      </Field>
                    </div>
                    <Field>
                      <FieldLabel htmlFor="evalset-categories">Categories</FieldLabel>
                      <Input id="evalset-categories" value={categories} onChange={(event) => setCategories(event.target.value)} />
                      <FieldDescription>Comma-separated; source-grounded categories only.</FieldDescription>
                    </Field>
                    <Button type="submit" disabled={busy !== null}>{busy === "evalset" ? "Generating and reviewing…" : "Generate evalset"}</Button>
                  </FieldGroup>
                </form>
                {evalset === null ? null : <EvalsetEvidence result={evalset} />}
              </section>
            </>
          )}
        </main>
      </div>
    </section>
  );
}


function PipelineProgress({
  source,
  retrieval,
  evalset,
  busy,
}: {
  source: SourceView | null;
  retrieval: RetrievalResult | null;
  evalset: EvalsetResult | null;
  busy: BusyAction | null;
}) {
  const sourceReady = source?.revision.state === "ready";
  const stages = [
    {
      title: "API collection",
      detail: source === null
        ? "Upload a collection to begin"
        : `${source.revision.original_filename} uploaded`,
      state: source === null ? "active" : "complete",
    },
    {
      title: "Graph + index",
      detail: sourceReady
        ? "Graph and index ready"
        : source === null
          ? "Waiting for collection"
          : "Building graph and index",
      state: sourceReady ? "complete" : source === null ? "waiting" : "active",
    },
    {
      title: "GRAG retrieval",
      detail: retrieval !== null
        ? "Retrieval complete"
        : busy === "retrieval"
          ? "Running retrieval"
          : sourceReady
            ? "Run a query"
            : "Waiting for graph",
      state: retrieval !== null ? "complete" : sourceReady ? "active" : "waiting",
    },
    {
      title: "Reviewed evalset",
      detail: evalset !== null
        ? "Evalset ready"
        : busy === "evalset"
          ? "Generating and reviewing"
          : retrieval !== null
            ? "Generate reviewed candidates"
            : "Waiting for retrieval",
      state: evalset !== null ? "complete" : retrieval !== null ? "active" : "waiting",
    },
  ] as const;

  return (
    <section className="sources-pipeline" aria-label="API connector ToolRouter pipeline">
      <header>
        <h2>Full pipeline evidence</h2>
        <p>API connector input through the private ToolRouter adapter.</p>
      </header>
      <ol>
        {stages.map((stage, index) => (
          <li
            key={stage.title}
            data-state={stage.state}
            aria-current={stage.state === "active" ? "step" : undefined}
          >
            <span aria-hidden="true">{index + 1}</span>
            <div>
              <strong>{stage.title}</strong>
              <small>{stage.detail}</small>
            </div>
            <em>{stage.state}</em>
          </li>
        ))}
      </ol>
    </section>
  );
}


function SourceOverview({ source }: { source: SourceView }) {
  const summary = source.revision.summary;
  return (
    <section className="source-overview" aria-labelledby="source-overview-title">
      <div><p>Selected source</p><h2 id="source-overview-title">{source.display_name}</h2><span>{source.revision.original_filename}</span></div>
      <dl>
        <Metric label="Endpoints" value={summary.endpoint_count} />
        <Metric label="Graph nodes" value={summary.graph_node_count} />
        <Metric label="Graph edges" value={summary.graph_edge_count} />
        <Metric label="Cards" value={summary.graph_card_count} />
      </dl>
    </section>
  );
}


function Metric({ label, value }: { label: string; value: unknown }) {
  return <div><dt>{label}</dt><dd>{typeof value === "number" ? value : "—"}</dd></div>;
}


function RetrievalEvidence({ result }: { result: RetrievalResult }) {
  return (
    <section className="sources-evidence" aria-label="Retrieval result">
      <header><strong>{result.decision_type}</strong><span>{result.decision_reason}</span></header>
      {result.missing_inputs.length === 0 ? null : <p>Missing: {result.missing_inputs.join(", ")}</p>}
      <ol>
        {result.steps.flatMap((step) => step.ranked_items.map((item) => (
          <li key={`${step.query}-${item.item_id}`}><code>{item.item_id}</code><span>{item.score.toFixed(4)}</span></li>
        )))}
      </ol>
      <details><summary>Trace and decision evidence</summary><pre>{JSON.stringify({ steps: result.steps, decision_evidence: result.decision_evidence, ambiguity: result.ambiguity }, null, 2)}</pre></details>
    </section>
  );
}


function EvalsetEvidence({ result }: { result: EvalsetResult }) {
  return (
    <section className="sources-evidence" aria-label="Evalset result">
      <header><strong data-state={result.status}>{result.status}</strong><span>{result.accepted_count} accepted / {result.completed_count} completed</span></header>
      <dl className="evalset-models">
        <div><dt>Generator</dt><dd>{result.generator_model}</dd></div>
        <div><dt>Reviewer</dt><dd>{result.reviewer_model}</dd></div>
        <div><dt>Offline tokens</dt><dd>{result.offline_tokens}</dd></div>
        <div><dt>Quarantined</dt><dd>{result.quarantined_count}</dd></div>
      </dl>
      <details><summary>Run evidence</summary><pre>{JSON.stringify(result, null, 2)}</pre></details>
    </section>
  );
}


function parseProvidedParams(value: string): Readonly<Record<string, unknown>> | null {
  if (!value.trim()) return null;
  const parsed: unknown = JSON.parse(value);
  if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error("Provided parameters must be a JSON object.");
  }
  return parsed as Readonly<Record<string, unknown>>;
}


function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "The Sources action failed.";
}
