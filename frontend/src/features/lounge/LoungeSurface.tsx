import { useCallback, useState } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { ArrowRight, LogIn, Sparkles, UserPlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useOwnerSession } from "../../auth/OwnerSessionContext";
import {
  publicOperationFailureMessage,
  requireCompletedOperation,
} from "./operationResult";

export function LoungeSurface({
  dispatchAffordance,
}: RouteDeckSurfaceComponentProps) {
  const { session, loading } = useOwnerSession();
  const [error, setError] = useState<Error | null>(null);
  const navigate = useCallback(
    async (
      affordanceId:
        | "open_sign_in"
        | "open_registration"
        | "continue_to_workspace",
    ) => {
      setError(null);
      try {
        requireCompletedOperation(
          await dispatchAffordance(affordanceId, {}),
          "The requested page could not be opened.",
        );
      } catch (caught) {
        setError(new Error(publicOperationFailureMessage(
          caught,
          "The requested page could not be opened.",
        )));
      }
    },
    [dispatchAffordance],
  );
  const ownerName = session?.owner.display_name ?? session?.owner.email;

  return (
    <section className="workspace-lounge" aria-labelledby="workspace-lounge-title">
      <div className="workspace-lounge-intro">
        <span className="workspace-lounge-mark" aria-hidden="true">
          <Sparkles />
        </span>
        <div>
          <h1 id="workspace-lounge-title">
            {loading
              ? "Checking your Corpus session"
              : session === null
                ? "Explore Corpus"
                : "Return to your Workspace"}
          </h1>
          <p>
            {loading
              ? "Confirming whether this Lounge conversation has an authenticated owner."
              : session === null
                ? "Ask about the platform and let Corpus guide the next step when you are ready."
                : `${ownerName}, you are signed in to ${session.organization.name}. This Lounge conversation is preserved; continue when you are ready.`}
          </p>
        </div>
      </div>
      <div className="workspace-lounge-actions">
        {loading ? null : session === null ? (
          <>
            <Button type="button" variant="outline" onClick={() => void navigate("open_sign_in")}>
              <LogIn data-icon="inline-start" />
              Sign in
            </Button>
            <Button
              type="button"
              onClick={() => void navigate("open_registration")}
            >
              <UserPlus data-icon="inline-start" />
              Create account
              <ArrowRight data-icon="inline-end" />
            </Button>
          </>
        ) : (
          <Button
            type="button"
            onClick={() => void navigate("continue_to_workspace")}
          >
            Continue to Workspace
            <ArrowRight data-icon="inline-end" />
          </Button>
        )}
      </div>
      {error === null ? null : <p role="alert">{error.message}</p>}
    </section>
  );
}
