import React, { useCallback, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  createRouteDeckAgentClient,
  isRouteDeckConversationSessionRecoveryError,
  type AgentHistoryTurn,
  type AssistantInitiatedTurnProgress,
  type RouteDeckAgentClient,
} from "@routedeck/core";
import { RouteDeckBootstrapBoundary } from "@routedeck/react";

import { ApplicationShell } from "./app/ApplicationShell";
import { BootstrapLoadingShell } from "./app/BootstrapLoadingShell";
import { BootstrapRecoveryShell } from "./app/BootstrapRecoveryShell";
import {
  markInitialSessionHealthy,
  recoverInitialSession,
} from "./app/sessionRecovery";
import type { AppRouteDeck } from "./app/createRouteDeck";
import {
  captureAuthTokenFragment,
} from "./features/lounge/tokenFragment";
import {
  createGreetingRetryRequestId,
  type InitialConversationPhase,
  loadInitialConversation,
  shouldStartEntryGreeting,
} from "./app/initialConversation";
import { loadRouteDeck } from "./app/loadRouteDeck";
import { CorpusHeader } from "./features/workspace/CorpusHeader";
import { WorkspaceHeading } from "./features/workspace/WorkspaceHeading";
import { WorkspaceNavigation } from "./features/workspace/WorkspaceNavigation";
import { ownerAuthClient } from "./features/lounge/authClient";
import { corpusSurfaceRegistry } from "./routedeck/surfaces";
import "./styles.css";
import "./features/workspace/workspace.css";
import "./features/sources/sources.css";

const INITIAL_GREETING_REQUEST_ID = "corpus.lounge-greeting.v1";

const rootElement = document.getElementById("root");
if (rootElement === null) {
  throw new Error("Corpus requires a #root element.");
}
const root = createRoot(rootElement);
captureAuthTokenFragment(window);
root.render(<BootstrapLoadingShell />);
void start();

async function start(): Promise<void> {
  let routeDeck: AppRouteDeck;
  try {
    routeDeck = await loadRouteDeck(window);
  } catch (error) {
    root.render(
      <FatalShell
        title="Corpus could not load"
        error={error}
        fallback="The RouteDeck contract could not be loaded."
      />,
    );
    return;
  }
  window.addEventListener("pagehide", () => routeDeck.store.dispose(), { once: true });
  const chatClient = createRouteDeckAgentClient();

  root.render(
    <React.StrictMode>
      <CorpusApplicationRoot routeDeck={routeDeck} chatClient={chatClient} />
    </React.StrictMode>,
  );
}

function CorpusApplicationRoot({
  routeDeck,
  chatClient,
}: {
  routeDeck: AppRouteDeck;
  chatClient: RouteDeckAgentClient;
}) {
  return (
    <RouteDeckBootstrapBoundary
      store={routeDeck.store}
      loading={<BootstrapLoadingShell />}
      recovery={(state) => <BootstrapRecoveryShell state={state} />}
    >
      <InitialConversationGate routeDeck={routeDeck} chatClient={chatClient} />
    </RouteDeckBootstrapBoundary>
  );
}

function InitialConversationGate({
  routeDeck,
  chatClient,
}: {
  routeDeck: AppRouteDeck;
  chatClient: RouteDeckAgentClient;
}) {
  const [attempt, setAttempt] = useState<ConversationAttempt>({
    sequence: 0,
    requestId: INITIAL_GREETING_REQUEST_ID,
  });
  const [result, setResult] = useState<ConversationLoadState>(() => ({
    phase: "loading",
    greetingPending: shouldStartGreeting(routeDeck),
    progress: null,
    bootstrapPhase: "loading_history",
  }));
  const retained = useRef<RetainedConversationLoad | null>(null);

  useEffect(() => {
    let active = true;
    const greetingPending = shouldStartGreeting(routeDeck);
    setResult({ phase: "loading", greetingPending, progress: null, bootstrapPhase: "loading_history" });
    let load = retained.current;
    if (load === null || load.sequence !== attempt.sequence) {
      load = {
        sequence: attempt.sequence,
        promise: restoreInitialConversation(
          routeDeck,
          chatClient,
          attempt.requestId,
          greetingPending,
          (progress) => {
            setResult((current) =>
              current.phase === "loading"
                ? { ...current, progress }
                : current,
            );
          },
          (bootstrapPhase) => {
            setResult((current) =>
              current.phase === "loading"
                ? { ...current, bootstrapPhase }
                : current,
            );
          },
        ),
      };
      retained.current = load;
    }
    void load.promise.then(
      (conversation) => {
        if (active) {
          markInitialSessionHealthy(window.sessionStorage);
          setResult({ phase: "ready", conversation });
        }
      },
      (error: unknown) => {
        if (!active) return;
        setResult({ phase: "recovering" });
        void recoverInitialSession(
          window.sessionStorage,
          () => ownerAuthClient.recover(),
          () => window.location.replace("/"),
        ).then(
          (started) => {
            if (!started && active) setResult({ phase: "error", error });
          },
          (recoveryError: unknown) => {
            if (active) setResult({ phase: "error", error: recoveryError });
          },
        );
      },
    );
    return () => {
      active = false;
    };
  }, [attempt, chatClient, routeDeck]);

  const retry = useCallback(() => {
    setAttempt((current) => ({
      sequence: current.sequence + 1,
      requestId: createGreetingRetryRequestId(INITIAL_GREETING_REQUEST_ID),
    }));
  }, []);

  if (result.phase === "error") {
    return (
      <FatalShell
        title="Corpus conversation could not load"
        error={result.error}
        fallback="The saved conversation could not be restored."
        retry={retry}
      />
    );
  }
  if (result.phase === "recovering") {
    return (
      <BootstrapLoadingShell
        title="Recovering session"
        message="Clearing the stale session and reopening the Lounge."
      />
    );
  }

  const conversation = result.phase === "ready" ? result.conversation : [];
  const conversationBootstrapPending =
    result.phase === "loading" && result.greetingPending;
  const conversationBootstrapProgress =
    result.phase === "loading" ? result.progress : null;
  const conversationBootstrapPhase =
    result.phase === "loading" ? result.bootstrapPhase : null;
  return (
    <ApplicationShell
      routeDeck={routeDeck}
      registry={corpusSurfaceRegistry}
      chatClient={chatClient}
      initialConversation={conversation}
      conversationBootstrapPending={conversationBootstrapPending}
      conversationBootstrapProgress={conversationBootstrapProgress}
      conversationBootstrapPhase={conversationBootstrapPhase}
      header={<CorpusHeader />}
      navigation={<WorkspaceNavigation />}
      mainHeader={<WorkspaceHeading />}
    />
  );
}

async function restoreInitialConversation(
  routeDeck: AppRouteDeck,
  chatClient: RouteDeckAgentClient,
  requestId: string,
  startGreeting: boolean,
  onProgress: (progress: AssistantInitiatedTurnProgress) => void,
  onPhase: (phase: InitialConversationPhase) => void,
): Promise<readonly AgentHistoryTurn[]> {
  try {
    return await loadConversation(
      routeDeck,
      chatClient,
      requestId,
      startGreeting,
      onProgress,
      onPhase,
    );
  } catch (error) {
    if (!isRouteDeckConversationSessionRecoveryError(error)) throw error;
    await routeDeck.store.resync();
    return loadConversation(
      routeDeck,
      chatClient,
      requestId,
      startGreeting,
      onProgress,
      onPhase,
    );
  }
}

function loadConversation(
  routeDeck: AppRouteDeck,
  chatClient: RouteDeckAgentClient,
  requestId: string,
  startGreeting: boolean,
  onProgress: (progress: AssistantInitiatedTurnProgress) => void,
  onPhase: (phase: InitialConversationPhase) => void,
) {
  return loadInitialConversation(routeDeck, chatClient, requestId, {
    startGreeting,
    onProgress,
    onPhase,
  });
}

function shouldStartGreeting(routeDeck: AppRouteDeck): boolean {
  return shouldStartEntryGreeting(
    routeDeck.store.getState().projection?.current.node_id ?? null,
  );
}

function FatalShell({
  title,
  error,
  fallback,
  retry,
}: {
  title: string;
  error: unknown;
  fallback: string;
  retry?: () => void;
}) {
  return (
    <section className="bootstrap-error" role="alert">
      <h1>{title}</h1>
      <p>{error instanceof Error ? error.message : fallback}</p>
      {retry === undefined ? null : (
        <button type="button" onClick={retry}>Retry</button>
      )}
    </section>
  );
}

interface ConversationAttempt {
  readonly sequence: number;
  readonly requestId: string;
}

interface RetainedConversationLoad {
  readonly sequence: number;
  readonly promise: Promise<readonly AgentHistoryTurn[]>;
}

type ConversationLoadState =
  | Readonly<{
      phase: "loading";
      greetingPending: boolean;
      progress: AssistantInitiatedTurnProgress | null;
      bootstrapPhase: InitialConversationPhase;
    }>
  | Readonly<{ phase: "ready"; conversation: readonly AgentHistoryTurn[] }>
  | Readonly<{ phase: "recovering" }>
  | Readonly<{ phase: "error"; error: unknown }>;
