import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { AgentChatClient } from "@routedeck/core";
import {
  defineRouteDeckSurfaceRegistry,
  type RouteDeckBootstrapActionRequiredState,
} from "@routedeck/react";
import { expect, it, vi } from "vitest";

import { ApplicationShell } from "../app/ApplicationShell";
import { useOwnerSession } from "../auth/OwnerSessionContext";
import { configureOwnerAuthClient } from "../auth/authClient";
import { BootstrapLoadingShell } from "../app/BootstrapLoadingShell";
import { CorpusRecoveryCoordinator } from "../app/CorpusRecoveryCoordinator";
import { loadRouteDeck } from "../app/loadRouteDeck";
import {
  frameworkContractFixture,
  frameworkProjectionFixture,
  TestRouteDeckClient,
} from "./routeDeckHarness";

const idleChatClient: AgentChatClient = Object.freeze({
  async *stream() {},
  async loadConversation() { return []; },
  async startAssistantRun() { throw new Error("not used"); },
  async loadConversationRun() { throw new Error("not used"); },
  async *streamConversationRunEvents() {},
});
const registry = defineRouteDeckSurfaceRegistry({
  "test.active": () => <section>Loaded feature surface</section>,
  "test.detail": () => <section>Loaded detail surface</section>,
});

function AuthTransitionSurface() {
  const { loading, setSession } = useOwnerSession();
  return (
    <button
      type="button"
      disabled={loading}
      onClick={() => setSession({
        type: "owner",
        owner: {
          email: "owner@example.test",
          display_name: "Owner",
          is_verified: true,
        },
        organization: { name: "Owner Workspace", slug: "owner-workspace" },
        membership: { role: "owner" },
      })}
    >
      Authenticate owner
    </button>
  );
}

it("loads the server contract into the product-neutral RouteDeck host", async () => {
  const contract = frameworkContractFixture();
  const client = new TestRouteDeckClient(frameworkProjectionFixture(), contract);
  const routeDeck = await loadRouteDeck(window, client);
  await routeDeck.store.bootstrap();

  render(
    <ApplicationShell
      routeDeck={routeDeck}
      registry={registry}
      chatClient={idleChatClient}
      header={<strong>Injected product header</strong>}
    />,
  );

  expect(screen.getByText("Injected product header")).toBeVisible();
  expect(screen.getByText("Loaded feature surface")).toBeVisible();
  routeDeck.store.dispose();
});

it("reveals API attachment from live owner state after anonymous bootstrap", async () => {
  configureOwnerAuthClient({
    transport: {
      fetch: vi.fn(async () => new Response(
        JSON.stringify({ type: "anonymous" }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      )),
    },
    signOut: vi.fn(async () => undefined),
  });
  const contract = frameworkContractFixture();
  const projection = frameworkProjectionFixture();
  projection.entities = [{ entity_kind: "agent", handle: "agent-current", values: [] }];
  projection.legal_operations = [{
    operation_id: "agents.open_source_creation",
    title: "Create and attach a Source",
    safety_class: "navigation",
    allowed_sources: ["surface", "agent"],
  }];
  const client = new TestRouteDeckClient(projection, contract);
  const routeDeck = await loadRouteDeck(window, client);
  await routeDeck.store.bootstrap();
  const authRegistry = defineRouteDeckSurfaceRegistry({
    "test.active": AuthTransitionSurface,
    "test.detail": () => <section>Loaded detail surface</section>,
  });

  render(
    <ApplicationShell
      routeDeck={routeDeck}
      registry={authRegistry}
      chatClient={idleChatClient}
      header={<strong>Corpus</strong>}
      onUploadApiSource={vi.fn(async () => ({
        attachmentId: "attachment-0001",
        displayName: "catalog",
      }))}
    />,
  );

  const authenticate = await screen.findByRole("button", { name: "Authenticate owner" });
  await waitFor(() => expect(authenticate).toBeEnabled());
  expect(screen.queryByLabelText("Attach API definition")).not.toBeInTheDocument();
  fireEvent.click(authenticate);
  expect(await screen.findByLabelText("Attach API definition")).toBeVisible();
  routeDeck.store.dispose();
});

it("reveals API attachment in authenticated Workspace without inventing an Agent binding", async () => {
  configureOwnerAuthClient({
    transport: {
      fetch: vi.fn(async () => new Response(
        JSON.stringify({ type: "anonymous" }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      )),
    },
    signOut: vi.fn(async () => undefined),
  });
  const contract = frameworkContractFixture();
  const projection = frameworkProjectionFixture();
  projection.entities = [];
  projection.legal_operations = [{
    operation_id: "workspace.open_sources",
    title: "Open Sources",
    safety_class: "navigation",
    allowed_sources: ["surface", "agent"],
  }];
  const client = new TestRouteDeckClient(projection, contract);
  const routeDeck = await loadRouteDeck(window, client);
  await routeDeck.store.bootstrap();
  const authRegistry = defineRouteDeckSurfaceRegistry({
    "test.active": AuthTransitionSurface,
    "test.detail": () => <section>Loaded detail surface</section>,
  });

  render(
    <ApplicationShell
      routeDeck={routeDeck}
      registry={authRegistry}
      chatClient={idleChatClient}
      header={<strong>Corpus</strong>}
      onUploadApiSource={vi.fn(async () => ({
        attachmentId: "attachment-0001",
        displayName: "catalog",
      }))}
    />,
  );

  const authenticate = await screen.findByRole("button", { name: "Authenticate owner" });
  await waitFor(() => expect(authenticate).toBeEnabled());
  expect(screen.queryByLabelText("Attach API definition")).not.toBeInTheDocument();
  fireEvent.click(authenticate);
  expect(await screen.findByLabelText("Attach API definition")).toBeVisible();
  routeDeck.store.dispose();
});

it("keeps standalone chat upload available in Source Hub without reusing a retained Agent binding", async () => {
  configureOwnerAuthClient({
    transport: {
      fetch: vi.fn(async () => new Response(
        JSON.stringify({ type: "anonymous" }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      )),
    },
    signOut: vi.fn(async () => undefined),
  });
  const contract = frameworkContractFixture();
  const projection = frameworkProjectionFixture();
  projection.entities = [{ entity_kind: "agent", handle: "agent-retained", values: [] }];
  projection.legal_operations = [{
    operation_id: "sources.open_api_creation",
    title: "Add API Source",
    safety_class: "navigation",
    allowed_sources: ["surface", "agent"],
  }];
  const client = new TestRouteDeckClient(projection, contract);
  const routeDeck = await loadRouteDeck(window, client);
  await routeDeck.store.bootstrap();
  const authRegistry = defineRouteDeckSurfaceRegistry({
    "test.active": AuthTransitionSurface,
    "test.detail": () => <section>Loaded detail surface</section>,
  });

  render(
    <ApplicationShell
      routeDeck={routeDeck}
      registry={authRegistry}
      chatClient={idleChatClient}
      header={<strong>Corpus</strong>}
      onUploadApiSource={vi.fn(async () => ({
        attachmentId: "attachment-0001",
        displayName: "catalog",
      }))}
    />,
  );

  const authenticate = await screen.findByRole("button", { name: "Authenticate owner" });
  await waitFor(() => expect(authenticate).toBeEnabled());
  fireEvent.click(authenticate);
  expect(await screen.findByLabelText("Attach API definition")).toBeVisible();
  routeDeck.store.dispose();
});

it("opens application navigation from a mobile menu without moving the desktop navigation", async () => {
  const contract = frameworkContractFixture();
  const client = new TestRouteDeckClient(frameworkProjectionFixture(), contract);
  const routeDeck = await loadRouteDeck(window, client);
  await routeDeck.store.bootstrap();

  render(
    <ApplicationShell
      routeDeck={routeDeck}
      registry={registry}
      chatClient={idleChatClient}
      header={<strong>Injected product header</strong>}
      navigation={<div>Workspace destinations</div>}
    />,
  );

  expect(screen.getByRole("navigation")).toHaveTextContent("Workspace destinations");
  const menuButton = screen.getByRole("button", { name: "Open navigation menu" });
  fireEvent.click(menuButton);
  const drawer = screen.getByRole("dialog", { name: "Workspace navigation" });
  expect(within(drawer).getByText("Workspace destinations")).toBeVisible();

  routeDeck.store.dispose();
});

it("keeps the loading shell generic for reuse by a fresh project", () => {
  render(<BootstrapLoadingShell />);

  expect(screen.getByRole("status")).toHaveTextContent("Preparing Corpus");
  expect(screen.queryByText("Corpus")).not.toBeInTheDocument();
});

it("replaces an expired conversation without rendering framework recovery UI", async () => {
  const replaceConversation = vi.fn(async () => undefined);
  const fetch = vi.fn(async () => ({
    ok: true,
    status: 204,
    json: async () => ({}),
  }));
  vi.stubGlobal("fetch", fetch);
  const state: RouteDeckBootstrapActionRequiredState = {
    phase: "recovery",
    syncStatus: "error",
    reason: "resume_expired",
    busy: false,
    activeAction: null,
    error: {
      code: "stream_session_expired",
      message: "The RouteDeck event session has expired.",
    },
    actions: [{ kind: "start_new_session", run: vi.fn() }],
  };

  render(
    <CorpusRecoveryCoordinator
      state={state}
      replaceConversation={replaceConversation}
    />,
  );

  expect(screen.getByRole("status")).toHaveTextContent("Preparing Corpus");
  expect(screen.queryByText("Application session expired")).not.toBeInTheDocument();
  expect(screen.queryByText("The RouteDeck event session has expired.")).not.toBeInTheDocument();
  await waitFor(() => expect(replaceConversation).toHaveBeenCalledOnce());
  expect(fetch).not.toHaveBeenCalled();
});
