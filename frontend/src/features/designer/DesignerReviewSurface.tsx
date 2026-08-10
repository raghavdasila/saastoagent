import { useState } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { useRouteDeckReviewActions } from "@routedeck/react";
import type { DesignerRefreshStore } from "./refreshStore";

export function DesignerReviewSurface({ props, refreshStore }: RouteDeckSurfaceComponentProps & { refreshStore: DesignerRefreshStore }) {
  const actions = useRouteDeckReviewActions();
  const [busy, setBusy] = useState(false);
  if (Object.keys(props).length === 0) return null;
  if (props.state !== "pending" || typeof props.review_id !== "string" || typeof props.expires_at !== "string") throw new Error("The Agent design review projection is invalid.");
  async function decide(decision: "accept" | "reject") {
    setBusy(true);
    try {
      const result = await (decision === "accept" ? actions.accept(props.review_id as string) : actions.reject(props.review_id as string));
      if (
        (decision === "accept" && result.disposition === "completed" && result.outcome === "accepted") ||
        (decision === "reject" && result.disposition === "failed" && result.failure?.code === "review_rejected")
      ) refreshStore.notify();
    }
    finally { setBusy(false); }
  }
  return <section className="designer-review" aria-labelledby={`designer-review-${props.review_id}`}><h2 id={`designer-review-${props.review_id}`}>Approve exact Agent design</h2><p>Approval persists this exact proposal revision. It does not build or run the Agent.</p><p>Review expires {new Date(props.expires_at).toLocaleString()}.</p><button type="button" disabled={busy} onClick={() => void decide("accept")}>Approve design</button><button type="button" disabled={busy} onClick={() => void decide("reject")}>Keep accepted design unchanged</button></section>;
}
