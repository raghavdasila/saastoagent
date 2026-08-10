import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { Maximize2, Minimize2 } from "lucide-react";
import {
  createRouteDeckAgentClient,
  type AgentChatClient,
  type AgentHistoryTurn,
  type RouteDeckConversationClient,
  type RouteDeckClientState,
} from "@routedeck/core";
import {
  RouteDeckSurfaceHost,
  useRouteDeckConversation,
  useRouteDeckConversationInputPolicy,
  useRouteDeckDispatch,
  useRouteDeckProjection,
  useRouteDeckRuntime,
  useRouteDeckSelector,
  type RouteDeckSurfaceRegistry,
  type RouteDeckSurfaceSlot,
} from "@routedeck/react";

import { Composer } from "./Composer";
import type { ChatSourceUpload } from "./Composer";
import { Conversation } from "./Conversation";
import type { ConversationScrollState } from "./Conversation";
import { CorpusSuggestedActions } from "./CorpusSuggestedActions";
import { RouteDeckSessionVersionContext } from "../routedeck/RouteDeckSessionVersionContext";

const CONVERSATION_SURFACE_SLOTS: readonly RouteDeckSurfaceSlot[] = Object.freeze([
  "active",
  "detail",
  "review",
]);
const EMPTY_LEGAL_OPERATIONS = Object.freeze([]);
const selectSessionVersion = (state: RouteDeckClientState) => state.sessionVersion;
const selectCurrentNodeId = (state: RouteDeckClientState) =>
  state.projection?.current.node_id ?? null;
const selectLegalOperations = (state: RouteDeckClientState) =>
  state.projection?.legal_operations ?? EMPTY_LEGAL_OPERATIONS;
const selectActiveChatRequestId = (state: RouteDeckClientState) => {
  const interaction = state.projection?.interaction;
  return interaction?.phase === "active" && interaction.owner === "chat"
    ? interaction.request_id ?? null
    : null;
};
export interface AgentShellProps {
  registry: RouteDeckSurfaceRegistry;
  client?: AgentChatClient;
  initialConversation?: readonly AgentHistoryTurn[];
  onUploadApiSource?: (file: File) => Promise<ChatSourceUpload>;
}

export function AgentShell({
  registry,
  client,
  initialConversation = [],
  onUploadApiSource,
}: AgentShellProps) {
  const activeRunRequestId = useRouteDeckSelector(selectActiveChatRequestId);
  const chatClient = useMemo(
    () => client ?? createRouteDeckAgentClient(),
    [client],
  );
  const [authoritativeConversation, setAuthoritativeConversation] = useState(
    initialConversation,
  );
  const [presentationGeneration, setPresentationGeneration] = useState(0);
  const [recoveryError, setRecoveryError] = useState<string | null>(null);
  const [conversationStreamActive, setConversationStreamActive] = useState(false);
  const observedActiveRun = useRef<string | null>(null);
  const restoreComposerAfterKeyboardSend = useRef(false);
  const conversationScrollState = useRef<ConversationScrollState>({
    pinnedToBottom: true,
    scrollTop: 0,
  });
  const activeShellElement = useRef<HTMLElement | null>(null);
  const recordKeyboardSend = useCallback(() => {
    restoreComposerAfterKeyboardSend.current = true;
  }, []);
  const setActiveShellElement = useCallback((element: HTMLElement | null) => {
    activeShellElement.current = element;
  }, []);
  useLayoutEffect(() => {
    if (!restoreComposerAfterKeyboardSend.current) return;
    const composer = activeShellElement.current?.querySelector<HTMLTextAreaElement>(
      "#routedeck-agent-message",
    );
    if (composer === undefined || composer === null || composer.disabled) return;
    composer.focus();
    restoreComposerAfterKeyboardSend.current = false;
  }, [presentationGeneration]);

  useEffect(() => {
    if (activeRunRequestId !== null) {
      observedActiveRun.current = activeRunRequestId;
      return;
    }
    if (conversationStreamActive) return;
    const completedRequestId = observedActiveRun.current;
    if (completedRequestId === null) return;
    const loadConversation = (
      chatClient as AgentChatClient & Partial<RouteDeckConversationClient>
    ).loadConversation;
    if (loadConversation === undefined) {
      setRecoveryError(
        "Corpus could not synchronize the completed conversation.",
      );
      return;
    }
    const abort = new AbortController();
    void loadConversation.call(chatClient, abort.signal).then((conversation) => {
      if (abort.signal.aborted) return;
      if (
        !conversation.some(
          (turn) => turn.request_id === completedRequestId,
        )
      ) {
        setRecoveryError(
          "Corpus could not verify the completed conversation.",
        );
        return;
      }
      observedActiveRun.current = null;
      setAuthoritativeConversation(conversation);
      setRecoveryError(null);
      setPresentationGeneration((current) => current + 1);
    }).catch(() => {
      if (!abort.signal.aborted) {
        setRecoveryError(
          "Corpus could not synchronize the completed conversation.",
        );
      }
    });
    return () => abort.abort();
  }, [activeRunRequestId, chatClient, conversationStreamActive]);

  return (
    <>
      <AgentConversationShell
        key={presentationGeneration}
        registry={registry}
        chatClient={chatClient}
        initialConversation={authoritativeConversation}
        activeRunRequestId={activeRunRequestId}
        onStreamActiveChange={setConversationStreamActive}
        onKeyboardSend={recordKeyboardSend}
        onShellElementChange={setActiveShellElement}
        conversationScrollState={conversationScrollState.current}
        onUploadApiSource={onUploadApiSource}
      />
      {recoveryError === null ? null : (
        <p role="alert" data-agent-chat-recovery-error="">
          {recoveryError}
        </p>
      )}
    </>
  );
}

interface AgentConversationShellProps {
  registry: RouteDeckSurfaceRegistry;
  chatClient: AgentChatClient;
  initialConversation: readonly AgentHistoryTurn[];
  activeRunRequestId: string | null;
  onStreamActiveChange(active: boolean): void;
  onKeyboardSend(): void;
  onShellElementChange(element: HTMLElement | null): void;
  conversationScrollState: ConversationScrollState;
  onUploadApiSource?: (file: File) => Promise<ChatSourceUpload>;
}

function AgentConversationShell({
  registry,
  chatClient,
  initialConversation,
  activeRunRequestId,
  onStreamActiveChange,
  onKeyboardSend,
  onShellElementChange,
  conversationScrollState,
  onUploadApiSource,
}: AgentConversationShellProps) {
  const runtime = useRouteDeckRuntime();
  const sessionVersion = useRouteDeckSelector(selectSessionVersion);
  const currentNodeId = useRouteDeckSelector(selectCurrentNodeId);
  const legalOperations = useRouteDeckSelector(selectLegalOperations);
  const conversationInput = useRouteDeckConversationInputPolicy();
  const projection = useRouteDeckProjection();
  const dispatch = useRouteDeckDispatch();
  const surfaceDockRef = useRef<HTMLDivElement>(null);
  const [surfaceExpanded, setSurfaceExpanded] = useState(false);
  const currentSessionVersion = useCallback(
    () => runtime.store.getState().sessionVersion,
    [runtime.store],
  );
  const resumableActiveRunRequestId =
    activeRunRequestId !== null &&
    !initialConversation.some(
      (turn) =>
        turn.role === "assistant" && turn.request_id === activeRunRequestId,
    )
      ? activeRunRequestId
      : null;
  const agent = useRouteDeckConversation({
    client: chatClient,
    initialConversation,
    sessionVersion,
    currentSessionVersion,
    createRequestId: runtime.createRequestId,
    synchronizeTo: runtime.store.synchronizeTo,
    resync: runtime.store.resync,
    activeRunRequestId: resumableActiveRunRequestId,
  });
  const send = useCallback(async (message: string) => {
    onStreamActiveChange(true);
    try {
      await agent.send(message);
    } finally {
      onStreamActiveChange(false);
    }
  }, [agent.send, onStreamActiveChange]);
  const retry = useCallback(async () => {
    onStreamActiveChange(true);
    try {
      await agent.retry();
    } finally {
      onStreamActiveChange(false);
    }
  }, [agent.retry, onStreamActiveChange]);
  const reviewIsCurrent =
    agent.review !== null &&
    legalOperations.some(
      (operation) =>
        operation.operation_id === agent.review?.operation_id &&
        operation.review_required,
    );
  const conversationInputDisabled = conversationInput?.enabled === false;
  const composerDisabled =
    agent.status === "streaming" ||
    conversationInputDisabled;
  const disabledReason = conversationInputDisabled
    ? conversationInput.disabled_message ?? undefined
    : undefined;
  const canAttachApiDefinition =
    onUploadApiSource !== undefined
    && legalOperations.some(
      (operation) => operation.operation_id === "agents.open_source_creation",
    );
  const canUploadWorkspaceApiDefinition =
    onUploadApiSource !== undefined
    && legalOperations.some(
      (operation) => operation.operation_id === "workspace.open_sources"
        || operation.operation_id === "sources.open_api_creation",
    );
  const uploadApiDefinition = canAttachApiDefinition
    ? onUploadApiSource
    : canUploadWorkspaceApiDefinition
      ? onUploadApiSource
      : undefined;

  useEffect(() => {
    if (surfaceDockRef.current !== null) {
      surfaceDockRef.current.scrollTop = 0;
    }
  }, [currentNodeId]);

  return (
    <main ref={onShellElementChange} data-agent-shell="" data-surface-layout={surfaceExpanded ? "split" : "dock"}>
      <Conversation
        messages={agent.messages}
        status={agent.status}
        scrollState={conversationScrollState}
        suggestedActions={
          <CorpusSuggestedActions disabled={agent.status === "streaming"} />
        }
      />
      <div ref={surfaceDockRef} data-agent-surface-dock="">
        <div data-agent-surface-toolbar="">
          <span>{surfaceExpanded ? "Chat and surface" : "Current workspace"}</span>
          <button type="button" aria-pressed={surfaceExpanded} onClick={() => setSurfaceExpanded((value) => !value)}>
            {surfaceExpanded ? <Minimize2 aria-hidden="true" /> : <Maximize2 aria-hidden="true" />}
            {surfaceExpanded ? "Return to dock" : "Maximize surface"}
          </button>
        </div>
        <div data-agent-surface="">
          <RouteDeckSessionVersionContext.Provider value={sessionVersion ?? 0}>
            <RouteDeckSurfaceHost
              registry={registry}
              slots={CONVERSATION_SURFACE_SLOTS}
            />
          </RouteDeckSessionVersionContext.Provider>
        </div>
      </div>
      {!reviewIsCurrent || agent.review === null ? null : (
        <CorpusReviewRequiredNotice />
      )}
      {agent.error === null ? null : (
        <p role="alert" data-agent-chat-error={agent.error.code}>
          Corpus could not complete that request. Try again.
        </p>
      )}
      <div data-agent-input-dock="">
        <Composer
          disabled={composerDisabled}
          showCancel={agent.status === "streaming"}
          disabledReason={disabledReason}
          onSend={send}
          onKeyboardSend={onKeyboardSend}
          {...(uploadApiDefinition === undefined
            ? {}
            : { onUploadApiSource: uploadApiDefinition })}
          onCancel={agent.cancel}
          {...(agent.pendingRequest === null
            ? {}
            : {
                onRetry: retry,
                onDiscardPending: agent.discardPending,
              })}
        />
      </div>
    </main>
  );
}

export function CorpusReviewRequiredNotice() {
  return (
    <section role="status" data-agent-review-required="">
      <h2>Approval required</h2>
      <p>A consequential Corpus action is waiting for your explicit review.</p>
    </section>
  );
}
