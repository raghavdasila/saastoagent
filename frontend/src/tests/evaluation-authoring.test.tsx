import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import type { AgentClient } from "../features/agents/client";
import { AgentStore } from "../features/agents/store";
import type { AgentBuildView, EvaluationSetView } from "../features/builder/models";
import { EvaluationDeleteReviewSurface } from "../features/evaluation/EvaluationDeleteReviewSurface";
import { EvaluationSurface } from "../features/evaluation/EvaluationSurface";


const acceptReview = vi.fn();
const rejectReview = vi.fn();
vi.mock("@routedeck/react", async (importOriginal) => {
  const original = await importOriginal<typeof import("@routedeck/react")>();
  return { ...original, useRouteDeckReviewActions: () => ({ accept: acceptReview, reject: rejectReview }) };
});
vi.mock("../features/builder/BuildNavGraph", () => ({ BuildNavGraph: () => <div>Exact build NavGraph</div> }));


it("generates against the selected immutable build and exposes revisioned case management", async () => {
  const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
  const agentRef = `agent-${agentId.replaceAll("-", "").slice(0, 20)}`;
  const build = buildView(agentId);
  const evaluationSet = setView(agentId, build.id);
  const dispatch = vi.fn(async (affordance: string) => ({
    disposition: affordance === "delete_case" ? "requires_review" : "completed",
    outcome: affordance === "generate_set" ? "queued" : affordance === "edit_case" ? "edited" : null,
    failure: null,
  }));
  const runtimeClient = {
    builds: vi.fn(async () => ({ agent_id: agentId, builds: [build] })),
    sandbox: vi.fn(async () => ({ agent_id: agentId, runs: [] })),
    evaluations: vi.fn(async () => ({ agent_id: agentId, evaluation_sets: [evaluationSet] })),
  };

  render(<EvaluationSurface {...surfaceProps(agentRef, dispatch)} agentStore={agentStore(agentId)} runtimeClient={runtimeClient as never} />);

  fireEvent.click(await screen.findByRole("button", { name: "Generate with ToolRouter" }));
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("generate_set", {
    agent_ref: agentRef, build_id: build.id,
    set_name: "Generated coverage", categories: ["paraphrase"],
  }));
  expect(screen.getByText("ToolRouter generated")).toBeVisible();
  expect(screen.getByText("Draft coverage")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Edit" }));
  fireEvent.change(screen.getByRole("textbox", { name: "Edit case title" }), { target: { value: "List product taxonomy" } });
  fireEvent.click(screen.getByRole("button", { name: "Save revision" }));
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("edit_case", expect.objectContaining({
    agent_ref: agentRef, case_id: evaluationSet.cases[0].id,
    expected_revision: 1, title: "List product taxonomy",
  })));
  fireEvent.click(screen.getByRole("button", { name: "Remove" }));
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("delete_case", {
    agent_ref: agentRef, case_id: evaluationSet.cases[0].id, expected_revision: 1,
  }));
});


it("renders destructive case removal as a consequence review that preserves prior results", async () => {
  acceptReview.mockResolvedValueOnce({ disposition: "completed", outcome: "removed", failure: null });
  render(<EvaluationDeleteReviewSurface {...reviewProps()} />);
  expect(screen.getByText(/prior case revisions and completed evaluation results remain/i)).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Remove case" }));
  await waitFor(() => expect(acceptReview).toHaveBeenCalledWith("review-evaluation-delete"));
});


it("explains the missing build prerequisite and continues the same Agent to Builds", async () => {
  const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
  const agentRef = `agent-${agentId.replaceAll("-", "").slice(0, 20)}`;
  const dispatch = vi.fn(async () => ({ disposition: "completed", outcome: "opened", failure: null }));
  const runtimeClient = {
    builds: vi.fn(async () => ({ agent_id: agentId, builds: [] })),
    sandbox: vi.fn(async () => ({ agent_id: agentId, runs: [] })),
    evaluations: vi.fn(async () => ({ agent_id: agentId, evaluation_sets: [] })),
  };

  render(<EvaluationSurface {...surfaceProps(agentRef, dispatch)} agentStore={agentStore(agentId)} runtimeClient={runtimeClient as never} />);

  expect(await screen.findByText("A ready immutable build is required.")).toBeVisible();
  expect(screen.getByText("Corpus will not start or substitute a build.", { exact: false })).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Continue to Builds" }));

  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("continue_to_builds", {
    agent_ref: agentRef,
  }));
});


it("does not report a missing build while authoritative Evaluation state is loading", async () => {
  const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
  const agentRef = `agent-${agentId.replaceAll("-", "").slice(0, 20)}`;
  const never = new Promise<never>(() => undefined);
  const runtimeClient = {
    builds: vi.fn(() => never),
    sandbox: vi.fn(() => never),
    evaluations: vi.fn(() => never),
  };

  render(<EvaluationSurface {...surfaceProps(agentRef, vi.fn())} agentStore={agentStore(agentId)} runtimeClient={runtimeClient as never} />);

  expect(await screen.findByText("Loading exact Evaluation…")).toBeVisible();
  expect(screen.queryByText("A ready immutable build is required.")).not.toBeInTheDocument();
});


it("shows durable run failure and retries the exact failed attempt", async () => {
  const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
  const agentRef = `agent-${agentId.replaceAll("-", "").slice(0, 20)}`;
  const build = buildView(agentId);
  const baseSet = setView(agentId, build.id);
  const attemptId = "4fd0585f-9102-44df-972f-8e8a8b57de33";
  const evaluationSet: EvaluationSetView = {
    ...baseSet,
    cases: [{
      ...baseSet.cases[0],
      latest_run_attempt: {
        id: attemptId, status: "failed",
        retry_of_attempt_id: null, failure_code: "evaluation_run_failed",
        failure_message: "The queued evaluation run failed.",
        created_at: "2026-08-11T00:00:00Z",
        updated_at: "2026-08-11T00:01:00Z",
      },
    }],
  };
  const dispatch = vi.fn(async () => ({ disposition: "completed", outcome: "queued", failure: null }));
  const runtimeClient = {
    builds: vi.fn(async () => ({ agent_id: agentId, builds: [build] })),
    sandbox: vi.fn(async () => ({ agent_id: agentId, runs: [] })),
    evaluations: vi.fn(async () => ({ agent_id: agentId, evaluation_sets: [evaluationSet] })),
  };

  render(<EvaluationSurface {...surfaceProps(agentRef, dispatch)} agentStore={agentStore(agentId)} runtimeClient={runtimeClient as never} />);

  expect(await screen.findByText("The queued evaluation run failed.")).toBeVisible();
  fireEvent.click(screen.getByRole("button", { name: "Retry failed run" }));
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("retry_case_run", {
    agent_ref: agentRef, attempt_id: attemptId,
  }));
});


function buildView(agentId: string): AgentBuildView {
  return {
    id: "4bf642f8-18d2-45a9-8a77-b6d293a4fd7a", agent_id: agentId,
    build_request_id: "request", design_revision_id: "design", agent_version: 1, attempt_number: 1,
    status: "ready", runtime_lifecycle: "running", runtime_build_hash: "r".repeat(64),
    model: "model", model_digest: "digest", allowed_operation_ids: ["GetProductTypes"],
    navgraph_hash: "n".repeat(64), compiled_navgraph: {}, frontend_contract: {},
    failure_code: null, failure_message: null,
    created_at: "2026-08-11T00:00:00Z", updated_at: "2026-08-11T00:00:00Z",
  };
}


function setView(agentId: string, buildId: string): EvaluationSetView {
  return {
    id: "b7a7f92f-2b1b-43cb-b404-ff99172ee8e5", agent_id: agentId, build_id: buildId,
    name: "Generated coverage", generation_job_id: "cf1dd736-c823-4e0c-82fd-cedbb3a4f70d",
    generation_status: "ready", generation_failure_code: null,
    generation_failure_message: null, generation_summary: { accepted_count: 1 },
    eligible: null, eligibility_reasons: [], created_at: "2026-08-11T00:00:00Z",
    cases: [{
      id: "8441f6a6-7958-4635-89bb-c3e020bc77f5", title: "List product types",
      message: "List every product type", source_kind: "toolrouter",
      category: "paraphrase", difficulty: "easy", mandatory: false,
      expected_operation_ids: ["GetProductTypes"], current_revision: 1,
      removed: false, runnable: false, latest_status: null, latest_run_attempt: null,
    }],
  };
}


function agentStore(agentId: string): AgentStore {
  return new AgentStore({
    list: vi.fn(async () => ({ agents: [{ id: agentId, name: "Store Agent", description: "", instructions: "", lifecycle: "active", current_version: 1, created_at: "2026-08-11T00:00:00Z", updated_at: "2026-08-11T00:00:00Z" }] })),
    listSources: vi.fn(async () => ({ attachments: [] })), listBuilds: vi.fn(async () => ({ builds: [] })),
    inspectDependencies: vi.fn(async () => ({ agent_id: agentId, source_attachments: [], build_ids: [], blocks_delete: false })),
  } as unknown as AgentClient);
}


function surfaceProps(agentRef: string, dispatch: unknown): RouteDeckSurfaceComponentProps {
  return { surface: { surface_id: "evaluation.home", component: "evaluation.home", props: [] }, slot: "active", props: { selected_agent_ref: agentRef }, spec: { id: "evaluation.home", component: "evaluation.home", lifecycle: "stable", public_props_schema: {}, affordances: [] }, dispatchAffordance: dispatch } as unknown as RouteDeckSurfaceComponentProps;
}


function reviewProps(): RouteDeckSurfaceComponentProps {
  return { surface: { surface_id: "evaluation.delete_case_review", component: "evaluation.delete_case_review", props: [] }, slot: "review", props: { state: "pending", review_id: "review-evaluation-delete", expires_at: "2026-08-12T00:00:00Z" }, spec: { id: "evaluation.delete_case_review", component: "evaluation.delete_case_review", lifecycle: "stable", public_props_schema: {}, affordances: [] } } as unknown as RouteDeckSurfaceComponentProps;
}
