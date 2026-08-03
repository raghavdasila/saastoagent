import { useCallback, useEffect, useRef, useState } from "react";
import {
  useRouteDeckNavigation,
  useRouteDeckNavigationActions,
  useRouteDeckNavigationRecovery,
} from "@routedeck/react";

export function CorpusNavigationControls() {
  const navigation = useRouteDeckNavigation();
  const actions = useRouteDeckNavigationActions();
  const recovery = useRouteDeckNavigationRecovery();
  const attempted = useRef<unknown>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (recovery.pending === null) {
      attempted.current = null;
      return;
    }
    if (attempted.current === recovery.pending || recovery.abandon === null) return;
    attempted.current = recovery.pending;
    setFailed(false);
    void (async () => {
      try {
        await recovery.abandon?.();
      } catch {
        setFailed(true);
      }
    })();
  }, [recovery]);

  const invoke = useCallback(async (action: (() => void | Promise<void>) | null) => {
    setFailed(false);
    try {
      await action?.();
    } catch {
      setFailed(true);
    }
  }, []);

  if (navigation === null) return null;
  return (
    <nav aria-label="Conversation history">
      <button
        type="button"
        onClick={() => void invoke(actions?.back ?? null)}
        disabled={recovery.pending !== null || !navigation.can_back || !actions?.back}
      >
        Back
      </button>
      <button
        type="button"
        onClick={() => void invoke(actions?.forward ?? null)}
        disabled={recovery.pending !== null || !navigation.can_forward || !actions?.forward}
      >
        Forward
      </button>
      <button
        type="button"
        onClick={() => void invoke(actions?.cancel ?? null)}
        disabled={recovery.pending !== null || !navigation.can_cancel || !actions?.cancel}
      >
        Cancel
      </button>
      {failed ? <p role="alert">Corpus could not restore this view. Try again.</p> : null}
    </nav>
  );
}
