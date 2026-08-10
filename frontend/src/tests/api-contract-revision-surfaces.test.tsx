import { fireEvent, screen, waitFor } from "@testing-library/react";
import type { RouteDeckDispatchResult } from "@routedeck/core";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { expect, it, vi } from "vitest";

import { ApiContractRevisionPanel } from "../features/sources/ApiContractRevisionPanel";
import { ApiContractRevisionReviewSurface } from "../features/sources/ApiContractRevisionReviewSurface";
import { RoutedApiWriteReviewSurface } from "../features/sources/RoutedApiWriteReviewSurface";
import { ContractRevisionStore } from "../features/sources/contractRevisionStore";
import { RoutedExecutionStore } from "../features/sources/routedExecutionStore";
import { SourceClient } from "../features/sources/sourceClient";
import {
  frameworkContractFixture,
  frameworkProjectionFixture,
  renderRouteDeckComponent,
} from "./routeDeckHarness";

const SOURCE_ID = "sourceopaque0001";
const PROPOSAL_ID = "proposalopaque01";
const PROPOSAL_REF = `contract-proposal-${PROPOSAL_ID}`;

it("renders exact hashes, all patches and BaseRegionCountry impact before review", async () => {
  const client = sourceClient();
  const store = new ContractRevisionStore(client);
  const dispatchAffordance = vi.fn(async () => requiresReviewResult());
  const rendered = await renderRouteDeckComponent(
    <ApiContractRevisionPanel
      {...surfaceProps(
        "sources.contract_revision_proposal",
        "sources.contract_revision_proposal",
        dispatchAffordance,
        { source_id: SOURCE_ID, proposal_ref: PROPOSAL_REF },
      )}
      store={store}
    />,
    { contract: frameworkContractFixture(), projection: frameworkProjectionFixture() },
  );

  expect(await screen.findByText("Shared-schema impact: 2")).toBeVisible();
  expect(screen.getByText("6435eb6c5861391b")).toBeVisible();
  expect(screen.getByText("6fca".repeat(16))).toBeVisible();
  expect(screen.getAllByRole("listitem")).toHaveLength(10);
  fireEvent.click(screen.getByRole("button", { name: "Review this API update" }));
  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledWith(
    "approve_contract_revision",
    { proposal_ref: PROPOSAL_REF },
  ));
  rendered.dispose();
});

it("accepts through durable RouteDeck review and signals Source inventory refresh", async () => {
  const client = sourceClient();
  const store = new ContractRevisionStore(client);
  await store.load(SOURCE_ID, PROPOSAL_REF);
  const rendered = await renderRouteDeckComponent(
    <ApiContractRevisionReviewSurface
      {...surfaceProps(
        "sources.contract_revision_review",
        "sources.contract_revision_review",
        vi.fn(),
        {
          state: "pending",
          review_id: "review-contract-1",
          expires_at: "2026-08-07T23:00:00Z",
        },
      )}
      store={store}
    />,
    {
      contract: frameworkContractFixture(),
      projection: frameworkProjectionFixture(),
      dispatchResult: completedResult(),
    },
  );

  expect(screen.getByText("Explicit shared-schema impact: 2")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Accept and create new version" }));
  await waitFor(() => expect(store.snapshot().approvalSequence).toBe(1));
  expect(store.snapshot().proposal?.state).toBe("approved");
  rendered.dispose();
});

it("keeps the current API version unchanged when durable review is rejected", async () => {
  const store = new ContractRevisionStore(sourceClient());
  await store.load(SOURCE_ID, PROPOSAL_REF);
  const rendered = await renderRouteDeckComponent(
    <ApiContractRevisionReviewSurface
      {...surfaceProps(
        "sources.contract_revision_review",
        "sources.contract_revision_review",
        vi.fn(),
        {
          state: "pending",
          review_id: "review-contract-reject",
          expires_at: "2026-08-07T23:00:00Z",
        },
      )}
      store={store}
    />,
    {
      contract: frameworkContractFixture(),
      projection: frameworkProjectionFixture(),
      dispatchResult: reviewRejectedResult(),
    },
  );

  fireEvent.click(screen.getByRole("button", { name: "Keep current version unchanged" }));
  await waitFor(() => expect(screen.queryByText("Keeping current revisionâ€¦")).toBeNull());
  expect(store.snapshot().proposal?.state).toBe("pending");
  expect(store.snapshot().approvalSequence).toBe(0);
  expect(screen.queryByRole("alert")).toBeNull();
  rendered.dispose();
});

it("shows the safe failure when review acceptance does not complete", async () => {
  const store = new ContractRevisionStore(sourceClient());
  await store.load(SOURCE_ID, PROPOSAL_REF);
  const rendered = await renderRouteDeckComponent(
    <ApiContractRevisionReviewSurface
      {...surfaceProps(
        "sources.contract_revision_review",
        "sources.contract_revision_review",
        vi.fn(),
        {
          state: "pending",
          review_id: "review-contract-stale",
          expires_at: "2026-08-07T23:00:00Z",
        },
      )}
      store={store}
    />,
    {
      contract: frameworkContractFixture(),
      projection: frameworkProjectionFixture(),
      dispatchResult: failedAcceptResult(),
    },
  );

  fireEvent.click(screen.getByRole("button", { name: "Accept and create new version" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "The contract proposal changed. Reload its exact evidence before approval.",
  );
  expect(store.snapshot().proposal?.state).toBe("pending");
  expect(store.snapshot().approvalSequence).toBe(0);
  rendered.dispose();
});

it("renders only the exact props-targeted review when proposal and routed-plan contexts coexist", async () => {
  const contractStore = new ContractRevisionStore(sourceClient());
  await contractStore.load(SOURCE_ID, PROPOSAL_REF);
  const routeClient = new SourceClient({
    fetch: vi.fn(async () => new Response("null", {
      status: 200,
      headers: { "Content-Type": "application/json" },
    })),
  });
  routeClient.selectConversation("conversation-review-isolation");
  const executionStore = new RoutedExecutionStore(routeClient);
  await executionStore.select(SOURCE_ID, routedWritePlan());
  const contractPending = {
    state: "pending",
    review_id: "review-contract-exact",
    expires_at: "2026-08-08T09:00:00Z",
  };
  const routedPending = {
    state: "pending",
    review_id: "review-routed-exact",
    expires_at: "2026-08-08T09:00:00Z",
  };
  const rendered = await renderRouteDeckComponent(
    <>
      <ApiContractRevisionReviewSurface
        {...surfaceProps("sources.contract_revision_review", "sources.contract_revision_review", vi.fn(), contractPending)}
        store={contractStore}
      />
      <RoutedApiWriteReviewSurface
        {...surfaceProps("sources.routed_api_write_review", "sources.routed_api_write_review", vi.fn(), {})}
        store={executionStore}
      />
    </>,
    { contract: frameworkContractFixture(), projection: frameworkProjectionFixture() },
  );

  expect(screen.getByRole("heading", { name: "Create this immutable API version?" })).toBeVisible();
  expect(screen.queryByRole("heading", { name: "Send this routed API write?" })).toBeNull();
  rendered.rerender(
    <>
      <ApiContractRevisionReviewSurface
        {...surfaceProps("sources.contract_revision_review", "sources.contract_revision_review", vi.fn(), {})}
        store={contractStore}
      />
      <RoutedApiWriteReviewSurface
        {...surfaceProps("sources.routed_api_write_review", "sources.routed_api_write_review", vi.fn(), routedPending)}
        store={executionStore}
      />
    </>,
  );
  expect(screen.queryByRole("heading", { name: "Create this immutable API version?" })).toBeNull();
  expect(screen.getByRole("heading", { name: "Send this routed API write?" })).toBeVisible();
  rendered.dispose();
});

function sourceClient(): SourceClient {
  return new SourceClient({
    fetch: vi.fn(async (input: RequestInfo | URL) => {
      if (String(input) !== `/api/sources/${SOURCE_ID}/contract-revisions`) {
        throw new Error(`Unexpected request: ${String(input)}`);
      }
      return new Response(JSON.stringify([proposal()]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }),
  });
}

function proposal() {
  const patches = [
    "0e3ca203c694b3ea", "0b580a91a8f44b89", "79b18616b26c149a",
    "40e01e7194d00a7d", "092ef91c4b3d772b", "c974401b1bfc59b3",
    "6435eb6c5861391b", "2e3008cbf6b3f5b2", "edcb5d80e92f57a1",
    "3f4de4aa354d0324",
  ];
  return {
    proposal_id: PROPOSAL_ID,
    source_id: SOURCE_ID,
    parent_revision_id: "revisionopaque01",
    state: "pending",
    source_raw_sha256: "fd17".repeat(16),
    source_canonical_sha256: "a3db".repeat(16),
    repair_manifest_sha256: "dc71".repeat(16),
    repaired_parent_sha256: "bc1b".repeat(16),
    final_canonical_sha256: "6fca".repeat(16),
    patches: patches.map((patchId) => ({
      patch_id: patchId,
      kind: patchId === "6435eb6c5861391b" ? "remove_required" : "set_nullable",
      schema_pointer: patchId === "6435eb6c5861391b"
        ? "/components/schemas/BaseRegionCountry"
        : "/components/schemas/StoreCart",
      field_name: patchId === "6435eb6c5861391b" ? "id" : null,
      evidence_count: patchId === "6435eb6c5861391b" ? 7 : 1,
      impact_count: patchId === "6435eb6c5861391b" ? 2 : 1,
    })),
    local_medusa_version: "2.13.6",
    local_package_json_sha256: "798d".repeat(16),
    local_package_lock_sha256: "540a".repeat(16),
    evidence_sha256: "de48".repeat(16),
    proposed_at: "2026-08-07T20:00:00Z",
    approved_by_owner_id: null,
    approved_at: null,
    approved_revision_id: null,
  };
}

function routedWritePlan() {
  return {
    plan_id: "planopaque000001",
    record_id: "recordopaque0001",
    previous_record_id: null,
    source_id: SOURCE_ID,
    source_revision_id: "revisionopaque01",
    profile_id: "profileopaque001",
    curation_id: "curationopaque01",
    inventory_fingerprint: "b".repeat(64),
    subset_fingerprint: "c".repeat(64),
    request_text: "Create a cart",
    state: "ready" as const,
    steps: [{
      query: "Create a cart",
      ranked_operations: [{ operation_id: "CreateCart", endpoint_id: "medusa:CreateCart", score: 0.99 }],
      selected_operation_id: "CreateCart",
      method: "POST",
      path_template: "/store/carts",
      http_safety: "write" as const,
    }],
    missing_inputs: [],
    input_provenance: [],
    managed_parameters: [{
      name: "x-publishable-api-key",
      location: "header" as const,
      authentication_method: "api_key" as const,
      source: "managed_by_profile" as const,
    }],
    operation_choice: null,
    clarification_prompt: null,
    created_at: "2026-08-08T08:00:00Z",
    expires_at: "2026-08-08T08:30:00Z",
    plan_fingerprint: "d".repeat(64),
    api_call_count: 0 as const,
  };
}

function surfaceProps(
  surfaceId: string,
  component: string,
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"],
  props: RouteDeckSurfaceComponentProps["props"],
): RouteDeckSurfaceComponentProps {
  return {
    surface: { surface_id: surfaceId, component, props: [] },
    slot: "review",
    props,
    spec: {
      id: surfaceId,
      component,
      lifecycle: "stable",
      public_props_schema: {},
      affordances: surfaceId.endsWith("proposal")
        ? [{ id: "approve_contract_revision", event: "submit", operation: { id: "sources.approve_contract_revision" } }]
        : [],
    },
    dispatchAffordance,
  };
}

function requiresReviewResult(): RouteDeckDispatchResult {
  return {
    ...completedResult(),
    disposition: "requires_review",
    outcome: null,
    review: { id: "review-contract-1", expires_at: "2026-08-07T23:00:00Z" },
  };
}

function completedResult(): RouteDeckDispatchResult {
  return {
    disposition: "completed",
    operation_id: "sources.approve_contract_revision",
    request_id: "contract-test",
    session_version: 2,
    projection_version: 2,
    evidence: {
      source: "surface",
      phases: ["received", "completed"],
      attempt_id: "attempt-contract",
      request_fingerprint: "fingerprint-contract",
      delivery_phase: "response_received",
      result_id: "result-contract",
      result_fingerprint: "result-fingerprint-contract",
    },
    review: null,
    outcome: "approved",
    failure: null,
  };
}

function reviewRejectedResult(): RouteDeckDispatchResult {
  return {
    ...completedResult(),
    disposition: "failed",
    outcome: null,
    failure: {
      kind: "review",
      code: "review_rejected",
      phase: "review",
      correlation_id: "attempt-contract",
      operation_id: "sources.approve_contract_revision",
      request_id: "contract-test",
      public_message: "The review was rejected. The current Source remains unchanged.",
      recovery_directive: null,
      safe_details: {},
    },
  };
}

function failedAcceptResult(): RouteDeckDispatchResult {
  return {
    ...completedResult(),
    disposition: "failed",
    outcome: null,
    failure: {
      kind: "review",
      code: "review_stale",
      phase: "review",
      correlation_id: "attempt-contract",
      operation_id: "sources.approve_contract_revision",
      request_id: "contract-test",
      public_message: "The contract proposal changed. Reload its exact evidence before approval.",
      recovery_directive: null,
      safe_details: {},
    },
  };
}
