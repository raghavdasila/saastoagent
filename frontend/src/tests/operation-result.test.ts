import type { RouteDeckDispatchResult } from "@routedeck/core";
import { describe, expect, it } from "vitest";

import { stagedReview } from "../features/agents/operationResult";

describe("RouteDeck review staging", () => {
  it("accepts only the exact required-review projection", () => {
    const result = reviewResult("deployment.deploy");
    expect(stagedReview(result, "deployment.deploy")).toBeNull();
    expect(stagedReview(result, "deployment.rollback"))
      .toBe("Corpus could not prepare the required review. Reload and try again.");
  });

  it("does not report required review as a failed completed operation", () => {
    const result = reviewResult("channels.set_enabled");
    expect(stagedReview(result, "channels.set_enabled")).toBeNull();
  });
});

function reviewResult(operationId: string): RouteDeckDispatchResult {
  return {
    disposition: "requires_review",
    operation_id: operationId,
    request_id: "review-request",
    session_version: 3,
    projection_version: 3,
    evidence: {
      source: "surface",
      phases: ["received", "review_staged"],
      attempt_id: "review-attempt",
      request_fingerprint: "review-request-fingerprint",
      delivery_phase: "not_sent",
      result_id: null,
      result_fingerprint: null,
    },
    review: {
      id: "review-exact",
      expires_at: "2026-08-12T00:00:00Z",
    },
    outcome: null,
    failure: null,
  };
}
