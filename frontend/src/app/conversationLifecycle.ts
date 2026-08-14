import {
  createRouteDeckAgentClient,
  createRouteDeckClient,
  type AgentHistoryTurn,
  type AgentChatClient,
  type ConversationRunSnapshot,
  type RouteDeckAgentClient,
} from "@routedeck/core";

import type { AppRouteDeck } from "./createRouteDeck";
import type { ConversationSummary } from "./conversations";
import {
  commitConversationHandoff,
  historyNeedsReconciliation,
  projectionPath,
  reconcileConversationHistory,
} from "./conversationHistory";
import { loadRouteDeck } from "./loadRouteDeck";
import {
  createConversationTransport,
} from "./transports";
import type { AuthorizedTransport, ConversationTransport } from "@/shared/transport/contracts";

export interface MountedConversation {
  summary: ConversationSummary;
  routeDeck: AppRouteDeck;
  chatClient: AgentChatClient;
  initialConversation: readonly AgentHistoryTurn[];
}

interface ConversationMutations {
  create(): Promise<ConversationSummary>;
  replaceAnonymous(id: string): Promise<ConversationSummary>;
}

export class ConversationLifecycle {
  constructor(
    private readonly browser: Window,
    private readonly authorized: AuthorizedTransport,
    private readonly conversations: ConversationMutations,
    private readonly onConversationMounted: (conversationId: string) => void = () => undefined,
  ) {}

  async mount(
    summary: ConversationSummary,
    existingTransport?: ConversationTransport,
    handoff = false,
    handoffPath?: string,
  ): Promise<MountedConversation> {
    const transport = existingTransport ?? createConversationTransport(this.authorized);
    if (existingTransport === undefined) transport.selectConversation(summary.id);
    const routeDeckClient = createRouteDeckClient({
      baseUrl: "/api/routedeck",
      fetch: transport.fetch,
      credentials: "omit",
    });
    const chatClient = createRouteDeckAgentClient({
      baseUrl: "/api/routedeck",
      fetch: transport.fetch,
    });
    if (
      handoffPath !== undefined &&
      summary.active_run?.status === "running"
    ) {
      await settleConversationRun(chatClient, summary.active_run.request_id);
    }
    const routeDeck = await loadRouteDeck(this.browser, routeDeckClient);
    try {
      const mustLoadCanonicalPath =
        handoff || historyNeedsReconciliation(this.browser, summary.id);
      const canonicalPath = mustLoadCanonicalPath
        ? projectionPath(
            routeDeck.contract,
            await routeDeck.client.getSession(),
          )
        : null;
      const initialConversation = await chatClient.loadConversation();
      if (canonicalPath !== null) {
        if (handoff) {
          commitConversationHandoff(
            this.browser,
            summary,
            handoffPath ?? canonicalPath,
          );
        } else {
          reconcileConversationHistory(this.browser, summary.id, canonicalPath);
        }
      } else {
        reconcileConversationHistory(this.browser, summary.id, "");
      }
      this.onConversationMounted(summary.id);
      return Object.freeze({ summary, routeDeck, chatClient, initialConversation });
    } catch (error) {
      routeDeck.privateForms.dispose();
      routeDeck.store.dispose();
      throw error;
    }
  }

  async createNext(
    current: ConversationSummary,
    anonymous: boolean,
  ): Promise<MountedConversation> {
    const next = anonymous
      ? await this.conversations.replaceAnonymous(current.id)
      : await this.conversations.create();
    return await this.mount(next, undefined, true);
  }

  async createFresh(handoffPath?: string): Promise<MountedConversation> {
    return await this.mount(
      await this.conversations.create(),
      undefined,
      true,
      handoffPath,
    );
  }

  dispose(mounted: MountedConversation): void {
    mounted.routeDeck.privateForms.dispose();
    mounted.routeDeck.store.dispose();
  }
}

export async function settleConversationRun(
  client: RouteDeckAgentClient,
  requestId: string,
): Promise<void> {
  let run = await client.loadConversationRun(requestId);
  requireConversationRunIdentity(run, requestId);
  if (!conversationRunIsTerminal(run)) {
    for await (const next of client.streamConversationRunEvents(
      requestId,
      run.cursor,
    )) {
      requireConversationRunIdentity(next, requestId);
      if (next.cursor <= run.cursor) {
        throw new Error("Corpus received a regressed conversation-run cursor.");
      }
      run = next;
      if (conversationRunIsTerminal(run)) break;
    }
  }
  if (!conversationRunIsTerminal(run)) {
    run = await client.loadConversationRun(requestId);
    requireConversationRunIdentity(run, requestId);
  }
  if (run.stage === "interrupted") {
    throw new Error(
      run.failure?.message ??
        "Corpus could not complete the new conversation's arrival turn.",
    );
  }
  if (run.stage !== "completed") {
    throw new Error(
      "Corpus could not establish a terminal new-conversation state.",
    );
  }
}

function conversationRunIsTerminal(run: ConversationRunSnapshot): boolean {
  return run.stage === "completed" || run.stage === "interrupted";
}

function requireConversationRunIdentity(
  run: ConversationRunSnapshot,
  requestId: string,
): void {
  if (run.request_id !== requestId) {
    throw new Error("Corpus received a mismatched conversation-run identity.");
  }
}
