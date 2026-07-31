import { afterEach, expect, it, vi } from "vitest";

const state = vi.hoisted(() => {
  const authorized = { fetch: vi.fn() };
  const conversationFetch = vi.fn();
  return {
    authorized,
    conversationTransport: {
      fetch: conversationFetch,
      selectConversation: vi.fn(),
      clearConversation: vi.fn(),
    },
    bootstrap: vi.fn(),
    configureOwnerAuthClient: vi.fn(),
    createRouteDeckClient: vi.fn(() => ({ kind: "route-client" })),
    createRouteDeckAgentClient: vi.fn(() => ({
      async loadConversation() { return []; },
    })),
    sourceClients: [] as unknown[],
    createCorpusSurfaceRegistry: vi.fn(() => ({})),
    loadRouteDeck: vi.fn(async () => ({ store: { dispose: vi.fn() } })),
    render: vi.fn(),
  };
});

vi.mock("react-dom/client", () => ({
  createRoot: () => ({ render: state.render }),
}));
vi.mock("@routedeck/core", () => ({
  createRouteDeckClient: state.createRouteDeckClient,
  createRouteDeckAgentClient: state.createRouteDeckAgentClient,
}));
vi.mock("../app/bootstrapConnection", () => ({
  bootstrapCorpusConnection: state.bootstrap,
}));
vi.mock("../app/loadRouteDeck", () => ({ loadRouteDeck: state.loadRouteDeck }));
vi.mock("../features/lounge/authClient", () => ({
  configureOwnerAuthClient: state.configureOwnerAuthClient,
}));
vi.mock("../features/sources/sourceClient", () => ({
  SourceClient: class {
    constructor(transport: unknown) {
      state.sourceClients.push(transport);
    }
  },
}));
vi.mock("../routedeck/surfaces", () => ({
  createCorpusSurfaceRegistry: state.createCorpusSurfaceRegistry,
}));

afterEach(() => {
  vi.resetModules();
  document.body.replaceChildren();
});

it("composes bearer auth and Sources with conversation-scoped RouteDeck clients", async () => {
  document.body.innerHTML = '<div id="root"></div>';
  state.bootstrap.mockResolvedValue({
    authorized: state.authorized,
    conversationTransport: state.conversationTransport,
    session: { signOut: vi.fn() },
    conversation: { id: "cv-public" },
  });

  await import("../main");
  await new Promise((resolve) => setTimeout(resolve, 0));

  expect(state.configureOwnerAuthClient).toHaveBeenCalledWith({
    transport: state.authorized,
    signOut: expect.any(Function),
  });
  expect(state.sourceClients).toEqual([state.authorized]);
  expect(state.createRouteDeckClient).toHaveBeenCalledWith(expect.objectContaining({
    fetch: state.conversationTransport.fetch,
    credentials: "omit",
  }));
  expect(state.createRouteDeckAgentClient).toHaveBeenCalledWith(expect.objectContaining({
    fetch: state.conversationTransport.fetch,
  }));
});
