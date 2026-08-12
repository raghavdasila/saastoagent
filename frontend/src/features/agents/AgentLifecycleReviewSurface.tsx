import { useMemo, useState, useSyncExternalStore } from "react";
import type { RouteDeckDispatchResult } from "@routedeck/core";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { useRouteDeckReviewActions } from "@routedeck/react";

import type { AgentStore } from "./store";

export function AgentLifecycleReviewSurface({
  props,
  surface,
  store,
}: RouteDeckSurfaceComponentProps & { store: AgentStore }) {
  const snapshot = useSyncExternalStore(store.subscribe, store.snapshot);
  const selected = useMemo(
    () => snapshot.agents.find((agent) => agent.id === snapshot.selectedId) ?? null,
    [snapshot.agents, snapshot.selectedId],
  );
  const actions = useRouteDeckReviewActions();
  const [pending, setPending] = useState<"accept" | "reject" | null>(null);
  if (Object.keys(props).length === 0) return null;
  const review = decodeReview(props);
  const action = lifecycleReviewAction(surface.surface_id);

  async function decide(decision: "accept" | "reject") {
    setPending(decision);
    store.clearError();
    const selectedId = selected?.id ?? null;
    if (decision === "accept") store.clearSelection();
    try {
      const result = decision === "accept"
        ? await actions.accept(review.review_id)
        : await actions.reject(review.review_id);
      if (isSuccessfulDecision(result, decision, action)) {
        await store.refresh();
        const selectedId = store.snapshot().selectedId;
        if (
          decision === "reject" &&
          selectedId !== null &&
          store.snapshot().error === null
        ) {
          await store.refreshDependencies(selectedId);
        }
        return;
      }
      if (decision === "accept" && selected !== null) {
        await store.refresh();
        store.select(selected.id);
        await store.refreshDependencies(selected.id);
      }
      store.reportError(
        result.failure?.public_message ??
          "Corpus could not complete the Agent lifecycle review. Reload and try again.",
      );
    } catch {
      if (decision === "accept" && selectedId !== null) {
        await store.refresh().catch(() => undefined);
        store.select(selectedId);
        await store.refreshDependencies(selectedId).catch(() => undefined);
      }
      store.reportError(
        "Corpus could not complete the Agent lifecycle review. Reload and try again.",
      );
    } finally {
      setPending(null);
    }
  }

  return (
    <section
      className="agent-lifecycle-review"
      aria-labelledby={`review-${review.review_id}`}
    >
      <h2 id={`review-${review.review_id}`}>
        {action === "archive" ? "Confirm archive" : "Confirm permanent deletion"}
      </h2>
      {selected === null ? (
        <p role="status">Reload the exact selected Agent before confirming this action.</p>
      ) : (
        <>
          <p><strong>{selected.name}</strong> is the exact selected active Agent.</p>
          {action === "archive" ? (
            <p>Archive removes this Agent from the active inventory while preserving its record, configuration history, Source attachments, and immutable references.</p>
          ) : (
            <p>Permanent deletion is irreversible. It proceeds only when the refreshed dependency guard remains clear and never detaches or cascades through dependencies.</p>
          )}
          <p>
            Current Source attachments: {snapshot.dependencies?.source_attachments.length ?? "checking"}.
          </p>
        </>
      )}
      <p>Review expires {new Date(review.expires_at).toLocaleString()}.</p>
      <div>
        <button
          type="button"
          disabled={selected === null || snapshot.dependencies === null || pending !== null}
          onClick={() => void decide("accept")}
        >
          {pending === "accept"
            ? "Accepting…"
            : action === "archive"
              ? "Archive Agent"
              : "Delete Agent permanently"}
        </button>
        <button
          type="button"
          disabled={pending !== null}
          onClick={() => void decide("reject")}
        >
          {pending === "reject" ? "Rejecting…" : "Keep Agent unchanged"}
        </button>
      </div>
    </section>
  );
}

function isSuccessfulDecision(
  result: RouteDeckDispatchResult,
  decision: "accept" | "reject",
  action: "archive" | "delete",
): boolean {
  if (decision === "reject") {
    return result.disposition === "failed" && result.failure?.code === "review_rejected";
  }
  return result.disposition === "completed" &&
    result.failure === null &&
    result.outcome === (action === "archive" ? "archived" : "deleted");
}

function lifecycleReviewAction(surfaceId: string): "archive" | "delete" {
  if (surfaceId === "agents.archive_review") return "archive";
  if (surfaceId === "agents.delete_review") return "delete";
  throw new Error("The Agent lifecycle review surface is unavailable.");
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
    throw new Error("The Agent lifecycle review projection is invalid.");
  }
  return { review_id: props.review_id, expires_at: props.expires_at };
}
