import {
  ClientSessionManager,
} from "./clientSession";
import {
  createBrowserRefreshLock,
  createIndexedDbCredentialStore,
} from "./browserSessionAdapters";
import {
  createConversationTransport,
  type AuthorizedTransport,
  type ConversationTransport,
} from "./transports";
import {
  createConversationClient,
  selectConversation,
  type ConversationSummary,
} from "./conversations";

export interface BootstrappedCorpusConnection {
  session: ClientSessionManager;
  authorized: AuthorizedTransport;
  conversationTransport: ConversationTransport;
  conversation: ConversationSummary;
}

export async function bootstrapCorpusConnection(
  browser: Window,
): Promise<BootstrappedCorpusConnection> {
  const session = new ClientSessionManager(
    createIndexedDbCredentialStore(browser.indexedDB),
    createBrowserRefreshLock(browser.navigator),
    browser.fetch.bind(browser),
  );
  await session.bootstrap();
  const authorized = Object.freeze({ fetch: session.authorizedFetch.bind(session) });
  const conversationTransport = createConversationTransport(authorized);
  const conversations = createConversationClient(authorized.fetch);
  let catalog = await conversations.list();
  let selected = selectConversation(browser.sessionStorage, catalog);
  if (selected === null) {
    selected = await conversations.create();
    catalog = [selected];
    selected = selectConversation(browser.sessionStorage, catalog);
  }
  if (selected === null) {
    throw new Error("Corpus did not return an available conversation.");
  }
  conversationTransport.selectConversation(selected.id);
  return Object.freeze({ session, authorized, conversationTransport, conversation: selected });
}
