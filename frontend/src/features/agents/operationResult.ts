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
