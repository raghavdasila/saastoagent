import type {
  AgentChatClient,
  AgentHistoryTurn,
  AssistantInitiatedTurnProgress,
} from "@routedeck/core";
import {
  RouteDeckProvider,
  type RouteDeckSurfaceRegistry,
} from "@routedeck/react";
import type { ReactNode } from "react";

import { AgentShell } from "./AgentShell";
import type { AppRouteDeck } from "./createRouteDeck";
import { NavgraphSidebar } from "./NavgraphSidebar";
import { OwnerSessionProvider } from "../features/workspace/OwnerSessionContext";

export interface ApplicationShellProps {
  routeDeck: AppRouteDeck;
  registry: RouteDeckSurfaceRegistry;
  header: ReactNode;
  navigation?: ReactNode;
  mainHeader?: ReactNode;
  chatClient?: AgentChatClient;
  initialConversation?: readonly AgentHistoryTurn[];
  conversationBootstrapPending?: boolean;
  conversationBootstrapProgress?: AssistantInitiatedTurnProgress | null;
}

export function ApplicationShell({
  routeDeck,
  registry,
  header,
  navigation,
  mainHeader,
  chatClient,
  initialConversation = [],
  conversationBootstrapPending = false,
  conversationBootstrapProgress = null,
}: ApplicationShellProps) {
  const conversationKey =
    initialConversation.at(-1)?.turn_id ?? "empty-conversation";
  return (
    <RouteDeckProvider
      store={routeDeck.store}
      contract={routeDeck.contract}
      routeCodec={routeDeck.routes}
      routeController={routeDeck.routeController}
      privateForms={routeDeck.privateForms}
      navigationActions={routeDeck.navigationActions}
    >
      <OwnerSessionProvider>
        <div data-routedeck-application="">
          <header data-application-header="">{header}</header>
          <div data-application-layout="">
          {navigation === undefined ? null : (
            <nav data-application-navigation="">{navigation}</nav>
          )}
          <section data-application-main="">
            {mainHeader === undefined ? null : (
              <header data-application-main-header="">{mainHeader}</header>
            )}
            <AgentShell
              key={conversationKey}
              registry={registry}
              initialConversation={initialConversation}
              conversationBootstrapPending={conversationBootstrapPending}
              conversationBootstrapProgress={conversationBootstrapProgress}
              {...(chatClient === undefined ? {} : { client: chatClient })}
            />
          </section>
          <NavgraphSidebar />
          </div>
        </div>
      </OwnerSessionProvider>
    </RouteDeckProvider>
  );
}
