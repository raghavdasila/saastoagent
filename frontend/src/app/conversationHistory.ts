import {
  createRouteDeckRouteCodec,
  type FrontendContract,
  type RouteDeckProjection,
} from "@routedeck/core";

import { rememberConversation, type ConversationStorage, type ConversationSummary } from "./conversations";
import {
  projectionHasPublicRouteKey,
  projectionMatchesResumeCapability,
} from "./createRouteDeck";

export const HISTORY_CONVERSATION_KEY = "corpus.history-conversation.v1";

interface ConversationHistoryBrowser {
  history: Pick<History, "replaceState" | "state">;
  sessionStorage: ConversationStorage;
}

export function historyNeedsReconciliation(
  browser: ConversationHistoryBrowser,
  conversationId: string,
): boolean {
  return (
    hasRouteDeckHistoryEntry(browser.history.state) &&
    browser.sessionStorage.getItem(HISTORY_CONVERSATION_KEY) !== conversationId
  );
}

export function reconcileConversationHistory(
  browser: ConversationHistoryBrowser,
  conversationId: string,
  canonicalPath: string,
): void {
  if (historyNeedsReconciliation(browser, conversationId)) {
    browser.history.replaceState({}, "", canonicalPath);
  }
  browser.sessionStorage.setItem(HISTORY_CONVERSATION_KEY, conversationId);
}

export function commitConversationHandoff(
  browser: ConversationHistoryBrowser,
  conversation: ConversationSummary,
  canonicalPath: string,
): void {
  browser.history.replaceState({}, "", canonicalPath);
  browser.sessionStorage.setItem(HISTORY_CONVERSATION_KEY, conversation.id);
  rememberConversation(browser.sessionStorage, conversation);
}

export function projectionPath(
  contract: FrontendContract,
  projection: RouteDeckProjection,
): string {
  const routes = createRouteDeckRouteCodec(contract, {
    validatePublicRouteKey: (name, value) =>
      projectionHasPublicRouteKey(projection, name, value),
    validateResumeCapability: (handle, nodeId, params) =>
      projectionMatchesResumeCapability(
        projection,
        handle,
        nodeId,
        params,
      ),
  });
  const params: Record<string, string> = {};
  for (const parameter of projection.current.route_params) {
    if (typeof parameter.value !== "string") {
      throw new Error("Corpus received an invalid route parameter.");
    }
    params[parameter.name] = parameter.value;
  }
  const resumeHandle = projection.navigation.resume_handle;
  return routes.encode(projection.current.node_id, params, {
    ...(resumeHandle === null ? {} : { resumeHandle }),
  });
}

function hasRouteDeckHistoryEntry(value: unknown): boolean {
  if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
  const outer = value as Record<string, unknown>;
  if (Object.keys(outer).length !== 1) return false;
  const routeDeck = outer.routedeck;
  if (routeDeck === null || typeof routeDeck !== "object" || Array.isArray(routeDeck)) {
    return false;
  }
  const state = routeDeck as Record<string, unknown>;
  return (
    Object.keys(state).length === 2 &&
    state.version === 1 &&
    Number.isSafeInteger(state.history_entry_id) &&
    (state.history_entry_id as number) > 0
  );
}
