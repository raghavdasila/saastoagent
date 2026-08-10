import { expect, it, vi } from "vitest";

import { createConversationTransport } from "../app/transports";
import { SourceClient } from "../features/sources/sourceClient";

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

it("binds only route-plan requests to the exact selected conversation", async () => {
  const authorizedFetch = vi.fn(
    async (_input: RequestInfo | URL, _init?: RequestInit) =>
      new Response("null", { headers: { "Content-Type": "application/json" } }),
  );
  const client = new SourceClient({ fetch: authorizedFetch });
  client.selectConversation("conversation-route-plan");

  await client.list();
  await client.currentApiRoutePlan("source-one", "revision-one");
  await client.createApiRoutePlan("source-one", {
    source_revision_id: "revision-one",
    profile_id: "profile-one",
    curation_id: "curation-one",
    request_text: "get product taxonomy",
    provided_inputs: {},
  });
  await client.clarifyApiRoutePlan("source-one", "plan-one", {
    source_revision_id: "revision-one",
    expected_record_id: "record-one",
    answers: { operation_id: "GetProductTypesId" },
  });

  const headers = authorizedFetch.mock.calls.map((call) =>
    new Headers(call[1]?.headers)
  );
  expect(headers[0]?.get("X-Corpus-Conversation-ID")).toBeNull();
  expect(headers.slice(1).map((item) => item.get("X-Corpus-Conversation-ID")))
    .toEqual([
      "conversation-route-plan",
      "conversation-route-plan",
      "conversation-route-plan",
    ]);

  client.clearConversation();
  await expect(client.currentApiRoutePlan("source-one", "revision-one"))
    .rejects.toMatchObject({ code: "source_conversation_required", status: 0 });
  expect(authorizedFetch).toHaveBeenCalledTimes(4);
});
