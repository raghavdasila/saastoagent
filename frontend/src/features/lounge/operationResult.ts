import type { RouteDeckDispatchResult } from "@routedeck/core";

class CorpusOperationFailure extends Error {}

export function requireCompletedOperation(
  result: RouteDeckDispatchResult,
  fallback: string,
): RouteDeckDispatchResult {
  if (result.disposition === "completed") return result;
  throw new CorpusOperationFailure(result.failure?.public_message ?? fallback);
}

export function publicOperationFailureMessage(
  error: unknown,
  fallback: string,
): string {
  return error instanceof CorpusOperationFailure ? error.message : fallback;
}
