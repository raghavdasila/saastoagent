import { expect, it, vi } from "vitest";

import { createConversationTransport } from "../app/transports";

it("adds the selected conversation only to conversation-transport requests", async () => {
  const authorizedFetch = vi.fn(
    async (_input: RequestInfo | URL, _init?: RequestInit) => new Response("{}"),
  );
  const transport = createConversationTransport({ fetch: authorizedFetch });
  transport.selectConversation("cv_public");
  await transport.fetch("/api/routedeck/session", { method: "GET" });
  const headers = new Headers(authorizedFetch.mock.calls[0]?.[1]?.headers);
  expect(headers.get("X-Corpus-Conversation-ID")).toBe("cv_public");

  await authorizedFetch("/api/sources", { method: "GET" });
  const bearerOnlyHeaders = new Headers(authorizedFetch.mock.calls[1]?.[1]?.headers);
  expect(bearerOnlyHeaders.get("X-Corpus-Conversation-ID")).toBeNull();
});
