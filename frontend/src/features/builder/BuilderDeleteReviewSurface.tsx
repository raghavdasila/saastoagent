import { useState } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { useRouteDeckReviewActions } from "@routedeck/react";

import { Button } from "@/components/ui/button";


export function BuilderDeleteReviewSurface({ props }: RouteDeckSurfaceComponentProps) {
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
      const accepted = decision === "accept" &&
        result.disposition === "completed" && result.outcome === "removed";
      const rejected = decision === "reject" &&
        result.disposition === "failed" && result.failure?.code === "review_rejected";
      if (!accepted && !rejected) {
        setError(result.failure?.public_message ?? "Corpus could not complete the build runtime review.");
      }
    } catch {
      setError("Corpus could not complete the build runtime review.");
    } finally {
      setPending(null);
    }
  }

  return <section className="builder-delete-review" aria-labelledby={`builder-review-${review.review_id}`}>
    <h2 id={`builder-review-${review.review_id}`}>Remove this draft runtime?</h2>
    <p>This stops future Sandbox, Evaluation, and deployment work from using the selected build.</p>
    <p>The immutable build, prior Sandbox and Evaluation results, deployed runtime, and Operations lineage remain available.</p>
    <p>Review expires {new Date(review.expires_at).toLocaleString()}.</p>
    {error === null ? null : <p role="alert">{error}</p>}
    <div>
      <Button type="button" variant="destructive" disabled={pending !== null} onClick={() => void decide("accept")}>
        {pending === "accept" ? "Removing…" : "Remove draft runtime"}
      </Button>
      <Button type="button" variant="outline" disabled={pending !== null} onClick={() => void decide("reject")}>
        {pending === "reject" ? "Keeping…" : "Keep build unchanged"}
      </Button>
    </div>
  </section>;
}


function decodeReview(props: RouteDeckSurfaceComponentProps["props"]): {
  review_id: string;
  expires_at: string;
} {
  if (
    props.state !== "pending" ||
    typeof props.review_id !== "string" || props.review_id.length === 0 ||
    typeof props.expires_at !== "string" || !Number.isFinite(Date.parse(props.expires_at))
  ) {
    throw new Error("The build runtime review projection is invalid.");
  }
  return { review_id: props.review_id, expires_at: props.expires_at };
}
