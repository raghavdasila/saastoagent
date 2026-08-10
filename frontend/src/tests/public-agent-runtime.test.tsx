import { render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";

import { PublicAgentApp } from "../features/delivery/PublicAgentApp";

afterEach(() => vi.unstubAllGlobals());

it("renders a natural clarification without leaking owner-only runtime diagnostics", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify({
    session: { session_id: "public-session" },
    agent: {
      revision: 4,
      messages: [{ role: "assistant", content: "Which operation should I use?" }],
      awaiting_clarification: true,
    },
  }), { status: 200, headers: { "Content-Type": "application/json" } })));

  render(<PublicAgentApp slug="store-agent" />);

  expect(await screen.findByRole("heading", { name: "One detail needed" })).toBeVisible();
  expect(screen.getByText("Which operation should I use?")).toBeVisible();
  expect(screen.queryByText(/RouteDeck|NavGraph|ToolRouter|GetProductTypesId|agent_runtime/)).not.toBeInTheDocument();
});
