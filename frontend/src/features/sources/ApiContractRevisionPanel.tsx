import { useEffect, useState, useSyncExternalStore } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { ShieldCheck } from "lucide-react";

import { Button } from "@/components/ui/button";
import type { ContractRevisionStore } from "./contractRevisionStore";

export function ApiContractRevisionPanel({
  props,
  dispatchAffordance,
  store,
}: RouteDeckSurfaceComponentProps & { store: ContractRevisionStore }) {
  const snapshot = useSyncExternalStore(store.subscribe, store.snapshot);
  const [submitting, setSubmitting] = useState(false);
  const context = decodeContext(props);
  const sourceId = context?.sourceId ?? null;
  const proposalRef = context?.proposalRef ?? null;

  useEffect(() => {
    if (sourceId !== null && proposalRef !== null) {
      void store.load(sourceId, proposalRef);
    }
  }, [proposalRef, sourceId, store]);

  if (context === null) return null;
  const boundProposalRef = context.proposalRef;
  const proposal = snapshot.proposal;
  const sharedImpact = proposal?.patches.find(
    (item) => item.patch_id === "6435eb6c5861391b",
  );

  async function openReview() {
    setSubmitting(true);
    store.clearError();
    try {
      const result = await dispatchAffordance("approve_contract_revision", {
        proposal_ref: boundProposalRef,
      });
      if (!isReviewRequired(result)) {
        store.reportError(resultMessage(result, "Corpus could not stage this contract review."));
      }
    } catch {
      store.reportError("Corpus could not stage this contract review.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="contract-revision-panel" aria-labelledby="contract-proposal-title">
      <header>
        <ShieldCheck aria-hidden="true" />
        <div>
          <p>Corpus-reviewed derivative</p>
          <h2 id="contract-proposal-title">API contract revision proposal</h2>
          <span>Local Medusa {proposal?.local_medusa_version ?? "target"} evidence. This is not an official Medusa contract.</span>
        </div>
      </header>
      {snapshot.loading ? <p role="status">Loading exact proposal evidence…</p> : null}
      {snapshot.error === null ? null : <p className="sources-debug-error" role="alert">{snapshot.error}</p>}
      {proposal === null ? null : (
        <>
          <dl className="contract-hashes">
            <div><dt>Raw file</dt><dd><code>{proposal.source_raw_sha256}</code></dd></div>
            <div><dt>Raw canonical</dt><dd><code>{proposal.source_canonical_sha256}</code></dd></div>
            <div><dt>Repair manifest</dt><dd><code>{proposal.repair_manifest_sha256}</code></dd></div>
            <div><dt>Repaired parent</dt><dd><code>{proposal.repaired_parent_sha256}</code></dd></div>
            <div><dt>Proposed final</dt><dd><code>{proposal.final_canonical_sha256}</code></dd></div>
            <div><dt>Local package target</dt><dd><code>{proposal.local_package_json_sha256}</code><code>{proposal.local_package_lock_sha256}</code></dd></div>
            <div><dt>Validation evidence</dt><dd><code>{proposal.evidence_sha256}</code></dd></div>
          </dl>
          <div className="contract-shared-impact" role="note">
            <strong>Shared-schema impact: {sharedImpact?.impact_count ?? "unavailable"}</strong>
            <p><code>BaseRegionCountry.id</code> becomes optional across two schema uses. This impact must be explicitly accepted.</p>
          </div>
          <ol className="contract-patches" aria-label="Ordered reviewed patches">
            {proposal.patches.map((patch) => (
              <li key={patch.patch_id}>
                <code>{patch.patch_id}</code>
                <span>{patch.kind} · {patch.schema_pointer}{patch.field_name === null ? "" : ` · ${patch.field_name}`}</span>
                <em>evidence {patch.evidence_count} · impact {patch.impact_count}</em>
              </li>
            ))}
          </ol>
          <Button type="button" disabled={submitting || proposal.state !== "pending"} onClick={() => void openReview()}>
            {submitting ? "Opening review…" : proposal.state === "pending" ? "Review this revision" : "Revision approved"}
          </Button>
          <p className="contract-no-call">Preparing or reviewing this proposal does not call the target API.</p>
        </>
      )}
    </section>
  );
}

function decodeContext(props: RouteDeckSurfaceComponentProps["props"]): {
  sourceId: string;
  proposalRef: string;
} | null {
  if (Object.keys(props).length === 0) return null;
  if (
    typeof props.source_id !== "string" || props.source_id.length !== 16 ||
    typeof props.proposal_ref !== "string" || props.proposal_ref.length === 0
  ) throw new Error("The contract proposal context is invalid.");
  return { sourceId: props.source_id, proposalRef: props.proposal_ref };
}

function isReviewRequired(value: unknown): boolean {
  return value !== null && typeof value === "object" &&
    (value as { disposition?: unknown }).disposition === "requires_review";
}

export function resultMessage(value: unknown, fallback: string): string {
  if (value !== null && typeof value === "object") {
    const failure = (value as { failure?: unknown }).failure;
    if (failure !== null && typeof failure === "object") {
      const message = (failure as { public_message?: unknown }).public_message;
      if (typeof message === "string" && message.length > 0) return message;
    }
  }
  return fallback;
}
