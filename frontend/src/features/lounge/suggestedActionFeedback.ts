import type { RouteDeckDispatchResult } from "@routedeck/core";

export function resolveLoungeSuggestedActionFeedback(
  result: RouteDeckDispatchResult,
): string | null {
  if (
    result.disposition === "completed"
    && result.operation_id === "lounge.request_verification_delivery"
  ) {
    return "The verification email request was accepted. Delivery and verification are not yet confirmed.";
  }
  return null;
}
