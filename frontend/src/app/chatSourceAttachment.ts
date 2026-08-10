import type { RouteDeckDispatchResult } from "@routedeck/core";

import type { ChatSourceUpload } from "./Composer";

type Dispatch = (
  operationId: string,
  argumentsValue?: Readonly<Record<string, string>>,
) => Promise<RouteDeckDispatchResult>;

export async function uploadAndAttachApiDefinition(options: {
  file: File;
  agentRef: string;
  dispatch: Dispatch;
  upload(file: File): Promise<ChatSourceUpload>;
}): Promise<ChatSourceUpload> {
  const opened = await options.dispatch("agents.open_source_creation", {
    agent_ref: options.agentRef,
  });
  requireCompleted(opened, "Corpus could not open Source creation for this Agent.");

  const uploaded = await options.upload(options.file);
  const attached = await options.dispatch("agents.attach_created_source", {
    agent_ref: options.agentRef,
    source_id: uploaded.sourceId,
  });
  requireCompleted(attached, "Corpus could not attach the processed API Source.");
  return uploaded;
}

function requireCompleted(result: RouteDeckDispatchResult, fallback: string): void {
  if (result.disposition !== "completed") {
    throw new Error(result.failure?.public_message || fallback);
  }
}
