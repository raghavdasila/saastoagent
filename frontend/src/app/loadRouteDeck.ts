import type { BrowserHistoryTarget, RouteDeckClient } from "@routedeck/core";

import { routeDeckClient } from "../routedeck/client";
import { createAppRouteDeck, type AppRouteDeck } from "./createRouteDeck";

export async function loadRouteDeck(
  browser: BrowserHistoryTarget,
  client: RouteDeckClient = routeDeckClient,
): Promise<AppRouteDeck> {
  const contract = await client.getFrontendContract();
  return createAppRouteDeck({ contract, browser, client });
}
