import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";

import { Composer } from "../app/Composer";

it("stages one exact owner attachment before chat without pre-processing or exposing its ID", async () => {
  const order: string[] = [];
  const onUploadApiSource = vi.fn(async (file: File) => {
    order.push(`upload:${file.name}`);
    return { attachmentId: "attachment-0001", displayName: "catalog" };
  });
  const onSend = vi.fn(async (message: string) => {
    order.push("send");
    expect(message).toBe(
      'Build an agent from this API.\n\nI attached the API definition "catalog" to this conversation.',
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
  expect(onSend.mock.calls[0]?.[0]).not.toContain("attachment-0001");
  expect(screen.getByText("No API file attached")).toBeVisible();
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
