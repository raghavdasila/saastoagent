import type { SourceRevision } from "./contracts";

const CANONICAL_SHA256 = /^[0-9a-f]{64}$/;

export function isReviewedApiRevision(revision: SourceRevision): boolean {
  return revision.state === "ready"
    && revision.summary.revision_kind === "reviewed_api_contract"
    && reviewedApiDocumentHash(revision) !== null;
}

export function reviewedApiDocumentHash(revision: SourceRevision): string | null {
  const value = revision.summary.final_canonical_sha256;
  return typeof value === "string" && CANONICAL_SHA256.test(value) ? value : null;
}
