import type { RouteDeckDispatchResult } from "@routedeck/core";

export function completedOutcome(
  result: RouteDeckDispatchResult,
  expectedOutcome: string,
): string | null {
  if (
    result.disposition === "completed" &&
    result.failure === null &&
    result.outcome === expectedOutcome
  ) {
    return null;
  }
  return (
    result.failure?.public_message ??
    "Corpus could not complete the agent action. Reload and try again."
  );
}

export function stagedReview(
  result: RouteDeckDispatchResult,
  expectedOperationId: string,
): string | null {
  if (
    result.disposition === "requires_review" &&
    result.operation_id === expectedOperationId &&
    result.failure === null &&
    result.review !== null &&
    result.review !== undefined &&
    result.review.id !== ""
  ) {
    return null;
  }
  return (
    result.failure?.public_message ??
    "Corpus could not prepare the required review. Reload and try again."
  );
}
