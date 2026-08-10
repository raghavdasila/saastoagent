import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import { Composer } from "../app/Composer";
import { uploadAndAttachApiDefinition } from "../app/chatSourceAttachment";

it("processes one exact owner Source without putting its internal ID in chat", async () => {
  const order: string[] = [];
  const onUploadApiSource = vi.fn(async (file: File) => {
    order.push(`upload:${file.name}`);
    return { sourceId: "source-ready-001", displayName: "catalog" };
  });
  const onSend = vi.fn(async (message: string) => {
    order.push("send");
    expect(message).toBe(
      'Build an agent from this API.\n\nI attached the API definition "catalog".',
    );
  });
  render(
    <Composer
      disabled={false}
      onSend={onSend}
      onUploadApiSource={onUploadApiSource}
      onCancel={() => undefined}
    />,
  );

  const file = new File(["openapi: 3.0.0"], "catalog.yaml", { type: "text/yaml" });
  fireEvent.change(screen.getByLabelText("Attach API definition"), {
    target: { files: [file] },
  });
  fireEvent.change(screen.getByLabelText("Message the assistant"), {
    target: { value: "Build an agent from this API." },
  });
  fireEvent.click(screen.getByRole("button", { name: "Send message" }));

  await waitFor(() => expect(onSend).toHaveBeenCalledTimes(1));
  expect(order).toEqual(["upload:catalog.yaml", "send"]);
  expect(onSend.mock.calls[0]?.[0]).not.toContain("source-ready-001");
  expect(screen.getByText("No API file attached")).toBeVisible();
});

it("opens Source creation and attaches the exact processed Source before chat", async () => {
  const calls: Array<readonly [string, Readonly<Record<string, unknown>>]> = [];
  const dispatch = vi.fn(async (
    operationId: string,
    argumentsValue?: Readonly<Record<string, string>>,
  ) => {
    calls.push([operationId, argumentsValue ?? {}]);
    return {
      disposition: "completed" as const,
      operation_id: operationId,
      outcome: operationId === "agents.open_source_creation" ? "opened" : "attached",
      session_version: calls.length + 1,
      projection_version: calls.length + 1,
      request_id: `request-${calls.length}`,
      evidence: {
        attempt_id: `attempt-${calls.length}`,
        phases: [],
        request_fingerprint: `fingerprint-${calls.length}`,
        source: "surface" as const,
      },
    };
  });
  const file = new File(["openapi: 3.0.0"], "catalog.yaml");

  const result = await uploadAndAttachApiDefinition({
    file,
    agentRef: "agent-current",
    dispatch,
    upload: vi.fn(async () => ({
      sourceId: "source-ready-001",
      displayName: "catalog",
    })),
  });

  expect(result.displayName).toBe("catalog");
  expect(calls).toEqual([
    ["agents.open_source_creation", { agent_ref: "agent-current" }],
    ["agents.attach_created_source", {
      agent_ref: "agent-current",
      source_id: "source-ready-001",
    }],
  ]);
});

it("keeps API attachment unavailable when no authenticated Source uploader is composed", () => {
  render(
    <Composer
      disabled={false}
      onSend={vi.fn(async () => undefined)}
      onCancel={() => undefined}
    />,
  );
  expect(screen.queryByLabelText("Attach API definition")).not.toBeInTheDocument();
});
