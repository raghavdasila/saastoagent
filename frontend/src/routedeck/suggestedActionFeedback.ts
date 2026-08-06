import type { RouteDeckDispatchResult } from "@routedeck/core";

import { resolveLoungeSuggestedActionFeedback } from "../features/lounge/suggestedActionFeedback";

export function resolveCorpusSuggestedActionFeedback(
  result: RouteDeckDispatchResult,
): string | null {
  return resolveLoungeSuggestedActionFeedback(result);
}
