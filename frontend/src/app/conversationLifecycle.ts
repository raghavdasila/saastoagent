import {
  createRouteDeckAgentClient,
  createRouteDeckClient,
  type AgentHistoryTurn,
  type AgentChatClient,
} from "@routedeck/core";

import type { AppRouteDeck } from "./createRouteDeck";
import { rememberConversation, type ConversationSummary } from "./conversations";
import { loadRouteDeck } from "./loadRouteDeck";
import {
  createConversationTransport,
  type AuthorizedTransport,
  type ConversationTransport,
} from "./transports";

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
  ) {}

  async mount(
    summary: ConversationSummary,
    existingTransport?: ConversationTransport,
    alignRoute = false,
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
    const routeDeck = await loadRouteDeck(this.browser, routeDeckClient);
    if (alignRoute) {
      const path = routeDeck.routes.encode(summary.current_node_id, {});
      this.browser.history.replaceState({}, "", path);
    }
    try {
      const initialConversation = await chatClient.loadConversation();
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
    rememberConversation(this.browser.sessionStorage, next);
    return await this.mount(next, undefined, true);
  }

  dispose(mounted: MountedConversation): void {
    mounted.routeDeck.privateForms.dispose();
    mounted.routeDeck.store.dispose();
  }
}
