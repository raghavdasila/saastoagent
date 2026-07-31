import type { BrowserHistoryTarget, RouteDeckClient } from "@routedeck/core";

import { createAppRouteDeck, type AppRouteDeck } from "./createRouteDeck";

export async function loadRouteDeck(
  browser: BrowserHistoryTarget,
  client: RouteDeckClient,
): Promise<AppRouteDeck> {
  const contract = await client.getFrontendContract();
  return createAppRouteDeck({ contract, browser, client });
}
