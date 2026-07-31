import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { RouteDeckDispatchResult } from "@routedeck/core";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { expect, it, vi } from "vitest";

import { SourceDebugSurface } from "../features/sources/SourceDebugSurface";
import { SourceClient } from "../features/sources/sourceClient";


it("exercises API upload, retrieval, evalset generation, and RouteDeck return", async () => {
  const source = sourceView();
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/sources" && (init?.method ?? "GET") === "GET") {
      return jsonResponse([]);
    }
    if (url === "/api/sources/api" && init?.method === "POST") {
      expect(init.body).toBeInstanceOf(FormData);
      expect((init.body as FormData).get("file")).toMatchObject({
        name: "widgets.yaml",
        type: "application/yaml",
      });
      return jsonResponse(source, 201);
    }
    if (url.endsWith("/retrieve") && init?.method === "POST") {
      return jsonResponse({
        query: "list widgets",
        decision_type: "ROUTE",
        decision_reason: "one endpoint is sufficiently supported",
        decomposed: false,
        missing_inputs: [],
        ambiguity: null,
        decision_evidence: {},
        steps: [{
          query: "list widgets",
          ranked_items: [{ item_id: "widgets:listWidgets", item_kind: "api_operation", score: 0.91 }],
          trace: { trace_mode: "bounded" },
        }],
      });
    }
    if (url.endsWith("/evalsets") && init?.method === "POST") {
      return jsonResponse({
        evalset_id: "api-debug-v1",
        status: "ready",
        completed_count: 1,
        expected_count: 1,
        accepted_count: 1,
        quarantined_count: 0,
        terminal_status_counts: { accepted: 1 },
        offline_tokens: 320,
        generator_model: "gemma4:latest",
        generator_model_digest: "generator-digest",
        reviewer_model: "qwen2.5-coder:7b",
        reviewer_model_digest: "reviewer-digest",
        accepted_tasks: [{ query: "Show all available widgets" }],
        summary: {},
      });
    }
    throw new Error(`Unexpected request: ${init?.method ?? "GET"} ${url}`);
  });
  vi.stubGlobal("fetch", fetchMock);
  const dispatchAffordance = vi.fn(async () => dispatchResult());
  render(
    <SourceDebugSurface
      {...surfaceProps(dispatchAffordance)}
      sourceClient={new SourceClient({ fetch: fetchMock })}
    />,
  );

  expect(await screen.findByText("No API sources uploaded yet.")).toBeVisible();
  expect(screen.getByRole("region", { name: "API connector ToolRouter pipeline" })).toBeVisible();
  expect(screen.getByText("Upload a collection to begin")).toBeVisible();
  expect(screen.getByLabelText("OpenAPI collection")).toHaveAttribute(
    "accept",
    expect.stringContaining(".yaml"),
  );
  fireEvent.change(screen.getByLabelText("Source name"), {
    target: { value: "Widget API" },
  });
  fireEvent.change(screen.getByLabelText("OpenAPI collection"), {
    target: {
      files: [new File(["openapi: 3.0.0"], "widgets.yaml", { type: "application/yaml" })],
    },
  });
  fireEvent.submit(
    screen.getByRole("button", { name: "Upload and build graph" }).closest("form")!,
  );

  expect(await screen.findByRole("button", { name: /Widget API/ })).toBeVisible();
  expect(screen.getByText("Graph and index ready")).toBeVisible();
  fireEvent.change(screen.getByLabelText("Retrieval query"), {
    target: { value: "list widgets" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Run retrieval" }));
  expect(await screen.findByText("ROUTE")).toBeVisible();
  expect(screen.getByText("widgets:listWidgets")).toBeVisible();
  expect(screen.getByText("Retrieval complete")).toBeVisible();

  fireEvent.click(screen.getByRole("button", { name: "Generate evalset" }));
  expect(await screen.findByText("1 accepted / 1 completed")).toBeVisible();
  expect(screen.getByText("Evalset ready")).toBeVisible();

  fireEvent.click(screen.getByRole("button", { name: "Back to Home" }));
  await waitFor(() => {
    expect(dispatchAffordance).toHaveBeenCalledWith("return_to_home", {});
  });
});


function surfaceProps(
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"],
): RouteDeckSurfaceComponentProps {
  return {
    surface: { surface_id: "sources.debug", component: "sources.debug", props: [] },
    slot: "active",
    props: {},
    spec: {
      id: "sources.debug",
      component: "sources.debug",
      lifecycle: "stable",
      public_props_schema: {},
      affordances: [{
        id: "return_to_home",
        event: "open",
        operation: { id: "sources.return_to_home" },
      }],
    },
    dispatchAffordance,
  };
}


function sourceView() {
  return {
    source_id: "source-opaque-1",
    connector_key: "api",
    display_name: "Widget API",
    created_at: "2026-07-23T10:00:00Z",
    updated_at: "2026-07-23T10:00:05Z",
    revision: {
      schema_version: 1,
      revision_id: "revision-opaque-1",
      source_id: "source-opaque-1",
      original_filename: "widgets.yaml",
      content_sha256: "a".repeat(64),
      state: "ready",
      created_at: "2026-07-23T10:00:00Z",
      updated_at: "2026-07-23T10:00:05Z",
      summary: {
        endpoint_count: 3,
        graph_node_count: 12,
        graph_edge_count: 18,
        graph_card_count: 12,
      },
      failure_code: null,
      failure_message: null,
    },
  };
}


function jsonResponse(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}


function dispatchResult(): RouteDeckDispatchResult {
  return {
    disposition: "completed" as const,
    operation_id: "sources.return_to_home",
    request_id: "source-debug-test",
    session_version: 2,
    projection_version: 2,
    evidence: {
      source: "surface" as const,
      phases: ["received", "completed"],
      attempt_id: "attempt-sources",
      request_fingerprint: "fingerprint-sources",
      delivery_phase: "response_received" as const,
      result_id: "result-sources",
      result_fingerprint: "result-fingerprint-sources",
    },
    review: null,
    outcome: "opened",
    failure: null,
  };
}
