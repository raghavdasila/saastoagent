import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import type { AgentClient } from "../features/agents/client";
import { AgentStore } from "../features/agents/store";
import { BuilderDeleteReviewSurface } from "../features/builder/BuilderDeleteReviewSurface";
import { BuilderSurface } from "../features/builder/BuilderSurface";
import type { AgentBuildView } from "../features/builder/models";


const acceptReview = vi.fn();
const rejectReview = vi.fn();
vi.mock("@routedeck/react", async (importOriginal) => {
  const original = await importOriginal<typeof import("@routedeck/react")>();
  return {
    ...original,
    useRouteDeckReviewActions: () => ({ accept: acceptReview, reject: rejectReview }),
  };
});
vi.mock("../shared/agent/BuildNavGraph", () => ({
  BuildNavGraph: ({ build }: { readonly build: AgentBuildView }) => <div>NavGraph {build.id}</div>,
}));


it("runs one stopped build and exposes Sandbox only after authoritative running state", async () => {
  const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
  const agentRef = `agent-${agentId.replaceAll("-", "").slice(0, 20)}`;
  const stopped = build(agentId, "stopped");
  const running = { ...stopped, runtime_lifecycle: "running" as const };
  const builds = vi.fn()
    .mockResolvedValueOnce({ agent_id: agentId, builds: [stopped] })
    .mockResolvedValue({ agent_id: agentId, builds: [running] });
  const dispatch = vi.fn(async (affordance: string) => ({
    disposition: "completed",
    outcome: affordance === "run" ? "running" : "opened",
    failure: null,
  }));

  render(<BuilderSurface
    {...surfaceProps(agentRef, dispatch)}
    agentStore={agentStore(agentId)}
    designerClient={{ get: vi.fn(async () => emptyDesign(agentId)) } as never}
    runtimeClient={{ builds, evaluations: emptyEvaluations(agentId) } as never}
  />);

  expect(await screen.findByText(/Stopped\. Start this runtime/)).toBeVisible();
  expect(screen.queryByRole("button", { name: "Continue to Sandbox" })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Pause runtime" })).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Start runtime" }));
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("run", {
    agent_ref: agentRef,
    build_id: stopped.id,
  }));
  expect(await screen.findByText("Running")).toBeVisible();
  expect(screen.getByRole("button", { name: "Continue to Sandbox" })).toBeEnabled();
});


it("pauses admission durably and resumes only through the exact build action", async () => {
  const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
  const agentRef = `agent-${agentId.replaceAll("-", "").slice(0, 20)}`;
  const running = build(agentId, "running");
  const paused = { ...running, runtime_lifecycle: "paused" as const };
  const builds = vi.fn()
    .mockResolvedValueOnce({ agent_id: agentId, builds: [running] })
    .mockResolvedValueOnce({ agent_id: agentId, builds: [paused] })
    .mockResolvedValue({ agent_id: agentId, builds: [running] });
  const dispatch = vi.fn(async (affordance: string) => ({
    disposition: "completed",
    outcome: affordance === "pause" ? "paused" : "running",
    failure: null,
  }));

  render(<BuilderSurface
    {...surfaceProps(agentRef, dispatch)}
    agentStore={agentStore(agentId)}
    designerClient={{ get: vi.fn(async () => emptyDesign(agentId)) } as never}
    runtimeClient={{ builds, evaluations: emptyEvaluations(agentId) } as never}
  />);

  fireEvent.click(await screen.findByRole("button", { name: "Pause runtime" }));
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("pause", {
    agent_ref: agentRef,
    build_id: running.id,
  }));
  expect(await screen.findByText(/Paused\. New Sandbox, Evaluation, and deployment work is blocked/)).toBeVisible();
  expect(screen.queryByRole("button", { name: "Continue to Sandbox" })).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Generate evaluation set" })).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Delete build runtime" })).toBeDisabled();

  fireEvent.click(screen.getByRole("button", { name: "Resume runtime" }));
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("run", {
    agent_ref: agentRef,
    build_id: running.id,
  }));
  expect(await screen.findByText(/Ready for new Sandbox, Evaluation, and deployment work/)).toBeVisible();
});


it("keeps Sandbox navigation available when immutable history contains multiple running builds", async () => {
  const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
  const agentRef = "agent-" + agentId.replaceAll("-", "").slice(0, 20);
  const current = { ...build(agentId, "running"), id: "4bf642f8-18d2-45a9-8a77-b6d293a4fd7d" };
  const prior = { ...build(agentId, "running"), id: "4bf642f8-18d2-45a9-8a77-b6d293a4fd7e" };

  render(<BuilderSurface
    {...surfaceProps(agentRef, vi.fn())}
    agentStore={agentStore(agentId)}
    designerClient={{ get: vi.fn(async () => emptyDesign(agentId)) } as never}
    runtimeClient={{ builds: vi.fn(async () => ({ agent_id: agentId, builds: [current, prior] })), evaluations: emptyEvaluations(agentId) } as never}
  />);

  expect(await screen.findByRole("button", { name: "Continue to Sandbox" })).toBeEnabled();
});


it("requires review before removing a stopped draft runtime", async () => {
  const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
  const agentRef = `agent-${agentId.replaceAll("-", "").slice(0, 20)}`;
  const value = build(agentId, "stopped");
  const dispatch = vi.fn(async () => ({
    disposition: "requires_review",
    outcome: null,
    failure: null,
  }));
  render(<BuilderSurface
    {...surfaceProps(agentRef, dispatch)}
    agentStore={agentStore(agentId)}
    designerClient={{ get: vi.fn(async () => emptyDesign(agentId)) } as never}
    runtimeClient={{ builds: vi.fn(async () => ({ agent_id: agentId, builds: [value] })), evaluations: emptyEvaluations(agentId) } as never}
  />);

  fireEvent.click(await screen.findByRole("button", { name: "Delete build runtime" }));
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("delete", {
    agent_ref: agentRef,
    build_id: value.id,
  }));

  acceptReview.mockResolvedValueOnce({
    disposition: "completed", outcome: "removed", failure: null,
  });
  render(<BuilderDeleteReviewSurface {...reviewProps()} />);
  fireEvent.click(screen.getByRole("button", { name: "Remove draft runtime" }));
  await waitFor(() => expect(acceptReview).toHaveBeenCalledWith("review-build-delete"));
  expect(screen.getByText(/immutable build, prior Sandbox and Evaluation results/i)).toBeVisible();
});


it("guides a failed build to its exact Source setup and permits an explicit retained retry", async () => {
  const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
  const agentRef = `agent-${agentId.replaceAll("-", "").slice(0, 20)}`;
  const buildRequestId = "4bf642f8-18d2-45a9-8a77-b6d293a4fd7b";
  const sourceId = "source-retry-001";
  const sourceRevisionId = "revision-retry01";
  const failed = {
    ...build(agentId, "stopped"),
    build_request_id: buildRequestId,
    status: "failed",
    runtime_build_hash: null,
    model: null,
    model_digest: null,
    attempt_number: 1,
    failure_code: "builderunavailable",
    failure_message: "Connection setup is missing.",
  } satisfies AgentBuildView;
  const assembling = {
    ...failed,
    id: "4bf642f8-18d2-45a9-8a77-b6d293a4fd7d",
    status: "assembling",
    attempt_number: 2,
    failure_code: null,
    failure_message: null,
  } satisfies AgentBuildView;
  const builds = vi.fn()
    .mockResolvedValueOnce({ agent_id: agentId, builds: [failed] })
    .mockResolvedValue({ agent_id: agentId, builds: [assembling, failed] });
  const dispatch = vi.fn(async (affordance: string) => ({
    disposition: "completed",
    outcome: affordance === "assemble" ? "assembled" : "opened",
    failure: null,
  }));
  const design = {
    agent_id: agentId,
    current_revision_id: "4bf642f8-18d2-45a9-8a77-b6d293a4fd7c",
    accepted_revision_id: "4bf642f8-18d2-45a9-8a77-b6d293a4fd7c",
    revisions: [{
      id: "4bf642f8-18d2-45a9-8a77-b6d293a4fd7c",
      revision: 1,
      agent_version: 1,
      input_fingerprint: "i".repeat(64),
      content: { goal: "", instructions: "", features: [], behaviors: [], policies: [], capabilities: [], tools: [] },
      topology: { topology_hash: "t".repeat(64), entry_node_id: "entry", nodes: [], capabilities: [], operation_ids: [] },
      source_inputs: [{ source_id: sourceId, source_revision_id: sourceRevisionId }],
      created_at: "2026-08-11T00:00:00Z",
    }],
    build_request: {
      id: buildRequestId,
      design_revision_id: "4bf642f8-18d2-45a9-8a77-b6d293a4fd7c",
      status: "failed",
      created_at: "2026-08-11T00:00:00Z",
    },
  };

  render(<BuilderSurface
    {...surfaceProps(agentRef, dispatch)}
    agentStore={agentStore(agentId)}
    designerClient={{ get: vi.fn(async () => design) } as never}
    runtimeClient={{ builds, evaluations: emptyEvaluations(agentId) } as never}
  />);

  expect(await screen.findByRole("button", { name: "Retry failed build" })).toBeEnabled();
  expect(screen.getByText(`API Source ${sourceId}`)).toBeVisible();
  expect(screen.getByText(`API version ${sourceRevisionId}`)).toBeVisible();
  expect(screen.getByText("Build attempt 1")).toBeVisible();

  expect(screen.getByText("Resolve the exact pinned API version. If its version changes, update the accepted design before retrying explicitly.")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Open API setup" }));
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("open_source_prerequisite", {
    agent_ref: agentRef,
    source_id: sourceId,
    return_to: "builder",
    target_stage: "connection",
  }));

  fireEvent.click(screen.getByRole("button", { name: "Retry failed build" }));
  await waitFor(() => expect(dispatch).toHaveBeenCalledWith("assemble", {
    agent_ref: agentRef,
    build_request_id: buildRequestId,
  }));
  expect(await screen.findByText("Build attempt 2")).toBeVisible();
  expect(screen.getByText("Build attempt 1")).toBeVisible();
});


it("shows automatic exact-build evaluation generation without a manual Builder action", async () => {
  const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
  const value = build(agentId, "running");
  render(<BuilderSurface
    {...surfaceProps(`agent-${agentId.replaceAll("-", "").slice(0, 20)}`, vi.fn())}
    agentStore={agentStore(agentId)}
    designerClient={{ get: vi.fn(async () => emptyDesign(agentId)) } as never}
    runtimeClient={{
      builds: vi.fn(async () => ({ agent_id: agentId, builds: [value] })),
      evaluations: vi.fn(async () => ({
        agent_id: agentId,
        evaluation_sets: [{
          id: "4bf642f8-18d2-45a9-8a77-b6d293a4fd70",
          agent_id: agentId,
          build_id: value.id,
          name: "Generated coverage",
          generation_job_id: "4bf642f8-18d2-45a9-8a77-b6d293a4fd71",
          generation_status: "ready",
          generation_failure_code: null,
          generation_failure_message: null,
          generation_summary: { accepted_count: 2 },
          cases: [{}, {}],
          eligible: false,
          eligibility_reasons: ["generated_evaluation_cases_pending"],
          created_at: "2026-08-11T00:00:00Z",
        }],
      })),
    } as never}
  />);

  expect(await screen.findByText("Ready with 2 generated cases.")).toBeVisible();
  expect(screen.queryByRole("button", { name: "Generate evaluation set" })).not.toBeInTheDocument();
});


it("refreshes exact-build evaluation generation after asynchronous assembly completes", async () => {
  const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
  const value = build(agentId, "stopped");
  const evaluation = (status: "queued" | "ready") => ({
    id: "4bf642f8-18d2-45a9-8a77-b6d293a4fd70",
    agent_id: agentId,
    build_id: value.id,
    name: "Generated coverage",
    generation_job_id: "4bf642f8-18d2-45a9-8a77-b6d293a4fd71",
    generation_status: status,
    generation_failure_code: null,
    generation_failure_message: null,
    generation_summary: status === "ready" ? { accepted_count: 1 } : null,
    cases: status === "ready" ? [{}] : [],
    eligible: false,
    eligibility_reasons: ["generated_evaluation_cases_pending"],
    created_at: "2026-08-11T00:00:00Z",
  });
  const evaluations = vi.fn()
    .mockResolvedValueOnce({ agent_id: agentId, evaluation_sets: [] })
    .mockResolvedValueOnce({ agent_id: agentId, evaluation_sets: [evaluation("queued")] })
    .mockResolvedValue({ agent_id: agentId, evaluation_sets: [evaluation("ready")] });

  render(<BuilderSurface
    {...surfaceProps(`agent-${agentId.replaceAll("-", "").slice(0, 20)}`, vi.fn())}
    agentStore={agentStore(agentId)}
    designerClient={{ get: vi.fn(async () => emptyDesign(agentId)) } as never}
    runtimeClient={{
      builds: vi.fn(async () => ({ agent_id: agentId, builds: [value] })),
      evaluations,
    } as never}
  />);

  expect(await screen.findByText(/Not scheduled\. This build is incomplete/)).toBeVisible();
  expect(await screen.findByText("Queued automatically for this exact build.", {}, { timeout: 3_000 })).toBeVisible();
  expect(await screen.findByText("Ready with 1 generated case.", {}, { timeout: 3_000 })).toBeVisible();
  expect(evaluations.mock.calls.length).toBeGreaterThanOrEqual(3);
});


function build(
  agentId: string,
  runtimeLifecycle: AgentBuildView["runtime_lifecycle"],
): AgentBuildView {
  return {
    id: "4bf642f8-18d2-45a9-8a77-b6d293a4fd7a",
    agent_id: agentId,
    build_request_id: "4bf642f8-18d2-45a9-8a77-b6d293a4fd7b",
    design_revision_id: "4bf642f8-18d2-45a9-8a77-b6d293a4fd7c",
    agent_version: 1,
    attempt_number: 1,
    status: "ready",
    runtime_lifecycle: runtimeLifecycle,
    runtime_build_hash: "r".repeat(64), model: "model", model_digest: "digest",
    allowed_operation_ids: ["GetProductTypes"], navgraph_hash: "n".repeat(64),
    compiled_navgraph: {}, frontend_contract: {}, failure_code: null,
    failure_message: null, created_at: "2026-08-11T00:00:00Z",
    updated_at: "2026-08-11T00:00:00Z",
  };
}


function agentStore(agentId: string): AgentStore {
  return new AgentStore({
    list: vi.fn(async () => ({ agents: [{
      id: agentId, name: "Store Agent", description: "", instructions: "",
      lifecycle: "active", current_version: 1,
      created_at: "2026-08-11T00:00:00Z", updated_at: "2026-08-11T00:00:00Z",
    }] })),
    listSources: vi.fn(async () => ({ attachments: [] })),
    listBuilds: vi.fn(async () => ({ builds: [] })),
    inspectDependencies: vi.fn(async () => ({
      agent_id: agentId, source_attachments: [], build_ids: [], blocks_delete: false,
    })),
  } as unknown as AgentClient);
}


function emptyDesign(agentId: string) {
  return {
    agent_id: agentId,
    current_revision_id: "",
    accepted_revision_id: null,
    revisions: [],
    build_request: null,
  };
}


function emptyEvaluations(agentId: string) {
  return vi.fn(async () => ({ agent_id: agentId, evaluation_sets: [] }));
}


function surfaceProps(agentRef: string, dispatch: unknown): RouteDeckSurfaceComponentProps {
  return {
    surface: { surface_id: "builder.home", component: "builder.home", props: [] },
    slot: "active", props: { selected_agent_ref: agentRef },
    spec: { id: "builder.home", component: "builder.home", lifecycle: "stable", public_props_schema: {}, affordances: [] },
    dispatchAffordance: dispatch,
  } as unknown as RouteDeckSurfaceComponentProps;
}


function reviewProps(): RouteDeckSurfaceComponentProps {
  return {
    surface: { surface_id: "builder.delete_review", component: "builder.delete_review", props: [] },
    slot: "review",
    props: {
      state: "pending", review_id: "review-build-delete",
      expires_at: "2026-08-12T00:00:00Z",
    },
    spec: { id: "builder.delete_review", component: "builder.delete_review", lifecycle: "stable", public_props_schema: {}, affordances: [] },
  } as unknown as RouteDeckSurfaceComponentProps;
}
