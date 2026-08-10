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
  const queued = sourceView("queued");
  const failed = sourceView("failed");
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/sources" && (init?.method ?? "GET") === "GET") {
      listCount += 1;
      return jsonResponse(listCount === 1 ? [] : [failed]);
    }
    if (url === "/api/sources/api" && init?.method === "POST") {
      const body = init.body as FormData;
      expect(body.get("file")).toMatchObject({ name: "widgets.yaml" });
      expect(body.get("description")).toMatchObject({ name: "widgets.md" });
      return jsonResponse(queued, 201);
    }
    throw new Error(`Unexpected request: ${init?.method ?? "GET"} ${url}`);
  });
  const dispatchAffordance = vi.fn(async (id: string) =>
    dispatchResult(id, id === "retry_processing" ? "queued" : "opened")
  );
  const rendered = await renderSourceHub(
    dispatchAffordance,
    new SourceClient({ fetch: fetchMock }),
  );

  expect(await screen.findByText("No API sources yet.")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Add API source" }));
  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledWith("open_api_creation", {}));
  fireEvent.change(screen.getByLabelText("Source name"), { target: { value: "Widget API" } });
  fireEvent.change(screen.getByLabelText("OpenAPI or Swagger definition"), {
    target: { files: [new File(["openapi: 3.0.3"], "widgets.yaml", { type: "application/yaml" })] },
  });
  fireEvent.change(screen.getByLabelText("Markdown description (optional)"), {
    target: { files: [new File(["# Widgets"], "widgets.md", { type: "text/markdown" })] },
  });
  fireEvent.submit(
    screen.getByRole("button", { name: "Upload and process" }).closest("form")!,
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
  const graph = screen.getByRole("img", { name: "Semantic graph visualization" });
  await waitFor(() => {
    expect(graph.querySelector("rect")).not.toBeNull();
    expect(graph.textContent).toContain("GET /products");
    expect(graph.textContent).toContain("api operation");
  });
  expect(screen.getByText(/selected semantic group and its direct relationships/)).toBeVisible();
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
    "Saved profile metadata is revision-bound. Credentials remain protected. No connection check was run.",
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

  fireEvent.click(await screen.findByRole("button", { name: "Prepare contract revision" }));
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
  expect(screen.getByText("Saved profile metadata and redacted check history are revision-bound. Credentials remain protected.")).toBeVisible();
  expect(screen.queryByText("Saved profile metadata is revision-bound. Credentials remain protected. No connection check was run.")).not.toBeInTheDocument();
  expect(JSON.stringify(dispatchAffordance.mock.calls)).not.toContain(secret);
  expect(document.body.textContent).not.toContain(secret);
  rendered.dispose();
});


async function renderSourceHub(
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"],
  sourceClient: SourceClient,
  values: RouteDeckSurfaceComponentProps["props"] = {},
) {
  return renderRouteDeckComponent(
    <PrivateFormGate formId="sources-api-connection">
      {(privateForm) => (
        <SourceHubSurface
          {...surfaceProps(dispatchAffordance, values)}
          sourceClient={sourceClient}
          privateForm={privateForm}
          contractRevisionStore={new ContractRevisionStore(sourceClient)}
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


function sourceView(state: "queued" | "ready" | "failed", reviewed = false) {
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
