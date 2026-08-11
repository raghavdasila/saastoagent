import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import { PublicAgentApp } from "../features/delivery/PublicAgentApp";

afterEach(() => {
  vi.unstubAllGlobals();
  window.sessionStorage.clear();
});

it("renders a natural clarification without leaking owner-only runtime diagnostics", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({
    session: { session_id: "public-session" },
    agent: {
      revision: 4,
      messages: [
        { role: "user", content: "Get product taxonomy" },
        { role: "assistant", content: "Which operation should I use?" },
      ],
      awaiting_clarification: true,
    },
  }), { status: 200, headers: { "Content-Type": "application/json" } })));

  render(<PublicAgentApp slug="store-agent" />);

  expect(await screen.findByRole("heading", { name: "One detail needed" })).toBeVisible();
  expect(screen.getByRole("heading", { name: "Store Agent" })).toBeVisible();
  expect(screen.getByText("Session-scoped conversation")).toBeVisible();
  expect(screen.getByText("Get product taxonomy")).toBeVisible();
  expect(screen.getByText("Which operation should I use?")).toBeVisible();
  expect(screen.getByRole("textbox", { name: "Message the assistant" })).toBeEnabled();
  expect(screen.queryByText(/RouteDeck|NavGraph|ToolRouter|GetProductTypesId|agent_runtime/)).not.toBeInTheDocument();
});

it("restores the exact public session after a page or backend restart", async () => {
  window.sessionStorage.setItem("corpus.public-agent-session.v1:store-agent", "public-session");
  const fetchProbe = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => new Response(JSON.stringify({
    revision: 2,
    messages: [
      { role: "user", content: "List the available product tags." },
      { role: "assistant", content: "No product tags are available." },
    ],
    awaiting_clarification: false,
  }), { status: 200, headers: { "Content-Type": "application/json" } }));
  vi.stubGlobal("fetch", fetchProbe);

  render(<PublicAgentApp slug="store-agent" />);

  expect(await screen.findByText("List the available product tags.")).toBeVisible();
  expect(screen.getByText("No product tags are available.")).toBeVisible();
  expect(fetchProbe).toHaveBeenCalledTimes(1);
  expect(fetchProbe.mock.calls[0]?.[0]).toBe("/api/public/agents/store-agent/sessions/public-session");
  expect(fetchProbe.mock.calls[0]?.[1]).toBeUndefined();
});

it("requires an explicit new-conversation action when a retained session cannot reload", async () => {
  window.sessionStorage.setItem("corpus.public-agent-session.v1:store-agent", "stale-session");
  const fetchProbe = vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify({ message: "This conversation can no longer be loaded." }), { status: 409, headers: { "Content-Type": "application/json" } }))
    .mockResolvedValueOnce(new Response(JSON.stringify({
      session: { session_id: "replacement-session" },
      agent: { revision: 0, messages: [], awaiting_clarification: false },
    }), { status: 200, headers: { "Content-Type": "application/json" } }));
  vi.stubGlobal("fetch", fetchProbe);

  render(<PublicAgentApp slug="store-agent" />);

  expect(await screen.findByRole("alert")).toHaveTextContent("This conversation can no longer be loaded.");
  fireEvent.click(screen.getByRole("button", { name: "Start a new conversation" }));

  await waitFor(() => expect(window.sessionStorage.getItem("corpus.public-agent-session.v1:store-agent")).toBe("replacement-session"));
  expect(fetchProbe).toHaveBeenCalledTimes(2);
  expect(fetchProbe.mock.calls[1]?.[1]).toMatchObject({ method: "POST" });
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});
