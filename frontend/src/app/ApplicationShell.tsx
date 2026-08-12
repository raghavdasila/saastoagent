import type {
  AgentChatClient,
  AgentHistoryTurn,
} from "@routedeck/core";
import {
  RouteDeckProvider,
  type RouteDeckSurfaceRegistry,
} from "@routedeck/react";
import type { ComponentProps, ReactNode } from "react";

import { AgentShell } from "./AgentShell";
import type { ChatSourceUpload } from "./Composer";
import { ApplicationNavigationDrawer } from "./ApplicationNavigationDrawer";
import type { AppRouteDeck } from "./createRouteDeck";
import { NavgraphSidebar } from "./NavgraphSidebar";
import {
  OwnerSessionProvider,
  useOwnerSession,
} from "../auth/OwnerSessionContext";

export interface ApplicationShellProps {
  routeDeck: AppRouteDeck;
  registry: RouteDeckSurfaceRegistry;
  header: ReactNode;
  navigation?: ReactNode;
  mainHeader?: ReactNode;
  chatClient?: AgentChatClient;
  initialConversation?: readonly AgentHistoryTurn[];
  onConversationSynchronized?: (
    conversation: readonly AgentHistoryTurn[],
  ) => void;
  onUploadApiSource?: (file: File) => Promise<ChatSourceUpload>;
}

export function ApplicationShell({
  routeDeck,
  registry,
  header,
  navigation,
  mainHeader,
  chatClient,
  initialConversation = [],
  onConversationSynchronized,
  onUploadApiSource,
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
          <header data-application-header="">
            {header}
            {navigation === undefined ? null : (
              <ApplicationNavigationDrawer navigation={navigation} />
            )}
          </header>
          <div data-application-layout="">
            {navigation === undefined ? null : (
              <nav data-application-navigation="">{navigation}</nav>
            )}
            <section data-application-main="">
              {mainHeader === undefined ? null : (
                <header data-application-main-header="">{mainHeader}</header>
              )}
              <AuthenticatedAgentShell
                key={conversationKey}
                registry={registry}
                initialConversation={initialConversation}
                onConversationSynchronized={onConversationSynchronized}
                {...(chatClient === undefined ? {} : { client: chatClient })}
                {...(onUploadApiSource === undefined ? {} : { onUploadApiSource })}
              />
            </section>
            <NavgraphSidebar />
          </div>
        </div>
      </OwnerSessionProvider>
    </RouteDeckProvider>
  );
}

function AuthenticatedAgentShell({
  onUploadApiSource,
  ...props
}: Omit<ComponentProps<typeof AgentShell>, "onUploadApiSource"> & {
  onUploadApiSource?: (file: File) => Promise<ChatSourceUpload>;
}) {
  const { session } = useOwnerSession();
  return (
    <AgentShell
      {...props}
      {...(session === null || onUploadApiSource === undefined
        ? {}
        : { onUploadApiSource })}
    />
  );
}
