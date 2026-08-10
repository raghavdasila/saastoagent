import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import type { RouteDeckDispatchResult } from "@routedeck/core";
import { expect, it, vi } from "vitest";

import { ApiOperationCurationPanel } from "../features/sources/ApiOperationCurationPanel";
import { SourceClient } from "../features/sources/sourceClient";


it("requires every exact operation decision and saves immutable revision-bound curation", async () => {
  let reads = 0;
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    expect(String(input)).toContain("/api/sources/sourceopaque0001/operation-curation?revision_id=revisionopaque01");
    reads += 1;
    return jsonResponse(curation(reads > 1));
  });
  const dispatchAffordance = vi.fn(async () => dispatchResult("saved"));
  render(
    <ApiOperationCurationPanel
      sourceId="sourceopaque0001"
      sourceRevisionId="revisionopaque01"
      sourceClient={new SourceClient({ fetch: fetchMock })}
      dispatchAffordance={dispatchAffordance}
    />,
  );

  expect(await screen.findByRole("heading", { name: "API operation curation" })).toBeVisible();
  const save = screen.getByRole("button", { name: "Save operation selection" });
  expect(save).toBeDisabled();
  expect(screen.getByText("2 operations still need an explicit decision.")).toBeVisible();

  fireEvent.change(screen.getByLabelText("Filter operations"), {
    target: { value: "create" },
  });
  expect(screen.getByText("createWidget")).toBeVisible();
  expect(screen.queryByText("listWidgets")).not.toBeInTheDocument();
  fireEvent.click(within(screen.getByText("createWidget").closest("li")!).getByRole("radio", { name: "Exclude" }));
  fireEvent.change(screen.getByLabelText("Filter operations"), { target: { value: "" } });
  fireEvent.click(within(screen.getByText("listWidgets").closest("li")!).getByRole("radio", { name: "Include" }));

  expect(screen.getByText("Every discovered operation is explicitly classified.")).toBeVisible();
  fireEvent.click(save);
  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledWith(
    "save_api_operation_curation",
    {
      source_id: "sourceopaque0001",
      source_revision_id: "revisionopaque01",
      inventory_fingerprint: "a".repeat(64),
      included_operation_ids: ["listWidgets"],
      excluded_operation_ids: ["createWidget"],
      expected_current_curation_id: null,
    },
  ));
  expect(await screen.findByText(
    "Saved 1 included and 1 excluded operations for this exact revision.",
  )).toBeVisible();
  expect(screen.getByText("1", { selector: ".api-curation-identity dd" })).toBeVisible();
  expect(fetchMock).toHaveBeenCalledTimes(2);
});


it("keeps the authoritative saved selection visible after a stale save failure", async () => {
  const current = curation(true);
  const fetchMock = vi.fn(async () => jsonResponse(current));
  const dispatchAffordance = vi.fn(async () => ({
    ...dispatchResult(null),
    disposition: "failed" as const,
    failure: {
      kind: "guard",
      code: "api_operation_curation_selection_stale",
      public_message: "The discovered operation inventory changed. Refresh it before saving.",
    },
  } as unknown as RouteDeckDispatchResult));
  render(
    <ApiOperationCurationPanel
      sourceId="sourceopaque0001"
      sourceRevisionId="revisionopaque01"
      sourceClient={new SourceClient({ fetch: fetchMock })}
      dispatchAffordance={dispatchAffordance}
    />,
  );

  expect(await screen.findByText("Every discovered operation is explicitly classified.")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Save operation selection" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "The discovered operation inventory changed. Refresh it before saving.",
  );
  expect(dispatchAffordance).toHaveBeenCalledWith(
    "save_api_operation_curation",
    expect.objectContaining({ expected_current_curation_id: "curationopaque01" }),
  );
  expect(fetchMock).toHaveBeenCalledTimes(2);
});


it("ignores an out-of-order response from the previously selected Source revision", async () => {
  const oldResponse = deferred<Response>();
  const newResponse = deferred<Response>();
  const fetchMock = vi.fn((input: RequestInfo | URL) =>
    String(input).includes("sourceopaque0001") ? oldResponse.promise : newResponse.promise
  );
  const props = {
    sourceClient: new SourceClient({ fetch: fetchMock }),
    dispatchAffordance: vi.fn(async () => dispatchResult("saved")),
  };
  const { rerender } = render(
    <ApiOperationCurationPanel
      {...props}
      sourceId="sourceopaque0001"
      sourceRevisionId="revisionopaque01"
    />,
  );
  rerender(
    <ApiOperationCurationPanel
      {...props}
      sourceId="sourceopaque0002"
      sourceRevisionId="revisionopaque02"
    />,
  );

  newResponse.resolve(jsonResponse(curationFor("sourceopaque0002", "revisionopaque02", "newOperation")));
  expect(await screen.findByText("newOperation")).toBeVisible();
  oldResponse.resolve(jsonResponse(curationFor("sourceopaque0001", "revisionopaque01", "oldOperation")));
  await waitFor(() => expect(screen.queryByText("oldOperation")).not.toBeInTheDocument());
  expect(screen.getByText("revisionopaque02")).toBeVisible();
});


it("serializes manual refresh and save so their authoritative refetches cannot overlap", async () => {
  const refreshResponse = deferred<Response>();
  const saveResult = deferred<RouteDeckDispatchResult>();
  let reads = 0;
  const fetchMock = vi.fn(async () => {
    reads += 1;
    if (reads === 1) return jsonResponse(curation(true));
    if (reads === 2) return refreshResponse.promise;
    return jsonResponse(curation(true));
  });
  const dispatchAffordance = vi.fn(() => saveResult.promise);
  render(
    <ApiOperationCurationPanel
      sourceId="sourceopaque0001"
      sourceRevisionId="revisionopaque01"
      sourceClient={new SourceClient({ fetch: fetchMock })}
      dispatchAffordance={dispatchAffordance}
    />,
  );
  expect(await screen.findByText("Every discovered operation is explicitly classified.")).toBeVisible();
  const refreshButton = screen.getByRole("button", { name: "Refresh inventory" });
  const saveButton = screen.getByRole("button", { name: "Save operation selection" });

  fireEvent.click(refreshButton);
  expect(refreshButton).toBeDisabled();
  expect(saveButton).toBeDisabled();
  fireEvent.click(saveButton);
  expect(dispatchAffordance).not.toHaveBeenCalled();
  refreshResponse.resolve(jsonResponse(curation(true)));
  await waitFor(() => expect(refreshButton).toBeEnabled());

  fireEvent.click(saveButton);
  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledTimes(1));
  expect(refreshButton).toBeDisabled();
  fireEvent.click(refreshButton);
  expect(fetchMock).toHaveBeenCalledTimes(2);
  saveResult.resolve(dispatchResult("saved"));
});


function curation(saved: boolean) {
  const record = {
    schema_version: 1,
    id: "curationopaque01",
    source_id: "sourceopaque0001",
    source_revision_id: "revisionopaque01",
    artifact_revision_id: "artifactopaque01",
    inventory_fingerprint: "a".repeat(64),
    included_operation_ids: ["listWidgets"],
    excluded_operation_ids: ["createWidget"],
    selected_by_owner_id: "00000000-0000-0000-0000-000000000001",
    selected_at: "2026-08-08T08:00:00Z",
    previous_curation_id: null,
  };
  return {
    source_id: "sourceopaque0001",
    source_revision_id: "revisionopaque01",
    artifact_revision_id: "artifactopaque01",
    inventory_fingerprint: "a".repeat(64),
    operations: [
      { operation_id: "listWidgets", graph_node_id: "operation:listWidgets", method: "GET", path_template: "/widgets", operation_class: "list" },
      { operation_id: "createWidget", graph_node_id: "operation:createWidget", method: "POST", path_template: "/widgets", operation_class: "create" },
    ],
    current: saved ? record : null,
    history: saved ? [record] : [],
  };
}


function curationFor(sourceId: string, revisionId: string, operationId: string) {
  return {
    source_id: sourceId,
    source_revision_id: revisionId,
    artifact_revision_id: revisionId,
    inventory_fingerprint: "b".repeat(64),
    operations: [
      { operation_id: operationId, graph_node_id: `operation:${operationId}`, method: "GET", path_template: "/widgets", operation_class: "list" },
    ],
    current: null,
    history: [],
  };
}


function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((next) => {
    resolve = next;
  });
  return { promise, resolve };
}


function dispatchResult(outcome: string | null): RouteDeckDispatchResult {
  return {
    disposition: "completed",
    operation_id: "sources.save_api_operation_curation",
    request_id: "source-curation-test",
    session_version: 2,
    projection_version: 2,
    evidence: {
      source: "surface",
      phases: ["received", "completed"],
      attempt_id: "attempt-curation",
      request_fingerprint: "fingerprint-curation",
      delivery_phase: "response_received",
      result_id: "result-curation",
      result_fingerprint: "result-fingerprint-curation",
    },
    review: null,
    outcome,
    failure: null,
  };
}


function jsonResponse(value: unknown): Response {
  return new Response(JSON.stringify(value), {
    status: 200,
    headers: { "Content-Type": "application/json" },
  });
}
