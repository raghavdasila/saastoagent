import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { RouteDeckDispatchResult } from "@routedeck/core";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { expect, it, vi } from "vitest";

import {
  ApiOperationTestPanel,
  RoutedExecutionResult,
} from "../features/sources/ApiOperationTestPanel";
import { RoutedApiWriteReviewSurface } from "../features/sources/RoutedApiWriteReviewSurface";
import { RoutedExecutionStore } from "../features/sources/routedExecutionStore";
import {
  type ApiRoutedExecutionView,
  SourceClient,
} from "../features/sources/sourceClient";
import {
  frameworkContractFixture,
  frameworkProjectionFixture,
  renderRouteDeckComponent,
} from "./routeDeckHarness";

const SOURCE_ID = "sourceopaque0001";
const REVISION_ID = "revisionopaque01";
const PROFILE_ID = "profileopaque001";
const CURATION_ID = "curationopaque01";
const ACTIVE_PLANNER_PROPS = {
  open: true,
  source_id: SOURCE_ID,
  source_revision_id: REVISION_ID,
};

function conversationSourceClient(
  fetch: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>,
): SourceClient {
  const client = new SourceClient({ fetch });
  client.selectConversation("conversation-route-plan-tests");
  return client;
}

it("prepares and clarifies the same non-executing route-plan lineage", async () => {
  let currentPlan: ReturnType<typeof plan> | null = null;
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/sources") return jsonResponse([source()]);
    if (url.endsWith(`/${SOURCE_ID}/connections`)) return jsonResponse([profile()]);
    if (url.includes("/operation-curation?")) return jsonResponse(curation());
    if (url.includes("/route-plans/current?")) return jsonResponse(currentPlan);
    throw new Error(`Unexpected request: ${url}`);
  });
  const dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"] = vi.fn(async (
    affordanceId: string,
    args = {},
  ) => {
    if (affordanceId === "create_api_route_plan") {
      currentPlan = plan("needs_input");
      return completedPlanningDispatch("sources.create_api_route_plan", "planned");
    }
    expect(args).toEqual({ answer: "cus_123" });
    currentPlan = plan("ready", "recordopaque0002", "recordopaque0001");
    return completedPlanningDispatch("sources.continue_api_route_plan", "continued");
  });
  renderPanel(conversationSourceClient(fetchMock), ACTIVE_PLANNER_PROPS, dispatchAffordance);

  expect(await screen.findByRole("heading", { name: "API operation test" })).toBeVisible();
  expect(screen.getByText("Planning only; no API request has been sent.")).toBeVisible();
  expect(await screen.findByText(/Current curation curationopaque01/)).toBeVisible();
  fireEvent.change(screen.getByLabelText("What should Corpus route?"), {
    target: { value: "List orders for the selected customer" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Prepare route" }));

  expect(await screen.findByText("Waiting for one required value")).toBeVisible();
  expect(screen.getByText("External calls: 0")).toBeVisible();
  expect(screen.queryByText("ASK_PARAM")).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("What should Corpus use for customer_id?"), {
    target: { value: "cus_123" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Continue this plan" }));

  expect(await screen.findByText("Route ready for one explicit operation")).toBeVisible();
  expect(screen.getByText("List Orders")).toBeVisible();
  expect(dispatchAffordance).toHaveBeenNthCalledWith(1, "create_api_route_plan", {
    request_text: "List orders for the selected customer",
    profile_name: "Local Medusa",
    provided_inputs: {},
  });
  expect(dispatchAffordance).toHaveBeenNthCalledWith(2, "continue_api_route_plan", { answer: "cus_123" });
});

it("sends one explicit non-secret current-request input and renders its provenance", async () => {
  let currentPlan: ReturnType<typeof plan> | null = null;
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/sources") return jsonResponse([source()]);
    if (url.endsWith(`/${SOURCE_ID}/connections`)) return jsonResponse([profile()]);
    if (url.includes("/operation-curation?")) return jsonResponse(curation());
    if (url.includes("/route-plans/current?")) return jsonResponse(currentPlan);
    throw new Error(`Unexpected request: ${url}`);
  });
  const dispatchAffordance = vi.fn(async () => {
    currentPlan = {
      ...plan("ready"),
      input_provenance: [{ name: "customer_id", value: "cus_123", source: "current_request" as const }],
    };
    return completedPlanningDispatch("sources.create_api_route_plan", "planned");
  });
  renderPanel(conversationSourceClient(fetchMock), ACTIVE_PLANNER_PROPS, dispatchAffordance);

  await screen.findByText(/Current curation curationopaque01/);
  fireEvent.change(screen.getByLabelText("What should Corpus route?"), {
    target: { value: "List orders" },
  });
  fireEvent.change(screen.getByLabelText("Known input name (optional)"), {
    target: { value: "customer_id" },
  });
  fireEvent.change(screen.getByLabelText("Known input value (optional)"), {
    target: { value: "cus_123" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Prepare route" }));

  expect(await screen.findByText(/Route ready/)).toBeVisible();
  expect(screen.getByText("Current request")).toBeVisible();
  expect(screen.getByText("Managed by selected connection profile")).toBeVisible();
  expect(dispatchAffordance).toHaveBeenCalledWith("create_api_route_plan", {
    request_text: "List orders",
    profile_name: "Local Medusa",
    provided_inputs: { customer_id: "cus_123" },
  });
});

it("shows ambiguity without a selected operation and sends an exact typed choice", async () => {
  let currentPlan: ReturnType<typeof plan> | null = null;
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/sources") return jsonResponse([source()]);
    if (url.endsWith(`/${SOURCE_ID}/connections`)) return jsonResponse([profile()]);
    if (url.includes("/operation-curation?")) return jsonResponse(curation());
    if (url.includes("/route-plans/current?")) return jsonResponse(currentPlan);
    throw new Error(`Unexpected request: ${url}`);
  });
  const dispatchAffordance = vi.fn(async (affordanceId: string) => {
    if (affordanceId === "create_api_route_plan") {
      currentPlan = plan("needs_operation_choice");
      return completedPlanningDispatch("sources.create_api_route_plan", "planned");
    }
    currentPlan = {
        ...plan("ready", "recordopaque0002", "recordopaque0001"),
        operation_choice: { operation_id: "GetOrders", source: "user_clarification" },
    };
    return completedPlanningDispatch("sources.continue_api_route_plan", "continued");
  });
  renderPanel(conversationSourceClient(fetchMock), ACTIVE_PLANNER_PROPS, dispatchAffordance);

  await screen.findByText(/Current curation curationopaque01/);
  fireEvent.change(screen.getByLabelText("What should Corpus route?"), {
    target: { value: "Use the orders API" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Prepare route" }));

  expect(await screen.findByText("Waiting for an operation choice")).toBeVisible();
  expect(screen.getByText("No operation selected")).toBeVisible();
  fireEvent.change(screen.getByLabelText("Which of these included operations did you mean?"), {
    target: { value: "List Orders" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Continue this plan" }));

  expect(await screen.findByText(/Chosen operation List Orders/)).toBeVisible();
  expect(dispatchAffordance).toHaveBeenLastCalledWith("continue_api_route_plan", { answer: "List Orders" });
});

it("refetches and adopts the authoritative plan after a create conflict", async () => {
  let currentReads = 0;
  let authoritativePlan: ReturnType<typeof plan> | null = null;
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/sources") return jsonResponse([source()]);
    if (url.endsWith(`/${SOURCE_ID}/connections`)) return jsonResponse([profile()]);
    if (url.includes("/operation-curation?")) return jsonResponse(curation());
    if (url.includes("/route-plans/current?")) {
      currentReads += 1;
      return jsonResponse(authoritativePlan);
    }
    throw new Error(`Unexpected request: ${url}`);
  });
  const dispatchAffordance = vi.fn(async () => {
    authoritativePlan = plan("ready");
    return completedPlanningDispatch("sources.create_api_route_plan", "conflict");
  });
  renderPanel(conversationSourceClient(fetchMock), ACTIVE_PLANNER_PROPS, dispatchAffordance);

  await screen.findByText(/Current curation curationopaque01/);
  fireEvent.change(screen.getByLabelText("What should Corpus route?"), {
    target: { value: "List orders" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Prepare route" }));

  expect(await screen.findByText(/Route ready/)).toBeVisible();
  expect(currentReads).toBe(2);
});

it("selects only a profile bound to the exact selected revision", async () => {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/sources") return jsonResponse([source()]);
    if (url.endsWith(`/${SOURCE_ID}/connections`)) {
      return jsonResponse([{ ...profile(), id: "oldprofile000001", revision_id: "oldrevision0001" }, profile()]);
    }
    if (url.includes("/operation-curation?")) return jsonResponse(curation());
    if (url.includes("/route-plans/current?")) return jsonResponse(null);
    throw new Error(`Unexpected request: ${url}`);
  });
  renderPanel(conversationSourceClient(fetchMock));

  await screen.findByText(/Current curation curationopaque01/);
  const profileSelect = screen.getByLabelText("Saved connection profile");
  expect(profileSelect).toHaveValue(PROFILE_ID);
  expect(profileSelect.querySelectorAll("option")).toHaveLength(2);
});

it("renders nothing for an inactive stable detail surface", () => {
  renderPanel(conversationSourceClient(vi.fn()), {});
  expect(screen.queryByRole("heading", { name: "API operation test" })).toBeNull();
});

it("dispatches the exact ready read once and renders only its redacted retained result", async () => {
  let executed = false;
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/sources") return jsonResponse([source()]);
    if (url.endsWith(`/${SOURCE_ID}/connections`)) return jsonResponse([profile()]);
    if (url.includes("/operation-curation?")) return jsonResponse(curation());
    if (url.includes("/route-plans/current?")) return jsonResponse(plan("ready"));
    if (url.endsWith("/execution")) return jsonResponse(executed ? execution("read") : null);
    throw new Error(`Unexpected request: ${url}`);
  });
  const dispatchAffordance = vi.fn(async () => {
    executed = true;
    return completedExecutionDispatch("sources.test_routed_api_read");
  });
  renderPanel(conversationSourceClient(fetchMock), ACTIVE_PLANNER_PROPS, dispatchAffordance);

  fireEvent.click(await screen.findByRole("button", { name: "Run routed read" }));
  expect(await screen.findByText("Routed API request succeeded")).toBeVisible();
  expect(screen.getByText("response received")).toBeVisible();
  expect(screen.getByText("e".repeat(12))).toBeVisible();
  expect(dispatchAffordance).toHaveBeenCalledTimes(1);
  expect(dispatchAffordance).toHaveBeenCalledWith("run_routed_api_read", {
    plan_id: "planopaque000001",
  });
  expect(screen.queryByRole("button", { name: "Run routed read" })).toBeNull();
});

it("accepts the durable write review once and renders an unknown retained result without retry", async () => {
  let reads = 0;
  const client = conversationSourceClient(vi.fn(async (input: RequestInfo | URL) => {
    if (!String(input).endsWith("/execution")) throw new Error(`Unexpected request: ${String(input)}`);
    reads += 1;
    return jsonResponse(reads === 1 ? null : execution("write", "outcome_unknown"));
  }));
  const store = new RoutedExecutionStore(client);
  await store.select(SOURCE_ID, writePlan());
  const rendered = await renderRouteDeckComponent(
    <RoutedApiWriteReviewSurface
      {...writeReviewSurfaceProps()}
      store={store}
    />,
    {
      contract: frameworkContractFixture(),
      projection: frameworkProjectionFixture(),
      dispatchResult: unknownExecutionDispatch(),
    },
  );

  expect(screen.getByText("CreateCart")).toBeVisible();
  expect(screen.getByText("Acceptance makes exactly one attempt. Corpus will not retry automatically.")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Accept and send one write" }));
  expect(await screen.findByText("Routed API write outcome is unknown")).toBeVisible();
  expect(screen.getByRole("alert")).toHaveTextContent("Do not retry automatically");
  expect(screen.queryByRole("button", { name: "Accept and send one write" })).toBeDisabled();
  expect(reads).toBe(2);
  rendered.dispose();
});

it("rejects the durable write review without a routed result or API call", async () => {
  let reads = 0;
  const client = conversationSourceClient(vi.fn(async (input: RequestInfo | URL) => {
    if (!String(input).endsWith("/execution")) throw new Error(`Unexpected request: ${String(input)}`);
    reads += 1;
    return jsonResponse(null);
  }));
  const store = new RoutedExecutionStore(client);
  await store.select(SOURCE_ID, writePlan());
  const rendered = await renderRouteDeckComponent(
    <RoutedApiWriteReviewSurface {...writeReviewSurfaceProps()} store={store} />,
    {
      contract: frameworkContractFixture(),
      projection: frameworkProjectionFixture(),
      dispatchResult: reviewRejectedDispatch(),
    },
  );

  fireEvent.click(screen.getByRole("button", { name: "Reject without sending" }));
  await waitFor(() => expect(screen.getByRole("button", { name: "Reject without sending" })).toBeEnabled());
  expect(store.snapshot().result).toBeNull();
  expect(screen.queryByText(/Routed API request/)).toBeNull();
  expect(screen.queryByRole("alert")).toBeNull();
  expect(reads).toBe(1);
  rendered.dispose();
});

it("keeps the exact reloaded write plan and shows a stale accept failure without sending", async () => {
  let reads = 0;
  const client = conversationSourceClient(vi.fn(async (input: RequestInfo | URL) => {
    if (!String(input).endsWith("/execution")) throw new Error(`Unexpected request: ${String(input)}`);
    reads += 1;
    return jsonResponse(null);
  }));
  const store = new RoutedExecutionStore(client);
  await store.select(SOURCE_ID, writePlan());
  const rendered = await renderRouteDeckComponent(
    <RoutedApiWriteReviewSurface {...writeReviewSurfaceProps()} store={store} />,
    {
      contract: frameworkContractFixture(),
      projection: frameworkProjectionFixture(),
      dispatchResult: staleReviewDispatch(),
    },
  );

  expect(screen.getByText(/from plan/)).toHaveTextContent("planopaque000001");
  fireEvent.click(screen.getByRole("button", { name: "Accept and send one write" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "The exact route plan changed before approval. No API request was sent.",
  );
  expect(store.snapshot().result).toBeNull();
  expect(reads).toBe(2);
  rendered.dispose();
});

it("keeps the stale accept failure in the planner after the review projection tears down", async () => {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/sources") return jsonResponse([source()]);
    if (url.endsWith(`/${SOURCE_ID}/connections`)) return jsonResponse([profile()]);
    if (url.includes("/operation-curation?")) return jsonResponse(curation());
    if (url.includes("/route-plans/current?")) return jsonResponse(writePlan());
    if (url.endsWith("/execution")) return jsonResponse(null);
    throw new Error(`Unexpected request: ${url}`);
  });
  const client = conversationSourceClient(fetchMock);
  const store = new RoutedExecutionStore(client);
  await store.select(SOURCE_ID, writePlan());
  const panel = (
    <ApiOperationTestPanel
      {...surfaceProps(ACTIVE_PLANNER_PROPS, vi.fn())}
      sourceClient={client}
      executionStore={store}
    />
  );
  const rendered = await renderRouteDeckComponent(
    <>
      {panel}
      <RoutedApiWriteReviewSurface {...writeReviewSurfaceProps()} store={store} />
    </>,
    {
      contract: frameworkContractFixture(),
      projection: frameworkProjectionFixture(),
      dispatchResult: staleReviewDispatch(),
    },
  );

  fireEvent.click(await screen.findByRole("button", { name: "Accept and send one write" }));
  await waitFor(() => expect(store.snapshot().error).toBe(
    "The exact route plan changed before approval. No API request was sent.",
  ));
  rendered.rerender(panel);

  const planner = document.querySelector("section.api-routed-execution");
  expect(planner).not.toBeNull();
  expect(screen.getByRole("alert")).toHaveTextContent(
    "The exact route plan changed before approval. No API request was sent.",
  );
  expect(screen.queryByRole("button", { name: "Accept and send one write" })).toBeNull();
  expect(fetchMock.mock.calls.filter(([input]) => String(input).endsWith("/execution"))).toHaveLength(3);
  rendered.dispose();
});

it("renders an interrupted claim call count as explicitly unknown", () => {
  render(<RoutedExecutionResult result={{ ...execution("write", "outcome_unknown"), http_call_count: null }} />);
  expect(screen.getByText("Unknown after interruption")).toBeVisible();
});

it("surfaces possibly-sent read delivery without offering an automatic retry", () => {
  render(<RoutedExecutionResult result={{
    ...execution("read"),
    status: "failed",
    delivery: "possibly_sent",
    status_code: null,
    response_media_type: null,
    response_byte_count: 0,
    response_body_sha256: null,
    error_code: "transport_failed",
    outcome_verified: null,
  }} />);
  expect(screen.getByRole("alert")).toHaveTextContent("Delivery could not be confirmed");
  expect(screen.queryByRole("button")).toBeNull();
});

function source() {
  return {
    source_id: SOURCE_ID,
    connector_key: "api",
    display_name: "Medusa Store",
    created_at: "2026-08-08T08:00:00Z",
    updated_at: "2026-08-08T08:00:00Z",
    revision: {
      revision_id: REVISION_ID,
      source_id: SOURCE_ID,
      original_filename: "effective.json",
      content_sha256: "a".repeat(64),
      description_filename: null,
      description_sha256: null,
      job_id: null,
      state: "ready",
      created_at: "2026-08-08T08:00:00Z",
      updated_at: "2026-08-08T08:00:00Z",
      summary: {
        revision_kind: "reviewed_api_contract",
        final_canonical_sha256: "6fca793be700dfb8bf511c2217d72cf97abf2f6cba08fbc2cd26ef0369b8f3f6",
      },
      failure_code: null,
      failure_message: null,
      parent_revision_id: "parentopaque0001",
      artifact_revision_id: "artifactopaque01",
    },
  };
}

function renderPanel(
  client: SourceClient,
  props: RouteDeckSurfaceComponentProps["props"] = ACTIVE_PLANNER_PROPS,
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"] = vi.fn(),
) {
  return render(
    <ApiOperationTestPanel
      {...surfaceProps(props, dispatchAffordance)}
      sourceClient={client}
      executionStore={new RoutedExecutionStore(client)}
    />,
  );
}

function profile() {
  return {
    id: PROFILE_ID,
    source_id: SOURCE_ID,
    revision_id: REVISION_ID,
    profile_name: "Local Medusa",
    environment: "development",
    base_url: "http://127.0.0.1:9100",
    authentication_method: "api_key",
    credential_name: "x-publishable-api-key",
    credential_reference_id: "00000000-0000-0000-0000-000000000003",
    credential_version: 1,
    created_at: "2026-08-08T08:00:00Z",
    updated_at: "2026-08-08T08:00:00Z",
  };
}

function curation() {
  return {
    source_id: SOURCE_ID,
    source_revision_id: REVISION_ID,
    artifact_revision_id: "artifactopaque01",
    inventory_fingerprint: "b".repeat(64),
    operations: [{
      operation_id: "GetOrders",
      graph_node_id: "api_operation:medusa:GetOrders",
      method: "GET",
      path_template: "/store/orders",
      operation_class: "list",
    }],
    current: {
      schema_version: 1,
      id: CURATION_ID,
      source_id: SOURCE_ID,
      source_revision_id: REVISION_ID,
      artifact_revision_id: "artifactopaque01",
      inventory_fingerprint: "b".repeat(64),
      included_operation_ids: ["GetOrders"],
      excluded_operation_ids: [],
      selected_by_owner_id: "00000000-0000-0000-0000-000000000001",
      selected_at: "2026-08-08T08:00:00Z",
      previous_curation_id: null,
    },
    history: [],
  };
}

function plan(
  state: "needs_input" | "needs_operation_choice" | "ready",
  recordId = "recordopaque0001",
  previousRecordId: string | null = null,
): import("../features/sources/sourceClient").ApiRoutePlanView {
  return {
    plan_id: "planopaque000001",
    record_id: recordId,
    previous_record_id: previousRecordId,
    source_id: SOURCE_ID,
    source_revision_id: REVISION_ID,
    profile_id: PROFILE_ID,
    curation_id: CURATION_ID,
    inventory_fingerprint: "b".repeat(64),
    subset_fingerprint: "c".repeat(64),
    request_text: "List orders for the selected customer",
    state,
    steps: [{
      query: "List orders for the selected customer",
      ranked_operations: [{ operation_id: "GetOrders", operation_label: "List Orders", endpoint_id: "medusa:GetOrders", score: 0.95 }],
      selected_operation_id: state === "needs_operation_choice" ? null : "GetOrders",
      method: state === "needs_operation_choice" ? null : "GET",
      path_template: state === "needs_operation_choice" ? null : "/store/orders",
      http_safety: state === "needs_operation_choice" ? null : "read",
    }],
    missing_inputs: state === "needs_input" ? ["customer_id"] : [],
    input_provenance: state === "ready"
      ? [{ name: "customer_id", value: "cus_123", source: "user_clarification" }]
      : [],
    managed_parameters: [{
      name: "x-publishable-api-key",
      location: "header",
      authentication_method: "api_key",
      source: "managed_by_profile",
    }],
    operation_choice: null,
    clarification_prompt: state === "needs_input"
      ? "What should Corpus use for customer_id?"
      : state === "needs_operation_choice"
        ? "Which of these included operations did you mean?"
        : null,
    created_at: "2026-08-08T08:00:00Z",
    expires_at: "2026-08-08T08:30:00Z",
    plan_fingerprint: "d".repeat(64),
    api_call_count: 0,
  };
}

function writePlan() {
  const ready = plan("ready");
  return {
    ...ready,
    steps: [{
      ...ready.steps[0],
      selected_operation_id: "CreateCart",
      method: "POST",
      path_template: "/store/carts",
      http_safety: "write" as const,
    }],
  };
}

function execution(
  safety: "read" | "write",
  status: "succeeded" | "outcome_unknown" = "succeeded",
): ApiRoutedExecutionView {
  return {
    result_id: "resultopaque0001",
    plan_id: "planopaque000001",
    source_id: SOURCE_ID,
    source_revision_id: REVISION_ID,
    operation_id: safety === "read" ? "GetOrders" : "CreateCart",
    method: safety === "read" ? "GET" : "POST",
    path_template: safety === "read" ? "/store/orders" : "/store/carts",
    safety,
    status,
    delivery: status === "outcome_unknown" ? "possibly_sent" : "response_received",
    status_code: status === "outcome_unknown" ? null : 200,
    response_media_type: status === "outcome_unknown" ? null : "application/json",
    response_byte_count: status === "outcome_unknown" ? 0 : 42,
    response_body_sha256: status === "outcome_unknown" ? null : "e".repeat(64),
    error_code: status === "outcome_unknown" ? "transport_outcome_unknown" : null,
    public_message: null,
    validation_issue_count: 0,
    validation_phases: [],
    outcome_verified: safety === "read" && status === "succeeded" ? true : null,
    http_call_count: 1,
    started_at: "2026-08-08T08:00:00Z",
    finished_at: "2026-08-08T08:00:01Z",
    traces: [],
  };
}

function completedExecutionDispatch(operationId: string): RouteDeckDispatchResult {
  return {
    disposition: "completed" as const,
    operation_id: operationId,
    request_id: "routed-execution-test",
    session_version: 2,
    projection_version: 2,
    evidence: {
      source: "surface" as const,
      phases: ["received", "completed"],
      attempt_id: "attempt-routed",
      request_fingerprint: "fingerprint-routed",
      delivery_phase: "response_received" as const,
      result_id: "result-routed",
      result_fingerprint: "result-fingerprint-routed",
    },
    review: null,
    outcome: "observed",
    failure: null,
  };
}

function completedPlanningDispatch(operationId: string, outcome: string): RouteDeckDispatchResult {
  return {
    ...completedExecutionDispatch(operationId),
    outcome,
  };
}

function unknownExecutionDispatch(): RouteDeckDispatchResult {
  return {
    ...completedExecutionDispatch("sources.test_routed_api_write"),
    disposition: "external_outcome_unknown" as const,
    outcome: null,
    failure: {
      kind: "external_outcome_unknown" as const,
      code: "external_outcome_unknown",
      phase: "execution" as const,
      correlation_id: "attempt-routed",
      operation_id: "sources.test_routed_api_write",
      request_id: "routed-execution-test",
      public_message: "The external write outcome could not be confirmed.",
      recovery_directive: "Do not retry automatically.",
      safe_details: {},
    },
  };
}

function reviewRejectedDispatch(): RouteDeckDispatchResult {
  return {
    ...completedExecutionDispatch("sources.test_routed_api_write"),
    disposition: "failed",
    outcome: null,
    failure: {
      kind: "review",
      code: "review_rejected",
      phase: "review",
      correlation_id: "attempt-routed",
      operation_id: "sources.test_routed_api_write",
      request_id: "routed-execution-test",
      public_message: "The routed write was rejected. No API request was sent.",
      recovery_directive: null,
      safe_details: {},
    },
  };
}

function staleReviewDispatch(): RouteDeckDispatchResult {
  return {
    ...completedExecutionDispatch("sources.test_routed_api_write"),
    disposition: "failed",
    outcome: null,
    failure: {
      kind: "review",
      code: "review_stale",
      phase: "review",
      correlation_id: "attempt-routed",
      operation_id: "sources.test_routed_api_write",
      request_id: "routed-execution-test",
      public_message: "The exact route plan changed before approval. No API request was sent.",
      recovery_directive: null,
      safe_details: {},
    },
  };
}

function writeReviewSurfaceProps(): RouteDeckSurfaceComponentProps {
  return {
    surface: {
      surface_id: "sources.routed_api_write_review",
      component: "sources.routed_api_write_review",
      props: [],
    },
    slot: "review",
    props: {
      state: "pending",
      review_id: "review-routed-write",
      expires_at: "2026-08-08T09:00:00Z",
    },
    spec: {
      id: "sources.routed_api_write_review",
      component: "sources.routed_api_write_review",
      lifecycle: "stable",
      public_props_schema: {},
      affordances: [],
    },
    dispatchAffordance: vi.fn(),
  };
}

function surfaceProps(
  props: RouteDeckSurfaceComponentProps["props"],
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"] = vi.fn(),
): RouteDeckSurfaceComponentProps {
  return {
    surface: { surface_id: "sources.api_operation_test", component: "sources.api_operation_test", props: [] },
    slot: "detail",
    props,
    spec: {
      id: "sources.api_operation_test",
      component: "sources.api_operation_test",
      lifecycle: "stable",
      public_props_schema: {},
      affordances: [
        { id: "create_api_route_plan", event: "submit", operation: { id: "sources.create_api_route_plan" } },
        { id: "continue_api_route_plan", event: "submit", operation: { id: "sources.continue_api_route_plan" } },
        { id: "run_routed_api_read", event: "submit", operation: { id: "sources.test_routed_api_read" } },
        { id: "review_routed_api_write", event: "submit", operation: { id: "sources.test_routed_api_write" } },
      ],
    },
    dispatchAffordance,
  };
}

function jsonResponse(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}
