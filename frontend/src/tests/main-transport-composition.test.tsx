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
    agentClients: [] as unknown[],
    agentStores: [] as unknown[],
    workspaceClients: [] as unknown[],
    workspaceStores: [] as unknown[],
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
vi.mock("../auth/authClient", () => ({
  configureOwnerAuthClient: state.configureOwnerAuthClient,
}));
vi.mock("../features/sources/sourceClient", () => ({
  SourceClient: class {
    constructor(transport: unknown) {
      state.sourceClients.push(transport);
    }
  },
}));
vi.mock("../features/agents/client", () => ({
  AgentClient: class {
    constructor(transport: unknown) {
      state.agentClients.push(transport);
    }
  },
}));
vi.mock("../features/agents/store", () => ({
  AgentStore: class {
    constructor(client: unknown) {
      state.agentStores.push(client);
    }
  },
}));
vi.mock("../features/workspace/client", () => ({
  WorkspaceClient: class {
    constructor(transport: unknown) {
      state.workspaceClients.push(transport);
    }
  },
}));
vi.mock("../features/workspace/store", () => ({
  WorkspaceStore: class {
    constructor(client: unknown) {
      state.workspaceStores.push(client);
    }
  },
}));
vi.mock("../routedeck/surfaces", () => ({
  createCorpusSurfaceRegistry: state.createCorpusSurfaceRegistry,
}));

afterEach(() => {
  vi.resetModules();
  document.body.replaceChildren();
  window.history.replaceState({}, "", "/");
});

it("composes bearer auth and Sources with conversation-scoped RouteDeck clients", async () => {
  window.history.replaceState({}, "", "/");
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
  expect(state.agentClients).toEqual([state.authorized]);
  expect(state.agentStores).toHaveLength(1);
  expect(state.workspaceClients).toEqual([state.authorized]);
  expect(state.workspaceStores).toHaveLength(1);
  expect(state.createRouteDeckClient).toHaveBeenCalledWith(expect.objectContaining({
    fetch: state.conversationTransport.fetch,
    credentials: "omit",
  }));
  expect(state.createRouteDeckAgentClient).toHaveBeenCalledWith(expect.objectContaining({
    fetch: state.conversationTransport.fetch,
  }));
}, 10_000);
