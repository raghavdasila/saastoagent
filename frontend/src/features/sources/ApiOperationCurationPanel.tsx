import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { Filter, RefreshCcw } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import {
  type ApiOperationCurationView,
  type SourceClient,
  SourceClientError,
} from "./sourceClient";


type Decision = "included" | "excluded";


export function ApiOperationCurationPanel({
  sourceId,
  sourceRevisionId,
  sourceClient,
  dispatchAffordance,
}: {
  sourceId: string;
  sourceRevisionId: string;
  sourceClient: SourceClient;
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"];
}) {
  const [view, setView] = useState<ApiOperationCurationView | null>(null);
  const [decisions, setDecisions] = useState<ReadonlyMap<string, Decision>>(new Map());
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState<"loading" | "saving" | null>("loading");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const requestGeneration = useRef(0);
  const activity = useRef<"loading" | "saving" | null>("loading");

  const refresh = useCallback(async () => {
    const generation = ++requestGeneration.current;
    const next = await sourceClient.inspectApiOperationCuration(sourceId, sourceRevisionId);
    if (generation !== requestGeneration.current) return null;
    const saved = new Map<string, Decision>();
    for (const operationId of next.current?.included_operation_ids ?? []) {
      saved.set(operationId, "included");
    }
    for (const operationId of next.current?.excluded_operation_ids ?? []) {
      saved.set(operationId, "excluded");
    }
    setView(next);
    setDecisions(saved);
    return next;
  }, [sourceClient, sourceId, sourceRevisionId]);

  useEffect(() => {
    let active = true;
    activity.current = "loading";
    setBusy("loading");
    setError(null);
    setMessage(null);
    void refresh()
      .catch((caught) => {
        if (active) setError(errorMessage(caught));
      })
      .finally(() => {
        if (active) {
          activity.current = null;
          setBusy(null);
        }
      });
    return () => {
      active = false;
      requestGeneration.current += 1;
    };
  }, [refresh]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase();
    if (normalized.length === 0) return view?.operations ?? [];
    return (view?.operations ?? []).filter((item) =>
      `${item.operation_id} ${item.method} ${item.path_template} ${item.operation_class}`
        .toLocaleLowerCase()
        .includes(normalized)
    );
  }, [query, view]);
  const unclassifiedCount = (view?.operations.length ?? 0) - decisions.size;

  function decide(operationId: string, decision: Decision) {
    setDecisions((current) => {
      const next = new Map(current);
      next.set(operationId, decision);
      return next;
    });
    setMessage(null);
  }

  async function save() {
    if (
      activity.current !== null
      || view === null
      || unclassifiedCount !== 0
      || view.operations.length === 0
    ) return;
    activity.current = "saving";
    setBusy("saving");
    setError(null);
    setMessage(null);
    const included = view.operations
      .filter((item) => decisions.get(item.operation_id) === "included")
      .map((item) => item.operation_id);
    const excluded = view.operations
      .filter((item) => decisions.get(item.operation_id) === "excluded")
      .map((item) => item.operation_id);
    try {
      const result = await dispatchAffordance("save_api_operation_curation", {
        source_id: sourceId,
        source_revision_id: sourceRevisionId,
        inventory_fingerprint: view.inventory_fingerprint,
        included_operation_ids: included,
        excluded_operation_ids: excluded,
        expected_current_curation_id: view.current?.id ?? null,
      });
      if (result.outcome !== "saved") {
        throw new Error(result.failure?.public_message ?? "The operation curation could not be saved.");
      }
      const next = await refresh();
      if (next === null) return;
      setMessage(
        `Saved ${next.current?.included_operation_ids.length ?? 0} included and ${next.current?.excluded_operation_ids.length ?? 0} excluded operations for this exact revision.`
      );
    } catch (caught) {
      setError(errorMessage(caught));
      await refresh().catch(() => undefined);
    } finally {
      activity.current = null;
      setBusy(null);
    }
  }

  async function refreshInventory() {
    if (activity.current !== null) return;
    activity.current = "loading";
    setBusy("loading");
    setError(null);
    setMessage(null);
    try {
      await refresh();
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      activity.current = null;
      setBusy(null);
    }
  }

  return (
    <section className="api-operation-curation" aria-labelledby="api-operation-curation-title">
      <div className="api-operation-curation-heading">
        <div>
          <p>Revision-bound design inventory</p>
          <h3 id="api-operation-curation-title">API operation curation</h3>
          <span>Include or exclude every exact discovered operation. Filtering never changes the saved selection.</span>
        </div>
        <Button
          type="button"
          variant="outline"
          disabled={busy !== null}
          onClick={() => void refreshInventory()}
        >
          <RefreshCcw data-icon="inline-start" /> Refresh inventory
        </Button>
      </div>
      {error === null ? null : <p className="sources-debug-error" role="alert">{error}</p>}
      {message === null ? null : <p className="api-curation-success" role="status">{message}</p>}
      {view === null ? (
        <p role="status">Loading discovered operations…</p>
      ) : (
        <>
          <dl className="api-curation-identity">
            <div><dt>Revision</dt><dd><code>{view.source_revision_id}</code></dd></div>
            <div><dt>Inventory</dt><dd><code>{view.inventory_fingerprint.slice(0, 12)}…</code></dd></div>
            <div><dt>Saved versions</dt><dd>{view.history.length}</dd></div>
            <div><dt>Unclassified</dt><dd>{unclassifiedCount}</dd></div>
          </dl>
          <label className="api-curation-filter" htmlFor="api-operation-filter">
            <Filter aria-hidden="true" />
            <span>Filter operations</span>
            <Input
              id="api-operation-filter"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Operation ID, method, path, or class"
            />
          </label>
          {view.operations.length === 0 ? (
            <p className="sources-empty">No discovered API operations are available to curate.</p>
          ) : (
            <ul className="api-curation-list">
              {filtered.map((item) => (
                <li key={item.operation_id} data-decision={decisions.get(item.operation_id) ?? "unclassified"}>
                  <div>
                    <strong>{item.operation_id}</strong>
                    <span>{item.method} {item.path_template}</span>
                    <small>{item.operation_class}</small>
                  </div>
                  <fieldset>
                    <legend>Availability for {item.operation_id}</legend>
                    <label>
                      <input
                        type="radio"
                        name={`curation-${item.operation_id}`}
                        checked={decisions.get(item.operation_id) === "included"}
                        onChange={() => decide(item.operation_id, "included")}
                      />
                      Include
                    </label>
                    <label>
                      <input
                        type="radio"
                        name={`curation-${item.operation_id}`}
                        checked={decisions.get(item.operation_id) === "excluded"}
                        onChange={() => decide(item.operation_id, "excluded")}
                      />
                      Exclude
                    </label>
                  </fieldset>
                </li>
              ))}
            </ul>
          )}
          <div className="api-curation-actions">
            <p>{unclassifiedCount === 0 ? "Every discovered operation is explicitly classified." : `${unclassifiedCount} operations still need an explicit decision.`}</p>
            <Button
              type="button"
              disabled={busy !== null || unclassifiedCount !== 0 || view.operations.length === 0}
              onClick={() => void save()}
            >
              {busy === "saving" ? "Saving selection…" : "Save operation selection"}
            </Button>
          </div>
        </>
      )}
    </section>
  );
}


function errorMessage(error: unknown): string {
  return error instanceof SourceClientError || error instanceof Error
    ? error.message
    : "The API operation curation is unavailable.";
}
