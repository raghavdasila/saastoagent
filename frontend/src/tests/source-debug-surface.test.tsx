import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { RouteDeckDispatchResult } from "@routedeck/core";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { expect, it, vi } from "vitest";

import { SourceHubSurface } from "../features/sources/SourceHubSurface";
import { SourceClient } from "../features/sources/sourceClient";
import { ContractRevisionStore } from "../features/sources/contractRevisionStore";
import { PrivateFormGate } from "../routedeck/PrivateFormGate";
import {
  frameworkContractFixture,
  frameworkProjectionFixture,
  renderRouteDeckComponent,
} from "./routeDeckHarness";


it("uploads the optional description and exposes persisted failure retry", async () => {
  let listCount = 0;
  const failed = sourceView("failed");
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/sources" && (init?.method ?? "GET") === "GET") {
      listCount += 1;
      return jsonResponse(listCount === 1 ? [] : [failed]);
    }
    if (url === "/api/sources/api/attachments" && init?.method === "POST") {
      const body = init.body as FormData;
      expect(body.get("file")).toMatchObject({ name: "widgets.yaml" });
      expect(body.get("description")).toMatchObject({ name: "widgets.md" });
      expect(new Headers(init.headers).get("X-Corpus-Conversation-ID")).toBe("conversation-test-01");
      return jsonResponse({
        attachment_id: "attachmentopaque1",
        display_name: "Widget API",
        filename: "widgets.yaml",
        content_sha256: "a".repeat(64),
        staged_at: "2026-08-07T10:00:00Z",
        state: "staged",
        source_id: null,
        source_revision_id: null,
      }, 201);
    }
    if (url === "/api/sources/api/attachments/current") {
      return jsonResponse({
        attachment_id: "attachmentopaque1",
        display_name: "Widget API",
        filename: "widgets.yaml",
        content_sha256: "a".repeat(64),
        staged_at: "2026-08-07T10:00:00Z",
        state: "accepted",
        source_id: failed.source_id,
        source_revision_id: failed.revision.revision_id,
      });
    }
    throw new Error(`Unexpected request: ${init?.method ?? "GET"} ${url}`);
  });
  const dispatchAffordance = vi.fn(async (id: string) =>
    dispatchResult(
      id,
      id === "retry_processing" ? "queued" : id === "accept_staged_api" ? "accepted" : "opened",
    )
  );
  const rendered = await renderSourceHub(
    dispatchAffordance,
    new SourceClient({ fetch: fetchMock }),
    {
      form_handle: "sources-api-connection",
      mode: "create",
    },
  );

  expect(await screen.findByRole("heading", { name: "Add an API source" })).toBeVisible();
  fireEvent.change(screen.getByLabelText("Source name"), { target: { value: "Widget API" } });
  fireEvent.change(screen.getByLabelText("OpenAPI or Swagger definition"), {
    target: { files: [new File(["openapi: 3.0.3"], "widgets.yaml", { type: "application/yaml" })] },
  });
  fireEvent.change(screen.getByLabelText("Markdown description (optional)"), {
    target: { files: [new File(["# Widgets"], "widgets.md", { type: "text/markdown" })] },
  });
  fireEvent.submit(
    screen.getByRole("button", { name: "Add API definition" }).closest("form")!,
  );

  expect(await screen.findByText("source_processing_failed")).toBeVisible();
  expect(screen.getByText("ToolRouter rejected the definition.")).toBeVisible();
  expect(screen.getByText("widgets.md")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Retry processing" }));
  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledWith(
    "retry_processing", { source_id: "sourceopaque0001" },
  ));
  rendered.dispose();
});


it("keeps Source Hub as inventory and opens one exact API Source workflow", async () => {
  const ready = sourceView("ready");
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    if (String(input) === "/api/sources") return jsonResponse([ready]);
    throw new Error(`Unexpected request: ${String(input)}`);
  });
  const dispatchAffordance = vi.fn(async (id: string) => dispatchResult(id, "opened"));
  const rendered = await renderSourceHub(
    dispatchAffordance,
    new SourceClient({ fetch: fetchMock }),
    {},
    "hub",
  );

  expect(await screen.findByRole("heading", { name: "Source Hub" })).toBeVisible();
  expect(screen.getByRole("list", { name: "API sources" })).toBeVisible();
  expect(screen.queryByRole("heading", { name: "Semantic graph" })).not.toBeInTheDocument();
  await screen.findAllByText("Widget API");
  fireEvent.click(screen.getAllByRole("button", { name: /Open API source/ }).at(-1)!);
  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledWith("open_api_source", {
    source_id: ready.source_id,
    source_revision_id: ready.revision.revision_id,
  }));
  rendered.dispose();
});

it("offers explicit existing-or-new Agent continuation from an accepted API definition", async () => {
  const accepted = sourceView("accepted");
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    if (String(input) === "/api/sources") return jsonResponse([accepted]);
    throw new Error(`Unexpected request: ${String(input)}`);
  });
  const dispatchAffordance = vi.fn(async (id: string) => dispatchResult(id, "opened"));
  const rendered = await renderSourceHub(
    dispatchAffordance,
    new SourceClient({ fetch: fetchMock }),
  );

  expect(await screen.findByText("Choose how to continue the Agent setup")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Use an existing Agent" }));
  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledWith(
    "open_agent_inventory", {},
  ));
  rendered.dispose();

  const creationDispatch = vi.fn(async (id: string) => dispatchResult(id, "opened"));
  const creationRendered = await renderSourceHub(
    creationDispatch,
    new SourceClient({ fetch: fetchMock }),
  );
  expect(await screen.findByText("Choose how to continue the Agent setup")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Create a new Agent" }));
  await waitFor(() => expect(creationDispatch).toHaveBeenCalledWith(
    "open_agent_creation", {},
  ));
  creationRendered.dispose();
});


it("renders persisted semantic groups and inspects an exact recorded construction stage", async () => {
  const ready = sourceView("ready");
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/sources") return jsonResponse([ready]);
    if (url === "/api/sources/sourceopaque0001/graph") {
      return jsonResponse({
        source_id: "sourceopaque0001",
        revision_id: "revisionopaque01",
        assembler: "resource_first_v1",
        total_nodes: 2,
        total_edges: 1,
        nodes: [
          {
            id: "api_operation:catalog:listProducts",
            node_type: "api_operation",
            label: "GET /products",
            endpoint_id: "catalog:listProducts",
            facets: { method: "GET", operation_id: "listProducts", path: "/products" },
          },
          {
            id: "resource:products",
            node_type: "resource",
            label: "products",
            endpoint_id: null,
            facets: { resource: "products" },
          },
        ],
        edges: [
          {
            id: "api_operation:catalog:listProducts|exposes|resource:products",
            source: "api_operation:catalog:listProducts",
            target: "resource:products",
            type: "exposes",
            status: "observed",
            confidence: 0.95,
          },
        ],
        semantic_groups: [
          {
            id: "resource:products",
            label: "products",
            operation_ids: ["api_operation:catalog:listProducts"],
          },
        ],
        playback: [
          { id: "ingest", status: "pass", metrics: { endpoint_count: 1 }, warning_codes: [] },
          { id: "connect", status: "pass", metrics: { edge_count: 1 }, warning_codes: [] },
        ],
        trace: [
          {
            index: 0,
            event_type: "operation_added",
            active_endpoint_id: "catalog:listProducts",
            added_node_ids: ["api_operation:catalog:listProducts"],
            updated_node_ids: [],
            added_edge_ids: [],
            cumulative_nodes: 1,
            cumulative_edges: 0,
          },
          {
            index: 1,
            event_type: "resource_connected",
            active_endpoint_id: "catalog:listProducts",
            added_node_ids: ["resource:products"],
            updated_node_ids: [],
            added_edge_ids: ["api_operation:catalog:listProducts|exposes|resource:products"],
            cumulative_nodes: 2,
            cumulative_edges: 1,
          },
        ],
      });
    }
    throw new Error(`Unexpected request: ${url}`);
  });
  const dispatchAffordance = vi.fn(async (id: string) =>
    dispatchResult(id, id === "select_graph_stage" ? "selected" : "opened")
  );
  const rendered = await renderSourceHub(
    dispatchAffordance,
    new SourceClient({ fetch: fetchMock }),
  );

  expect(await screen.findByRole("heading", { name: "Semantic graph" })).toBeVisible();
  expect(await screen.findByRole("img", { name: "Semantic graph visualization" })).toBeVisible();
  expect(screen.getByText("ToolRouter graph construction")).toBeVisible();
  expect(screen.getByText("Complete persisted graph · no sampling")).toBeVisible();
  expect(screen.getByRole("button", { name: "Accumulated graph" })).toBeVisible();
  expect(screen.getByRole("button", { name: "Operation neighborhood" })).toBeVisible();
  expect(screen.getByRole("button", { name: "Open graph full screen" })).toBeVisible();
  expect(screen.getByText("2 seconds per frame at 1×")).toBeVisible();
  expect(screen.getByRole("button", { name: "Previous construction event" })).toBeVisible();
  expect(screen.getByRole("button", { name: "Play construction replay" })).toBeVisible();
  expect(screen.getByLabelText("Construction event")).toHaveValue("1");
  expect(await screen.findByText("2 nodes · 1 edges · resource_first_v1")).toBeVisible();
  expect(screen.getByRole("button", { name: "products1" })).toBeVisible();
  expect(screen.getByText("listProducts")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "2. connect" }));
  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledWith(
    "select_graph_stage",
    {
      source_id: ready.source_id,
      revision_id: ready.revision.revision_id,
      stage_id: "connect",
    },
  ));
  expect(await screen.findByText("edge count")).toBeVisible();
  rendered.dispose();
});


it("sends API secrets only through the private form and dispatches an empty operation payload", async () => {
  const ready = sourceView("ready");
  const secret = "source-private-api-key";
  let connectionReads = 0;
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/sources") return jsonResponse([ready]);
    if (url === "/api/sources/sourceopaque0001/graph") {
      return jsonResponse(emptyGraph());
    }
    if (url === "/api/sources/sourceopaque0001/connections") {
      connectionReads += 1;
      return jsonResponse(connectionReads === 1 ? [] : [{
        id: "connectionopaque1",
        source_id: "sourceopaque0001",
        revision_id: "revisionopaque01",
        profile_name: "Production",
        environment: "production",
        base_url: "https://api.example.com/v1",
        authentication_method: "api_key",
        credential_name: "X-API-Key",
        credential_reference_id: "00000000-0000-0000-0000-000000000004",
        credential_version: 1,
        created_at: "2026-08-07T10:00:00Z",
        updated_at: "2026-08-07T10:00:00Z",
      }]);
    }
    throw new Error(`Unexpected request: ${url}`);
  });
  const dispatchAffordance = vi.fn(async (id: string, value: unknown) =>
    dispatchResult(id, id === "save_api_connection" ? "saved" : "opened")
  );
  const rendered = await renderSourceHub(
    dispatchAffordance,
    new SourceClient({ fetch: fetchMock }),
  );

  expect(await screen.findByRole("heading", { name: "API connections" })).toBeVisible();
  fireEvent.change(screen.getByLabelText("Profile name"), { target: { value: "Production" } });
  fireEvent.change(screen.getByLabelText("Environment"), { target: { value: "production" } });
  fireEvent.change(screen.getByLabelText("Base URL"), { target: { value: "https://api.example.com/v1" } });
  fireEvent.change(screen.getByLabelText("Authentication"), { target: { value: "api_key" } });
  fireEvent.change(screen.getByLabelText("Header name"), { target: { value: "X-API-Key" } });
  fireEvent.change(screen.getByLabelText("API key"), { target: { value: secret } });
  fireEvent.click(screen.getByRole("button", { name: "Save connection" }));

  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledWith("save_api_connection", {}));
  expect(rendered.client.privateFormSaves.at(-1)).toMatchObject({
    formId: "sources-api-connection",
    request: {
      complete: true,
      value: {
        source_id: "sourceopaque0001",
        profile_name: "Production",
        environment: "production",
        base_url: "https://api.example.com/v1",
        authentication_method: "api_key",
        credential_name: "X-API-Key",
        credential_value: secret,
      },
    },
  });
  expect(JSON.stringify(dispatchAffordance.mock.calls)).not.toContain(secret);
  expect(JSON.stringify(fetchMock.mock.calls)).not.toContain(secret);
  expect(await screen.findByText(
    "Saved profile metadata is tied to this API version. Credentials remain protected. No connection check was run.",
  )).toBeVisible();
  expect(screen.getByText("Protected api key · credential v1")).toBeVisible();
  rendered.dispose();
});


it("attaches the exact ready Source through the retained Agent handoff", async () => {
  const ready = sourceView("ready");
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/sources") return jsonResponse([ready]);
    if (url.endsWith("/graph")) return jsonResponse(emptyGraph());
    if (url.endsWith("/connections")) return jsonResponse([]);
    throw new Error(`Unexpected request: ${url}`);
  });
  const dispatchAffordance = vi.fn(async (id: string) =>
    dispatchResult(id, id === "attach_created_source" ? "attached" : "opened")
  );
  const rendered = await renderSourceHub(
    dispatchAffordance,
    new SourceClient({ fetch: fetchMock }),
    {
      form_handle: "sources-api-connection",
      return_agent_ref: "agent-canonical-001",
      agent_handoff_mode: "create",
      selected_source_id: ready.source_id,
    },
  );

  fireEvent.click(await screen.findByRole("button", { name: "Attach and return to Agent" }));
  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledWith(
    "attach_created_source",
    { agent_ref: "agent-canonical-001", source_id: ready.source_id },
  ));
  rendered.dispose();
});


it("prepares the exact selected ready revision without an API execution request", async () => {
  const ready = sourceView("ready");
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/sources") return jsonResponse([ready]);
    if (url.endsWith("/graph")) return jsonResponse(emptyGraph());
    if (url.endsWith("/connections")) return jsonResponse([]);
    throw new Error(`Unexpected request: ${url}`);
  });
  const dispatchAffordance = vi.fn(async (id: string) =>
    dispatchResult(id, id === "propose_contract_revision" ? "proposed" : "opened")
  );
  const rendered = await renderSourceHub(
    dispatchAffordance,
    new SourceClient({ fetch: fetchMock }),
  );

  fireEvent.click(await screen.findByRole("button", { name: "Review API changes" }));
  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledWith(
    "propose_contract_revision",
    { source_id: ready.source_id, revision_id: ready.revision.revision_id },
  ));
  expect(fetchMock.mock.calls.every(([input]) => !String(input).includes("execute"))).toBe(true);
  rendered.dispose();
});


it("dispatches one exact safe check and renders only redacted persisted evidence", async () => {
  const ready = sourceView("ready", true);
  const secret = "must-never-reach-safe-check-ui";
  let checkReads = 0;
  const profile = {
    id: "connectionopaque1",
    source_id: ready.source_id,
    revision_id: ready.revision.revision_id,
    profile_name: "Local Medusa",
    environment: "local",
    base_url: "http://host.docker.internal:9100",
    authentication_method: "api_key",
    credential_name: "x-publishable-api-key",
    credential_reference_id: "00000000-0000-0000-0000-000000000004",
    credential_version: 1,
    created_at: "2026-08-07T10:00:00Z",
    updated_at: "2026-08-07T10:00:00Z",
  };
  const check = {
    id: "connectioncheck01",
    execution_id: "executioncheck01",
    source_id: ready.source_id,
    source_revision_id: ready.revision.revision_id,
    connection_profile_id: profile.id,
    credential_reference_id: profile.credential_reference_id,
    credential_version: 1,
    operation_id: "GetProductTags",
    method: "GET",
    path_template: "/store/product-tags",
    effective_contract_sha256: "6fca793be700dfb8bf511c2217d72cf97abf2f6cba08fbc2cd26ef0369b8f3f6",
    status: "succeeded",
    status_code: 200,
    error_code: null,
    public_message: null,
    validation_issue_count: 0,
    validation_phases: [],
    http_call_count: 1,
    started_at: "2026-08-07T10:00:00Z",
    finished_at: "2026-08-07T10:00:01Z",
    traces: [{ event: "execution_succeeded", occurred_at: "2026-08-07T10:00:01Z", safe_details: { status_code: 200 } }],
  };
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/sources") return jsonResponse([ready]);
    if (url.endsWith("/graph")) return jsonResponse(emptyGraph());
    if (url.endsWith("/connections")) return jsonResponse([profile]);
    if (url.includes("/connection-checks?revision_id=")) {
      checkReads += 1;
      return jsonResponse(checkReads === 1 ? [] : [check]);
    }
    throw new Error(`Unexpected request: ${url}`);
  });
  const dispatchAffordance = vi.fn(async (id: string) =>
    dispatchResult(id, id === "test_api_connection" ? "checked" : "opened")
  );
  const rendered = await renderSourceHub(
    dispatchAffordance,
    new SourceClient({ fetch: fetchMock }),
  );

  expect(await screen.findByRole("heading", { name: "Test API connection" })).toBeVisible();
  const testConnection = await screen.findByRole("button", { name: "Test connection" });
  fireEvent.change(screen.getByLabelText("Safe check operation"), {
    target: { value: "GetProductTags" },
  });
  fireEvent.click(testConnection);
  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledWith(
    "test_api_connection",
    {
      source_id: ready.source_id,
      source_revision_id: ready.revision.revision_id,
      connection_profile_id: profile.id,
      operation_id: "GetProductTags",
    },
  ));
  expect(await screen.findByText("Connection check succeeded")).toBeVisible();
  expect(screen.getByText("GetProductTags · GET /store/product-tags")).toBeVisible();
  expect(screen.getByText("6fca793be700…")).toBeVisible();
  expect(screen.getByText("Saved profile metadata and redacted check history are tied to this API version. Credentials remain protected.")).toBeVisible();
  expect(screen.queryByText("Saved profile metadata is tied to this API version. Credentials remain protected. No connection check was run.")).not.toBeInTheDocument();
  expect(JSON.stringify(dispatchAffordance.mock.calls)).not.toContain(secret);
  expect(document.body.textContent).not.toContain(secret);
  rendered.dispose();
});


async function renderSourceHub(
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"],
  sourceClient: SourceClient,
  values: RouteDeckSurfaceComponentProps["props"] = {},
  view: "hub" | "api" = "api",
) {
  sourceClient.selectConversation("conversation-test-01");
  return renderRouteDeckComponent(
    <PrivateFormGate formId="sources-api-connection">
      {(privateForm) => (
        <SourceHubSurface
          {...surfaceProps(dispatchAffordance, values)}
          sourceClient={sourceClient}
          privateForm={privateForm}
          contractRevisionStore={new ContractRevisionStore(sourceClient)}
          view={view}
        />
      )}
    </PrivateFormGate>,
    {
      contract: frameworkContractFixture(),
      projection: frameworkProjectionFixture(),
    },
  );
}


function emptyGraph() {
  return {
    source_id: "sourceopaque0001",
    revision_id: "revisionopaque01",
    assembler: "resource_first_v1",
    total_nodes: 0,
    total_edges: 0,
    nodes: [],
    edges: [],
    semantic_groups: [],
    playback: [],
    trace: [],
  };
}


function surfaceProps(
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"],
  values: RouteDeckSurfaceComponentProps["props"] = {},
): RouteDeckSurfaceComponentProps {
  return {
    surface: { surface_id: "sources.home", component: "sources.home", props: [] },
    slot: "active",
    props: values,
    spec: {
      id: "sources.home",
      component: "sources.home",
      lifecycle: "stable",
      public_props_schema: {},
      affordances: [
        { id: "open_api_creation", event: "open", operation: { id: "sources.open_api_creation" } },
        { id: "open_api_source", event: "open", operation: { id: "sources.open_api_source" } },
        { id: "return_to_source_hub", event: "open", operation: { id: "sources.return_to_source_hub" } },
        { id: "accept_staged_api", event: "submit", operation: { id: "sources.accept_staged_api" } },
        { id: "process_api", event: "submit", operation: { id: "sources.process_api" } },
        { id: "retry_processing", event: "submit", operation: { id: "sources.retry_processing" } },
        { id: "select_graph_stage", event: "select", operation: { id: "sources.select_graph_stage" } },
        { id: "save_api_connection", event: "submit", operation: { id: "sources.save_api_connection" } },
        { id: "test_api_connection", event: "submit", operation: { id: "sources.test_api_connection" } },
        { id: "propose_contract_revision", event: "submit", operation: { id: "sources.propose_contract_revision" } },
        { id: "return_to_home", event: "open", operation: { id: "sources.return_to_home" } },
        { id: "attach_created_source", event: "submit", operation: { id: "agents.attach_created_source" } },
        { id: "return_to_agent", event: "open", operation: { id: "agents.return_from_source" } },
      ],
    },
    dispatchAffordance,
  };
}


function sourceView(state: "accepted" | "queued" | "ready" | "failed", reviewed = false) {
  return {
    source_id: "sourceopaque0001",
    connector_key: "api",
    display_name: "Widget API",
    created_at: "2026-08-07T10:00:00Z",
    updated_at: "2026-08-07T10:00:05Z",
    revision: {
      schema_version: 1,
      revision_id: "revisionopaque01",
      source_id: "sourceopaque0001",
      original_filename: "widgets.yaml",
      content_sha256: "a".repeat(64),
      description_filename: "widgets.md",
      description_sha256: "b".repeat(64),
      job_id: "00000000-0000-0000-0000-000000000003",
      state,
      created_at: "2026-08-07T10:00:00Z",
      updated_at: "2026-08-07T10:00:05Z",
      summary: reviewed ? {
        revision_kind: "reviewed_api_contract",
        final_canonical_sha256: "6fca793be700dfb8bf511c2217d72cf97abf2f6cba08fbc2cd26ef0369b8f3f6",
      } : {},
      failure_code: state === "failed" ? "source_processing_failed" : null,
      failure_message: state === "failed" ? "ToolRouter rejected the definition." : null,
    },
  };
}


function jsonResponse(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}


function dispatchResult(operationId: string, outcome: string): RouteDeckDispatchResult {
  return {
    disposition: "completed",
    operation_id: operationId,
    request_id: "source-hub-test",
    session_version: 2,
    projection_version: 2,
    evidence: {
      source: "surface",
      phases: ["received", "completed"],
      attempt_id: "attempt-sources",
      request_fingerprint: "fingerprint-sources",
      delivery_phase: "response_received",
      result_id: "result-sources",
      result_fingerprint: "result-fingerprint-sources",
    },
    review: null,
    outcome,
    failure: null,
  };
}
