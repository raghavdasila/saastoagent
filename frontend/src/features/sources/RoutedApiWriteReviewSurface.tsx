import { useState, useSyncExternalStore } from "react";
import type { RouteDeckDispatchResult } from "@routedeck/core";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { useRouteDeckReviewActions } from "@routedeck/react";

import { Button } from "@/components/ui/button";
import { RoutedExecutionResult } from "./ApiOperationTestPanel";
import type { RoutedExecutionStore } from "./routedExecutionStore";

export function RoutedApiWriteReviewSurface({
  props,
  store,
}: RouteDeckSurfaceComponentProps & { store: RoutedExecutionStore }) {
  const snapshot = useSyncExternalStore(store.subscribe, store.snapshot);
  const actions = useRouteDeckReviewActions();
  const [pending, setPending] = useState<"accept" | "reject" | null>(null);
  if (Object.keys(props).length === 0) return null;
  const review = decodeReview(props);
  const plan = snapshot.context?.plan ?? null;
  const step = plan?.steps.length === 1 ? plan.steps[0] : null;
  const exactWrite = plan?.state === "ready" && step?.http_safety === "write"
    && step.selected_operation_id !== null;

  async function decide(decision: "accept" | "reject") {
    setPending(decision);
    store.clearError();
    try {
      const result = decision === "accept"
        ? await actions.accept(review.reviewId)
        : await actions.reject(review.reviewId);
      if (decision === "reject" && isRejected(result)) return;
      if (decision === "accept") {
        await store.refresh();
        if (isTerminalAccept(result) && store.snapshot().result !== null) return;
      }
      store.reportError(
        result.failure?.public_message
          ?? "Corpus could not complete this routed API write review. Reload and verify the exact plan.",
      );
    } catch {
      await store.refresh().catch(() => undefined);
      store.reportError(
        "Corpus could not complete this routed API write review. Reload and verify the exact plan.",
      );
    } finally {
      setPending(null);
    }
  }

  return (
    <section className="routed-api-write-review" aria-labelledby={`routed-write-review-${review.reviewId}`}>
      <p>Explicit owner review · one external write</p>
      <h2 id={`routed-write-review-${review.reviewId}`}>Send this routed API write?</h2>
      {!exactWrite || step === null || plan === null ? (
        <p role="status">Reloading the exact current write plan before review…</p>
      ) : (
        <>
          <p><strong>{step.selected_operation_id}</strong> is the only selected operation.</p>
          <p><code>{step.method} {step.path_template}</code> from plan <code>{plan.plan_id}</code>.</p>
          <p role="note">Acceptance makes exactly one attempt. Corpus will not retry automatically.</p>
        </>
      )}
      {snapshot.error === null ? null : <p className="sources-debug-error" role="alert">{snapshot.error}</p>}
      {snapshot.result === null ? null : <RoutedExecutionResult result={snapshot.result} />}
      <p>Review expires {new Date(review.expiresAt).toLocaleString()}.</p>
      <div className="sources-form-actions">
        <Button
          type="button"
          disabled={!exactWrite || pending !== null || snapshot.result !== null}
          onClick={() => void decide("accept")}
        >
          {pending === "accept" ? "Sending one write…" : "Accept and send one write"}
        </Button>
        <Button
          type="button"
          variant="outline"
          disabled={pending !== null || snapshot.result !== null}
          onClick={() => void decide("reject")}
        >
          {pending === "reject" ? "Rejecting write…" : "Reject without sending"}
        </Button>
      </div>
    </section>
  );
}

function decodeReview(props: RouteDeckSurfaceComponentProps["props"]): {
  reviewId: string;
  expiresAt: string;
} {
  if (
    props.state !== "pending"
    || typeof props.review_id !== "string" || props.review_id.length === 0
    || typeof props.expires_at !== "string" || !Number.isFinite(Date.parse(props.expires_at))
  ) throw new Error("The routed API write review projection is invalid.");
  return { reviewId: props.review_id, expiresAt: props.expires_at };
}

function isRejected(result: RouteDeckDispatchResult): boolean {
  return result.disposition === "failed" && result.failure?.code === "review_rejected";
}

function isTerminalAccept(result: RouteDeckDispatchResult): boolean {
  return (result.disposition === "completed" && result.outcome === "observed" && result.failure === null)
    || (result.disposition === "external_outcome_unknown"
      && result.failure?.code === "external_outcome_unknown");
}
