import { useCallback, useState } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";

import type { OwnerSessionView } from "./authClient";
import { useOwnerSession } from "./OwnerSessionContext";

type ContinuationState = "idle" | "dispatching" | "required" | "completed";

export function useAuthenticationContinuation(
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"],
) {
  const { session, loading, setSession } = useOwnerSession();
  const [state, setState] = useState<ContinuationState>("idle");

  const dispatchContinuation = useCallback(async () => {
    setState("dispatching");
    try {
      await dispatchAffordance("authentication_completed", {});
      setState("completed");
      return true;
    } catch {
      setState("required");
      return false;
    }
  }, [dispatchAffordance]);

  const authenticateAndContinue = useCallback(
    async (owner: OwnerSessionView) => {
      setSession(owner);
      return dispatchContinuation();
    },
    [dispatchContinuation, setSession],
  );

  return {
    authenticateAndContinue,
    continueToWorkspace: dispatchContinuation,
    sessionLoading: loading,
    continuationRequired:
      !loading && session !== null && state !== "completed",
    continuationCompleted: state === "completed",
    continuing: state === "dispatching",
  } as const;
}
