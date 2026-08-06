import { useCallback, useState } from "react";
import type {
  RouteDeckDispatchResult,
  RouteDeckProjectedSuggestedAction,
} from "@routedeck/core";
import {
  useRouteDeckDispatch,
  useRouteDeckMutationRecovery,
  useRouteDeckProjection,
} from "@routedeck/react";

import { resolveCorpusSuggestedActionFeedback } from "../routedeck/suggestedActionFeedback";

const GENERIC_ACTION_FAILURE = "Corpus could not complete that action. Try again.";

type Feedback = Readonly<{ kind: "alert" | "status"; message: string }>;

export function CorpusSuggestedActions({ disabled = false }: { disabled?: boolean }) {
  const projection = useRouteDeckProjection();
  const dispatch = useRouteDeckDispatch();
  const mutation = useRouteDeckMutationRecovery();
  const [pendingActionId, setPendingActionId] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<Feedback | null>(null);
  const actions = projection?.suggested_actions ?? [];
  const interactionBusy = projection?.interaction.phase === "active";

  const activate = useCallback(async (action: RouteDeckProjectedSuggestedAction) => {
    setPendingActionId(action.action_id);
    setFeedback(null);
    try {
      const result = await dispatch(action.operation_id, action.arguments);
      setFeedback(feedbackFor(result));
    } catch {
      setFeedback({ kind: "alert", message: GENERIC_ACTION_FAILURE });
    } finally {
      setPendingActionId(null);
    }
  }, [dispatch]);

  if (actions.length === 0) return null;

  return (
    <div
      aria-label="Suggested actions"
      aria-busy={mutation.inFlight || interactionBusy}
      data-routedeck-suggested-actions=""
    >
      <div role="group">
        {actions.map((action) => (
          <button
            key={action.action_id}
            type="button"
            disabled={disabled || mutation.inFlight || interactionBusy}
            data-routedeck-suggested-action={action.action_id}
            onClick={() => void activate(action)}
          >
            {pendingActionId === action.action_id ? `${action.label}…` : action.label}
          </button>
        ))}
      </div>
      {feedback === null ? null : (
        <p role={feedback.kind}>{feedback.message}</p>
      )}
    </div>
  );
}

function feedbackFor(result: RouteDeckDispatchResult): Feedback | null {
  if (result.disposition === "completed") {
    const message = resolveCorpusSuggestedActionFeedback(result);
    return message === null ? null : { kind: "status", message };
  }
  if (
    result.disposition === "needs_input"
    || result.disposition === "requires_review"
    || result.disposition === "pending"
  ) {
    return null;
  }
  return {
    kind: "alert",
    message: result.failure?.public_message || GENERIC_ACTION_FAILURE,
  };
}
