import { useState } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { useRouteDeckReviewActions } from "@routedeck/react";

import { Button } from "@/components/ui/button";


export function EvaluationDeleteReviewSurface({ props }: RouteDeckSurfaceComponentProps) {
  const actions = useRouteDeckReviewActions();
  const [pending, setPending] = useState<"accept" | "reject" | null>(null);
  const [error, setError] = useState<string | null>(null);
  if (Object.keys(props).length === 0) return null;
  const review = decodeReview(props);

  async function decide(decision: "accept" | "reject") {
    setPending(decision); setError(null);
    try {
      const result = decision === "accept"
        ? await actions.accept(review.review_id)
        : await actions.reject(review.review_id);
      const accepted = decision === "accept" && result.disposition === "completed" && result.outcome === "removed";
      const rejected = decision === "reject" && result.disposition === "failed" && result.failure?.code === "review_rejected";
      if (!accepted && !rejected) setError(result.failure?.public_message ?? "Corpus could not complete the evaluation-case review.");
    } catch { setError("Corpus could not complete the evaluation-case review."); } finally { setPending(null); }
  }

  return <section className="evaluation-delete-review" aria-labelledby={`evaluation-delete-${review.review_id}`}>
    <h2 id={`evaluation-delete-${review.review_id}`}>Remove this evaluation case?</h2>
    <p>The case will no longer count toward future eligibility or be available for new runs.</p>
    <p>Prior case revisions and completed evaluation results remain attributable and visible.</p>
    <p>Review expires {new Date(review.expires_at).toLocaleString()}.</p>
    {error === null ? null : <p role="alert">{error}</p>}
    <div><Button type="button" variant="destructive" disabled={pending !== null} onClick={() => void decide("accept")}>{pending === "accept" ? "Removing..." : "Remove case"}</Button><Button type="button" variant="outline" disabled={pending !== null} onClick={() => void decide("reject")}>{pending === "reject" ? "Keeping..." : "Keep case"}</Button></div>
  </section>;
}

function decodeReview(props: RouteDeckSurfaceComponentProps["props"]): { review_id: string; expires_at: string } {
  if (props.state !== "pending" || typeof props.review_id !== "string" || typeof props.expires_at !== "string" || !Number.isFinite(Date.parse(props.expires_at))) throw new Error("The evaluation-case review projection is invalid.");
  return { review_id: props.review_id, expires_at: props.expires_at };
}
