import { useState, useSyncExternalStore } from "react";
import type { RouteDeckDispatchResult } from "@routedeck/core";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { useRouteDeckReviewActions } from "@routedeck/react";

import { Button } from "@/components/ui/button";
import type { ContractRevisionStore } from "./contractRevisionStore";
import { resultMessage } from "./ApiContractRevisionPanel";

export function ApiContractRevisionReviewSurface({
  props,
  store,
}: RouteDeckSurfaceComponentProps & { store: ContractRevisionStore }) {
  const snapshot = useSyncExternalStore(store.subscribe, store.snapshot);
  const actions = useRouteDeckReviewActions();
  const [pending, setPending] = useState<"accept" | "reject" | null>(null);
  if (Object.keys(props).length === 0) return null;
  const review = decodeReview(props);
  const proposal = snapshot.proposal;
  const sharedImpact = proposal?.patches.find(
    (item) => item.patch_id === "6435eb6c5861391b",
  );

  async function decide(decision: "accept" | "reject") {
    setPending(decision);
    store.clearError();
    try {
      const result = decision === "accept"
        ? await actions.accept(review.reviewId)
        : await actions.reject(review.reviewId);
      if (isSuccessfulDecision(result, decision)) {
        if (decision === "accept") store.markApproved();
        return;
      }
      store.reportError(resultMessage(
        result,
        "Corpus could not complete this contract revision review. Reload and try again.",
      ));
    } catch {
      store.reportError("Corpus could not complete this contract revision review. Reload and try again.");
    } finally {
      setPending(null);
    }
  }

  return (
    <section className="contract-revision-review" aria-labelledby={`contract-review-${review.reviewId}`}>
      <p>Explicit owner review</p>
      <h2 id={`contract-review-${review.reviewId}`}>Create this immutable API contract revision?</h2>
      {proposal === null ? (
        <p role="status">Reloading the exact persisted proposal before approval…</p>
      ) : (
        <>
          <p>The current Source remains intact. Acceptance creates a new revision from parent <code>{proposal.repaired_parent_sha256}</code>.</p>
          <p>Final canonical hash: <code>{proposal.final_canonical_sha256}</code></p>
          <div className="contract-shared-impact" role="note">
            <strong>Explicit shared-schema impact: {sharedImpact?.impact_count ?? "unavailable"}</strong>
            <p><code>BaseRegionCountry.id</code> becomes optional across two schema uses.</p>
          </div>
          <p>All {proposal.patches.length} displayed reviewed patches are included in the immutable candidate. No target API call will occur.</p>
        </>
      )}
      {snapshot.error === null ? null : <p className="sources-debug-error" role="alert">{snapshot.error}</p>}
      <p>Review expires {new Date(review.expiresAt).toLocaleString()}.</p>
      <div className="sources-form-actions">
        <Button type="button" disabled={proposal === null || pending !== null} onClick={() => void decide("accept")}>
          {pending === "accept" ? "Creating revision…" : "Accept and create new revision"}
        </Button>
        <Button type="button" variant="outline" disabled={pending !== null} onClick={() => void decide("reject")}>
          {pending === "reject" ? "Keeping current revision…" : "Keep current revision unchanged"}
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
    props.state !== "pending" ||
    typeof props.review_id !== "string" || props.review_id.length === 0 ||
    typeof props.expires_at !== "string" || !Number.isFinite(Date.parse(props.expires_at))
  ) throw new Error("The contract revision review projection is invalid.");
  return { reviewId: props.review_id, expiresAt: props.expires_at };
}

function isSuccessfulDecision(
  result: RouteDeckDispatchResult,
  decision: "accept" | "reject",
): boolean {
  if (decision === "reject") {
    return result.disposition === "failed" && result.failure?.code === "review_rejected";
  }
  return result.disposition === "completed" && result.outcome === "approved" && result.failure === null;
}
