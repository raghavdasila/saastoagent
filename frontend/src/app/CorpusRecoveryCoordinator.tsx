import { useCallback, useEffect, useRef, useState } from "react";
import type {
  RouteDeckBootstrapActionRequiredState,
  RouteDeckBootstrapDisposedState,
  RouteDeckBootstrapRecoveryActionKind,
} from "@routedeck/react";

import { Button } from "@/components/ui/button";
import { BootstrapLoadingShell } from "./BootstrapLoadingShell";

type RecoveryState =
  | RouteDeckBootstrapActionRequiredState
  | RouteDeckBootstrapDisposedState;

export function CorpusRecoveryCoordinator({
  state,
  replaceConversation,
}: {
  state: RecoveryState;
  replaceConversation(): Promise<void>;
}) {
  const attempted = useRef(false);
  const [failed, setFailed] = useState(false);

  const recover = useCallback(async () => {
    setFailed(false);
    try {
      if (state.phase === "disposed") throw new Error("disposed");
      switch (state.reason) {
        case "navigation":
          await requireAction(state, "abandon_navigation").run();
          return;
        case "resync":
          await requireAction(state, "resync").run();
          return;
        case "resume_expired":
        case "resume_missing":
        case "resume_contract_mismatch":
          await replaceConversation();
          return;
        default:
          throw new Error("unrecoverable");
      }
    } catch {
      setFailed(true);
    }
  }, [replaceConversation, state]);

  useEffect(() => {
    if (attempted.current) return;
    attempted.current = true;
    void recover();
  }, [recover]);

  if (!failed) return <BootstrapLoadingShell message="Loading Corpus…" />;
  return (
    <section className="bootstrap-error" role="alert">
      <h1>Corpus is temporarily unavailable</h1>
      <p>Corpus could not restore this view.</p>
      <Button type="button" onClick={() => void recover()}>
        Try again
      </Button>
    </section>
  );
}

function requireAction(
  state: RouteDeckBootstrapActionRequiredState,
  kind: RouteDeckBootstrapRecoveryActionKind,
) {
  const action = state.actions.find((candidate) => candidate.kind === kind);
  if (action === undefined) throw new Error("recovery action unavailable");
  return action;
}
