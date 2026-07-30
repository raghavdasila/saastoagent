import { useCallback, useState } from "react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { ArrowRight, LogIn, Sparkles, UserPlus } from "lucide-react";

import { Button } from "@/components/ui/button";

export function LoungeSurface({
  dispatchAffordance,
}: RouteDeckSurfaceComponentProps) {
  const [error, setError] = useState<Error | null>(null);
  const navigate = useCallback(
    async (affordanceId: "open_sign_in" | "open_registration") => {
      setError(null);
      try {
        await dispatchAffordance(affordanceId, {});
      } catch (caught) {
        setError(
          caught instanceof Error
            ? caught
            : new Error("The requested page could not be opened."),
        );
      }
    },
    [dispatchAffordance],
  );

  return (
    <section className="workspace-lounge" aria-labelledby="workspace-lounge-title">
      <div className="workspace-lounge-intro">
        <span className="workspace-lounge-mark" aria-hidden="true">
          <Sparkles />
        </span>
        <div>
          <h1 id="workspace-lounge-title">Explore Corpus</h1>
          <p>
            Ask about the platform and let Corpus guide the next step when you
            are ready.
          </p>
        </div>
      </div>
      <div className="workspace-lounge-actions">
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
      </div>
      {error === null ? null : <p role="alert">{error.message}</p>}
    </section>
  );
}
