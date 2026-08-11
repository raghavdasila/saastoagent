import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { beforeEach, expect, it, vi } from "vitest";

import { SourceDeleteReviewSurface } from "../features/sources/SourceDeleteReviewSurface";
import { SourceClient } from "../features/sources/sourceClient";
import { SourceLifecycleStore } from "../features/sources/sourceLifecycleStore";

const acceptReview = vi.fn();
const rejectReview = vi.fn();

vi.mock("@routedeck/react", async (importOriginal) => {
  const original = await importOriginal<typeof import("@routedeck/react")>();
  return {
    ...original,
    useRouteDeckReviewActions: () => ({ accept: acceptReview, reject: rejectReview }),
  };
});

beforeEach(() => {
  acceptReview.mockReset();
  rejectReview.mockReset();
});

it("shows exact dependency consequences and disables destructive acceptance while blocked", async () => {
  const store = lifecycleStore({
    attached_agent_ids: ["00000000-0000-0000-0000-000000000002"],
    design_revision_ids: ["00000000-0000-0000-0000-000000000003"],
    build_ids: ["00000000-0000-0000-0000-000000000004"],
    blocks_delete: true,
  });

  render(<SourceDeleteReviewSurface {...reviewProps()} store={store} />);

  expect(await screen.findByText("Agent attachments: 1")).toBeVisible();
  expect(screen.getByText("Saved design revisions: 1")).toBeVisible();
  expect(screen.getByText("Immutable builds: 1")).toBeVisible();
  expect(screen.getByRole("button", { name: "Delete API source permanently" })).toBeDisabled();
  expect(acceptReview).not.toHaveBeenCalled();
});

it("accepts one unblocked exact review and clears the deleted Source context", async () => {
  const store = lifecycleStore({
    attached_agent_ids: [],
    design_revision_ids: [],
    build_ids: [],
    blocks_delete: false,
  });
  acceptReview.mockResolvedValueOnce({
    disposition: "completed",
    outcome: "deleted",
    failure: null,
  });

  render(<SourceDeleteReviewSurface {...reviewProps()} store={store} />);
  fireEvent.click(await screen.findByRole("button", { name: "Delete API source permanently" }));

  await waitFor(() => expect(acceptReview).toHaveBeenCalledWith("review-source-delete"));
  expect(store.snapshot().selected).toBeNull();
  expect(store.snapshot().dependencies).toBeNull();
});

function lifecycleStore(overrides: {
  attached_agent_ids: string[];
  design_revision_ids: string[];
  build_ids: string[];
  blocks_delete: boolean;
}): SourceLifecycleStore {
  const client = new SourceClient({
    fetch: vi.fn(async (input: RequestInfo | URL) => {
      expect(String(input)).toBe("/api/sources/sourceopaque0001/dependencies");
      return new Response(JSON.stringify({
        source_id: "sourceopaque0001",
        processing_state: "ready",
        ...overrides,
      }), { status: 200, headers: { "Content-Type": "application/json" } });
    }),
  });
  const store = new SourceLifecycleStore(client);
  store.select({
    source_id: "sourceopaque0001",
    connector_key: "api",
    display_name: "Store API",
    created_at: "2026-08-11T00:00:00Z",
    updated_at: "2026-08-11T00:00:00Z",
    revision: {
      revision_id: "revisionopaque01",
      source_id: "sourceopaque0001",
      original_filename: "store.yaml",
      content_sha256: "a".repeat(64),
      description_filename: null,
      description_sha256: null,
      job_id: null,
      state: "ready",
      created_at: "2026-08-11T00:00:00Z",
      updated_at: "2026-08-11T00:00:00Z",
      summary: {},
      failure_code: null,
      failure_message: null,
      parent_revision_id: null,
      artifact_revision_id: null,
    },
  });
  return store;
}

function reviewProps(): RouteDeckSurfaceComponentProps {
  return {
    surface: {
      surface_id: "sources.delete_review",
      component: "sources.delete_review",
      props: [],
    },
    slot: "review",
    props: {
      state: "pending",
      review_id: "review-source-delete",
      expires_at: "2026-08-12T00:00:00Z",
    },
    spec: {
      id: "sources.delete_review",
      component: "sources.delete_review",
      lifecycle: "stable",
      public_props_schema: {},
      affordances: [],
    },
    dispatchAffordance: vi.fn(),
  };
}
