import { useCallback, useEffect, useRef, useState } from "react";
import {
  useRouteDeckContract,
  useRouteDeckDispatch,
  useRouteDeckMutationRecovery,
  useRouteDeckNavigation,
  useRouteDeckNavigationActions,
  useRouteDeckNavigationRecovery,
  useRouteDeckSurface,
} from "@routedeck/react";
import type {
  FrontendContract,
  JsonObject,
  RouteDeckProjectedSurface,
} from "@routedeck/core";

type SelectedAgentReturn = Readonly<{
  operationId: string;
  argumentsValue: JsonObject;
}>;

export function selectedAgentReturnForBack(
  backNodeId: string | null | undefined,
  activeSurface: RouteDeckProjectedSurface | null,
  contract: FrontendContract,
): SelectedAgentReturn | null {
  if (activeSurface === null) return null;
  const affordanceId = backNodeId === "agents.home"
    ? "return_to_agent"
    : backNodeId === "builder.home"
      ? "return_to_builder"
      : null;
  if (affordanceId === null) return null;
  const agentRef = activeSurface.props.find(
    ({ name }) => name === "selected_agent_ref" || name === "return_agent_ref",
  )?.value;
  if (typeof agentRef !== "string" || agentRef.length === 0) return null;
  const surface = contract.surfaces[activeSurface.surface_id];
  if (surface === undefined || surface.component !== activeSurface.component) return null;
  const matches = (surface.affordances ?? []).filter(
    ({ id, operation }) => id === affordanceId && operation !== null,
  );
  const match = matches.length === 1 ? matches[0] : undefined;
  if (match?.operation === null || match?.operation === undefined) return null;
  return {
    operationId: match.operation.id,
    argumentsValue: Object.freeze({ agent_ref: agentRef }),
  };
}

export function CorpusNavigationControls() {
  const navigation = useRouteDeckNavigation();
  const actions = useRouteDeckNavigationActions();
  const recovery = useRouteDeckNavigationRecovery();
  const mutation = useRouteDeckMutationRecovery();
  const activeSurface = useRouteDeckSurface("active");
  const contract = useRouteDeckContract();
  const dispatch = useRouteDeckDispatch();
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
  const selectedAgentReturn = selectedAgentReturnForBack(
    navigation.back_node_id,
    activeSurface,
    contract,
  );
  const backAction = selectedAgentReturn === null
    ? actions?.back ?? null
    : () => dispatch(
        selectedAgentReturn.operationId,
        selectedAgentReturn.argumentsValue,
      ).then(() => undefined);
  const busy = recovery.pending !== null || mutation.inFlight;
  return (
    <nav aria-label="Conversation history">
      <button
        type="button"
        onClick={() => void invoke(backAction)}
        disabled={busy || !navigation.can_back || backAction === null}
      >
        Back
      </button>
      <button
        type="button"
        onClick={() => void invoke(actions?.forward ?? null)}
        disabled={busy || !navigation.can_forward || !actions?.forward}
      >
        Forward
      </button>
      <button
        type="button"
        onClick={() => void invoke(actions?.cancel ?? null)}
        disabled={busy || !navigation.can_cancel || !actions?.cancel}
      >
        Cancel
      </button>
      {failed ? <p role="alert">Corpus could not restore this view. Try again.</p> : null}
    </nav>
  );
}
