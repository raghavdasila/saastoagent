import { useCallback, useState } from "react";
import type {
  RouteDeckBootstrapActionRequiredState,
  RouteDeckBootstrapDisposedState,
  RouteDeckBootstrapRecoveryAction,
  RouteDeckBootstrapRecoveryActionKind,
} from "@routedeck/react";

import { Button } from "@/components/ui/button";
import { ownerAuthClient } from "../features/workspace/authClient";

export interface BootstrapRecoveryShellProps {
  state:
    | RouteDeckBootstrapActionRequiredState
    | RouteDeckBootstrapDisposedState;
}

export function BootstrapRecoveryShell({
  state,
}: BootstrapRecoveryShellProps) {
  const [localBusy, setLocalBusy] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const reason = state.phase === "recovery" ? state.reason : "disposed";
  const busy = state.busy || localBusy;
  const action = (kind: RouteDeckBootstrapRecoveryActionKind) =>
    state.actions.find((candidate) => candidate.kind === kind) ?? null;

  const run = useCallback(
    async (recoveryAction: RouteDeckBootstrapRecoveryAction) => {
      setLocalBusy(true);
      setLocalError(null);
      try {
        if (recoveryAction.kind === "start_new_session") {
          await ownerAuthClient.recover();
        }
        await recoveryAction.run();
      } catch (caught) {
        setLocalError(
          caught instanceof Error ? caught.message : "Session recovery failed.",
        );
      } finally {
        setLocalBusy(false);
      }
    },
    [],
  );

  return (
    <section className="bootstrap-error" role="alert">
      <h1>{recoveryTitle(reason)}</h1>
      <p>
        {localError ?? state.error?.message ?? recoveryMessage(reason)}
      </p>
      {reason === "session_create" ? (
        <p>
          Session creation may already have completed. Retry preserves the
          original recovery request.
        </p>
      ) : null}
      {reason === "navigation" ? (
        <p>
          The requested page may already be open. Retry that navigation or use
          the authoritative current session.
        </p>
      ) : null}
      <div>
        <RecoveryButton
          action={action("retry_session_create")}
          disabled={busy}
          onRun={run}
        >
          Retry creating this session
        </RecoveryButton>
        <RecoveryButton
          action={action("retry_navigation")}
          disabled={busy}
          onRun={run}
        >
          Retry opening this page
        </RecoveryButton>
        <RecoveryButton
          action={action("abandon_navigation")}
          disabled={busy}
          onRun={run}
        >
          Use current session
        </RecoveryButton>
        <RecoveryButton
          action={action("resync")}
          disabled={busy}
          onRun={run}
        >
          Reconnect session
        </RecoveryButton>
        <RecoveryButton
          action={action("start_new_session")}
          disabled={busy}
          onRun={run}
          variant="outline"
        >
          Start a new session
        </RecoveryButton>
      </div>
    </section>
  );
}

function RecoveryButton({
  action,
  disabled,
  onRun,
  children,
  variant,
}: {
  action: RouteDeckBootstrapRecoveryAction | null;
  disabled: boolean;
  onRun(action: RouteDeckBootstrapRecoveryAction): Promise<void>;
  children: string;
  variant?: "outline";
}) {
  if (action === null) return null;
  return (
    <Button
      type="button"
      variant={variant}
      disabled={disabled}
      onClick={() => void onRun(action)}
    >
      {children}
    </Button>
  );
}

function recoveryTitle(reason: string): string {
  switch (reason) {
    case "resume_expired":
      return "Application session expired";
    case "resume_missing":
      return "Application session unavailable";
    case "resume_contract_mismatch":
      return "Application session contract changed";
    case "disposed":
      return "Application session closed";
    default:
      return "Application session recovery";
  }
}

function recoveryMessage(reason: string): string {
  switch (reason) {
    case "resume_expired":
      return "The saved session has expired. Start a new session explicitly to continue.";
    case "resume_missing":
      return "The saved session is no longer available. Start a new session explicitly to continue.";
    case "resume_contract_mismatch":
      return "The application contract changed. Start a new session explicitly to continue.";
    case "disposed":
      return "This RouteDeck store has been disposed and cannot recover.";
    default:
      return "The RouteDeck session did not finish starting.";
  }
}
