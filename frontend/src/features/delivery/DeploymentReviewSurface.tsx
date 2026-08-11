import { useState } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { useRouteDeckReviewActions } from "@routedeck/react";


export type HostedAgentReviewKind = "deploy" | "retry" | "rollback" | "availability";

export function DeploymentReviewSurface({ props, kind }: RouteDeckSurfaceComponentProps & { kind: HostedAgentReviewKind }) {
  const actions = useRouteDeckReviewActions();
  const [busy, setBusy] = useState(false);
  if (Object.keys(props).length === 0) return null;
  if (props.state !== "pending" || typeof props.review_id !== "string" || typeof props.expires_at !== "string") throw new Error("The deployment review projection is invalid.");
  async function decide(decision: "accept" | "reject") {
    setBusy(true);
    try {
      await (decision === "accept" ? actions.accept(props.review_id as string) : actions.reject(props.review_id as string));
      window.dispatchEvent(new Event("corpus:channels-refresh"));
    } finally { setBusy(false); }
  }
  const copy = hostedAgentReviewCopy(kind);
  return <section className="deployment-review" aria-labelledby={`deployment-review-${props.review_id}`}><h2 id={`deployment-review-${props.review_id}`}>{copy.heading}</h2><p>{copy.consequence}</p><p>Review expires {new Date(props.expires_at).toLocaleString()}.</p><button type="button" disabled={busy} onClick={() => void decide("accept")}>{copy.accept}</button><button type="button" disabled={busy} onClick={() => void decide("reject")}>{copy.reject}</button></section>;
}

export function hostedAgentReviewCopy(kind: HostedAgentReviewKind) {
  if (kind === "deploy") return {
    heading: "Approve hosted Agent deployment",
    consequence: "Approval activates the exact reviewed eligible build on this public channel. Rejection leaves the current deployment unchanged.",
    accept: "Deploy reviewed build", reject: "Keep current deployment",
  } as const;
  if (kind === "rollback") return {
    heading: "Approve hosted Agent rollback",
    consequence: "Approval activates the exact reviewed earlier deployment on this public channel. Rejection leaves the current deployment unchanged.",
    accept: "Roll back to reviewed deployment", reject: "Keep current deployment",
  } as const;
  if (kind === "retry") return {
    heading: "Approve a new deployment attempt",
    consequence: "Approval queues one new attempt linked to the exact failed deployment. It does not reuse or rewrite the failed attempt and Corpus will not retry automatically.",
    accept: "Queue reviewed retry", reject: "Keep failed deployment",
  } as const;
  return {
    heading: "Approve hosted Web availability change",
    consequence: "Approval applies the exact reviewed enable or disable choice. Rejection leaves the channel availability unchanged.",
    accept: "Apply availability change", reject: "Keep current availability",
  } as const;
}
