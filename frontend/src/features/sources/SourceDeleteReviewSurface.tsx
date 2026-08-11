import { useEffect, useState, useSyncExternalStore } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { useRouteDeckReviewActions } from "@routedeck/react";

import { Button } from "@/components/ui/button";
import type { SourceLifecycleStore } from "./sourceLifecycleStore";

export function SourceDeleteReviewSurface({
  props,
  store,
}: RouteDeckSurfaceComponentProps & { store: SourceLifecycleStore }) {
  const snapshot = useSyncExternalStore(store.subscribe, store.snapshot);
  const actions = useRouteDeckReviewActions();
  const [pending, setPending] = useState<"accept" | "reject" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const selected = snapshot.selected;
  const dependencies = snapshot.dependencies;

  useEffect(() => {
    if (Object.keys(props).length === 0 || selected === null || dependencies !== null) return;
    void store.refreshDependencies(selected.source_id).catch((caught) => {
      setError(caught instanceof Error ? caught.message : "Source dependencies are unavailable.");
    });
  }, [dependencies, props, selected, store]);

  if (Object.keys(props).length === 0) return null;
  const review = decodeReview(props);

  async function decide(decision: "accept" | "reject") {
    setPending(decision);
    setError(null);
    try {
      const result = decision === "accept"
        ? await actions.accept(review.review_id)
        : await actions.reject(review.review_id);
      if (decision === "reject") {
        if (result.failure?.code !== "review_rejected") {
          throw new Error(result.failure?.public_message ?? "Deletion review could not be rejected.");
        }
        if (selected !== null) await store.refreshDependencies(selected.source_id);
        return;
      }
      if (result.disposition === "completed" && result.outcome === "deleted") {
        store.clear();
        return;
      }
      if (selected !== null) await store.refreshDependencies(selected.source_id);
      throw new Error(
        result.failure?.public_message ??
          "Corpus could not delete this API source. It remains unchanged.",
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Corpus could not complete the deletion review.");
    } finally {
      setPending(null);
    }
  }

  return (
    <section className="source-delete-review" aria-labelledby={`source-delete-${review.review_id}`}>
      <h2 id={`source-delete-${review.review_id}`}>Confirm permanent Source deletion</h2>
      {selected === null || dependencies === null ? (
        <p role="status">Reload the exact selected API source and its dependencies before confirming.</p>
      ) : (
        <>
          <p><strong>{selected.display_name}</strong> is the exact selected API source.</p>
          <p>Permanent deletion is irreversible and never detaches or cascades through dependencies.</p>
          <ul>
            <li>Processing: {dependencies.processing_state}</li>
            <li>Agent attachments: {dependencies.attached_agent_ids.length}</li>
            <li>Saved design revisions: {dependencies.design_revision_ids.length}</li>
            <li>Immutable builds: {dependencies.build_ids.length}</li>
          </ul>
        </>
      )}
      <p>Review expires {new Date(review.expires_at).toLocaleString()}.</p>
      {error === null ? null : <p role="alert">{error}</p>}
      <div>
        <Button
          type="button"
          variant="destructive"
          disabled={selected === null || dependencies === null || dependencies.blocks_delete || pending !== null}
          onClick={() => void decide("accept")}
        >
          {pending === "accept" ? "Deleting…" : "Delete API source permanently"}
        </Button>
        <Button type="button" variant="outline" disabled={pending !== null} onClick={() => void decide("reject")}>
          {pending === "reject" ? "Keeping…" : "Keep API source unchanged"}
        </Button>
      </div>
    </section>
  );
}

function decodeReview(props: RouteDeckSurfaceComponentProps["props"]): {
  review_id: string;
  expires_at: string;
} {
  if (
    props.state !== "pending" ||
    typeof props.review_id !== "string" ||
    props.review_id.length === 0 ||
    typeof props.expires_at !== "string" ||
    !Number.isFinite(Date.parse(props.expires_at))
  ) {
    throw new Error("The Source deletion review projection is invalid.");
  }
  return { review_id: props.review_id, expires_at: props.expires_at };
}
