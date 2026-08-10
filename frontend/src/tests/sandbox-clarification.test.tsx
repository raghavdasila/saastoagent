import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import type { AgentClient } from "../features/agents/client";
import { AgentStore } from "../features/agents/store";
import type { AgentRuntimeClient } from "../features/builder/client";
import type { SandboxRunView } from "../features/builder/models";
import { SandboxSurface } from "../features/builder/SandboxSurface";


it("continues one waiting Sandbox run through operation choice and exact input", async () => {
  const agentId = "7db3745e-6f77-4b92-929c-4d2292fb3708";
  const agentRef = `agent-${agentId.replaceAll("-", "").slice(0, 20)}`;
  const buildId = "5c1ad911-849f-4ef6-aadb-b2a793ac4ae0";
  const runId = "9dc745fb-f283-4d94-8676-104137d4b597";
  const baseRun: SandboxRunView = {
    id: runId,
    agent_id: agentId,
    build_id: buildId,
    runtime_session_id: "session-exact",
    runtime_run_id: "runtime-run-exact",
    status: "waiting",
    message: "get product taxonomy",
    awaiting: "router",
    clarification: {
      question: "Which operation should I use: GetProductTagsId or GetProductTypesId?",
      candidate_operation_ids: ["GetProductTagsId", "GetProductTypesId"],
      candidate_choices: [
        { operation_id: "GetProductTagsId", label: "Retrieve a Product Tag" },
        { operation_id: "GetProductTypesId", label: "Retrieve a Product Type" },
      ],
      missing_input_names: [],
    },
    final_response: "Which operation should I use: GetProductTagsId or GetProductTypesId?",
    api_call_count: 0,
    routedeck_projection: { current: { node_id: "agent_runtime.home" }, legal_operations: [], suggested_actions: [], surfaces: { active: null, detail: [], review: [], status: [], error: [] } },
    events: [],
    failure_code: null,
    created_at: "2026-08-08T00:00:00Z",
    updated_at: "2026-08-08T00:00:00Z",
  };
  const inputRun: SandboxRunView = {
    ...baseRun,
    clarification: {
      question: "What value should I use for id?",
      candidate_operation_ids: ["GetProductTypesId"],
      candidate_choices: [{ operation_id: "GetProductTypesId", label: "Retrieve a Product Type" }],
      missing_input_names: ["id"],
    },
    final_response: "What value should I use for id?",
  };
  const completedRun: SandboxRunView = {
    ...inputRun,
    status: "succeeded",
    awaiting: null,
    clarification: null,
    final_response: "Product type loaded.",
    api_call_count: 1,
  };
  const runtimeClient = {
    builds: vi.fn(async () => ({
      agent_id: agentId,
      builds: [{
        id: buildId,
        agent_id: agentId,
        build_request_id: "request",
        design_revision_id: "design",
        agent_version: 1,
        status: "ready",
        runtime_build_hash: "a".repeat(64),
        model: "model",
        model_digest: "digest",
        allowed_operation_ids: ["GetProductTagsId", "GetProductTypesId"],
        navgraph_hash: "n".repeat(64),
        compiled_navgraph: { nodes: [], transitions: [] },
        frontend_contract: { nodes: {} },
        failure_code: null,
        failure_message: null,
        created_at: "2026-08-08T00:00:00Z",
        updated_at: "2026-08-08T00:00:00Z",
      }],
    })),
    sandbox: vi.fn()
      .mockResolvedValueOnce({ agent_id: agentId, runs: [baseRun] })
      .mockResolvedValueOnce({ agent_id: agentId, runs: [inputRun] })
      .mockResolvedValueOnce({ agent_id: agentId, runs: [completedRun] }),
  } as unknown as AgentRuntimeClient;
  const agentStore = new AgentStore({
    list: vi.fn(async () => ({
      agents: [{
        id: agentId,
        name: "Store Agent",
        description: "",
        instructions: "Use exact operations.",
        lifecycle: "active",
        current_version: 1,
        created_at: "2026-08-08T00:00:00Z",
        updated_at: "2026-08-08T00:00:00Z",
      }],
    })),
    listSources: vi.fn(async () => ({ attachments: [] })),
    listBuilds: vi.fn(async () => ({ builds: [] })),
    inspectDependencies: vi.fn(async () => ({
      agent_id: agentId,
      source_attachments: [],
      build_ids: [],
      blocks_delete: false,
    })),
  } as unknown as AgentClient);
  const dispatch = vi.fn(async () => ({
    disposition: "completed",
    outcome: "resumed",
    failure: null,
  }));
  const props = {
    surface: { surface_id: "sandbox.home", component: "sandbox.home", props: [] },
    slot: "active",
    props: { selected_agent_ref: agentRef },
    spec: {
      id: "sandbox.home",
      component: "sandbox.home",
      lifecycle: "stable",
      public_props_schema: {},
      affordances: [],
    },
    dispatchAffordance: dispatch,
  } as unknown as RouteDeckSurfaceComponentProps;

  render(
    <SandboxSurface
      {...props}
      agentStore={agentStore}
      runtimeClient={runtimeClient}
    />,
  );

  expect((await screen.findAllByText(baseRun.clarification!.question))[0]).toBeVisible();
  expect(screen.getByRole("heading", { name: "ToolRouter clarification subagent" })).toBeVisible();
  expect(screen.getByText("agent_runtime.home")).toBeVisible();
  expect(screen.getByRole("option", { name: "Retrieve a Product Type" })).toBeVisible();
  fireEvent.change(screen.getByLabelText("Operation"), {
    target: { value: "GetProductTypesId" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Continue same run" }));
  expect(await screen.findByLabelText("Value for id")).toBeVisible();
  fireEvent.change(screen.getByLabelText("Value for id"), {
    target: { value: "pt_exact" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Continue same run" }));

  await waitFor(() => expect(screen.getByText("Product type loaded.")).toBeVisible());
  expect(dispatch).toHaveBeenNthCalledWith(1, "resume", {
    agent_ref: agentRef,
    run_id: runId,
    message: "GetProductTypesId",
    selected_operation_id: "GetProductTypesId",
    answers: {},
  });
  expect(dispatch).toHaveBeenNthCalledWith(2, "resume", {
    agent_ref: agentRef,
    run_id: runId,
    message: "pt_exact",
    selected_operation_id: "GetProductTypesId",
    answers: { id: "pt_exact" },
  });
});
