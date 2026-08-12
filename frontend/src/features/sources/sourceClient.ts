import type { AuthorizedTransport } from "@/app/transports";
import type { ContractRevisionProposal, SourceView, StagedApiAttachment } from "./contracts";
import type {
  ToolRouterGraphEdge,
  ToolRouterGraphNode,
  ToolRouterGraphTraceFrame,
} from "@/integrations/toolrouter/semantic-graph/model";

export type { SourceRevision, SourceState, SourceView } from "./contracts";
import type { SourceDescriptionView, SourceDependencyView, StagedApiDescription } from "./contracts";
export type { ContractRevisionProposal } from "./contracts";

export type ApiGraphNode = ToolRouterGraphNode;

export type ApiGraphEdge = ToolRouterGraphEdge;

export interface ApiSemanticGroup {
  readonly id: string;
  readonly label: string;
  readonly operation_ids: readonly string[];
}

export interface ApiGraphPlaybackStage {
  readonly id: string;
  readonly status: string;
  readonly metrics: Readonly<Record<string, string | number | boolean>>;
  readonly warning_codes: readonly string[];
}

export type ApiGraphTraceFrame = ToolRouterGraphTraceFrame;

export interface ApiGraphView {
  readonly source_id: string;
  readonly revision_id: string;
  readonly artifact_revision_id: string;
  readonly assembler: string;
  readonly total_nodes: number;
  readonly total_edges: number;
  readonly nodes: readonly ApiGraphNode[];
  readonly edges: readonly ApiGraphEdge[];
  readonly semantic_groups: readonly ApiSemanticGroup[];
  readonly playback: readonly ApiGraphPlaybackStage[];
  readonly trace: readonly ApiGraphTraceFrame[];
}

export type ApiAuthenticationMethod = "none" | "api_key" | "bearer";

export interface ApiConnectionProfile {
  readonly id: string;
  readonly source_id: string;
  readonly revision_id: string;
  readonly profile_name: string;
  readonly environment: string;
  readonly base_url: string;
  readonly authentication_method: ApiAuthenticationMethod;
  readonly credential_name: string | null;
  readonly credential_reference_id: string | null;
  readonly credential_version: number | null;
  readonly created_at: string;
  readonly updated_at: string;
}

export interface ApiConnectionCheckRecord {
  readonly id: string;
  readonly execution_id: string;
  readonly source_id: string;
  readonly source_revision_id: string;
  readonly connection_profile_id: string;
  readonly credential_reference_id: string | null;
  readonly credential_version: number | null;
  readonly operation_id: "GetProductTypes" | "GetProductTags";
  readonly method: string;
  readonly path_template: string;
  readonly effective_contract_sha256: string;
  readonly status: "succeeded" | "failed";
  readonly status_code: number | null;
  readonly error_code: string | null;
  readonly public_message: string | null;
  readonly validation_issue_count: number;
  readonly validation_phases: readonly string[];
  readonly http_call_count: number;
  readonly started_at: string;
  readonly finished_at: string;
  readonly traces: readonly {
    readonly event: string;
    readonly occurred_at: string;
    readonly safe_details: Readonly<Record<string, string | number | boolean | null>>;
  }[];
}

export interface ApiOperationInventoryItem {
  readonly operation_id: string;
  readonly graph_node_id: string;
  readonly method: string;
  readonly path_template: string;
  readonly operation_class: string;
}

export interface ApiOperationCurationRecord {
  readonly schema_version: number;
  readonly id: string;
  readonly source_id: string;
  readonly source_revision_id: string;
  readonly artifact_revision_id: string;
  readonly inventory_fingerprint: string;
  readonly included_operation_ids: readonly string[];
  readonly excluded_operation_ids: readonly string[];
  readonly selected_by_owner_id: string;
  readonly selected_at: string;
  readonly previous_curation_id: string | null;
}

export interface ApiOperationCurationView {
  readonly source_id: string;
  readonly source_revision_id: string;
  readonly artifact_revision_id: string;
  readonly inventory_fingerprint: string;
  readonly operations: readonly ApiOperationInventoryItem[];
  readonly current: ApiOperationCurationRecord | null;
  readonly history: readonly ApiOperationCurationRecord[];
}

export type ApiRoutePlanState =
  | "ready"
  | "needs_input"
  | "needs_operation_choice"
  | "not_routable";

export interface ApiRoutePlanView {
  readonly plan_id: string;
  readonly record_id: string;
  readonly previous_record_id: string | null;
  readonly source_id: string;
  readonly source_revision_id: string;
  readonly profile_id: string;
  readonly curation_id: string;
  readonly inventory_fingerprint: string;
  readonly subset_fingerprint: string;
  readonly request_text: string;
  readonly state: ApiRoutePlanState;
  readonly steps: readonly {
    readonly query: string;
    readonly ranked_operations: readonly {
      readonly operation_id: string;
      readonly operation_label: string;
      readonly endpoint_id: string;
      readonly score: number;
    }[];
    readonly selected_operation_id: string | null;
    readonly method: string | null;
    readonly path_template: string | null;
    readonly http_safety: "read" | "write" | null;
  }[];
  readonly missing_inputs: readonly string[];
  readonly input_provenance: readonly {
    readonly name: string;
    readonly value: string | number | boolean;
    readonly source: "current_request" | "user_clarification";
  }[];
  readonly managed_parameters: readonly {
    readonly name: string;
    readonly location: "header";
    readonly authentication_method: "api_key";
    readonly source: "managed_by_profile";
  }[];
  readonly operation_choice: {
    readonly operation_id: string;
    readonly source: "user_clarification";
  } | null;
  readonly clarification_prompt: string | null;
  readonly created_at: string;
  readonly expires_at: string;
  readonly plan_fingerprint: string;
  readonly api_call_count: 0;
}

export interface ApiRoutedExecutionView {
  readonly result_id: string;
  readonly plan_id: string;
  readonly source_id: string;
  readonly source_revision_id: string;
  readonly operation_id: string;
  readonly method: string;
  readonly path_template: string;
  readonly safety: "read" | "write";
  readonly status: "succeeded" | "failed" | "outcome_unknown";
  readonly delivery: "not_sent" | "response_received" | "possibly_sent";
  readonly status_code: number | null;
  readonly response_media_type: string | null;
  readonly response_byte_count: number;
  readonly response_body_sha256: string | null;
  readonly error_code: string | null;
  readonly public_message: string | null;
  readonly validation_issue_count: number;
  readonly validation_phases: readonly string[];
  readonly outcome_verified: boolean | null;
  readonly http_call_count: number | null;
  readonly started_at: string;
  readonly finished_at: string;
  readonly traces: readonly {
    readonly event: string;
    readonly occurred_at: string;
    readonly safe_details: Readonly<Record<string, string | number | boolean | null>>;
  }[];
}

export interface RankedSourceItem {
  readonly item_id: string;
  readonly item_kind: string;
  readonly score: number;
}

export interface RetrievalResult {
  readonly query: string;
  readonly decision_type: string;
  readonly decision_reason: string;
  readonly decomposed: boolean;
  readonly steps: readonly {
    readonly query: string;
    readonly ranked_items: readonly RankedSourceItem[];
    readonly trace: Readonly<Record<string, unknown>>;
  }[];
  readonly missing_inputs: readonly string[];
  readonly ambiguity: Readonly<Record<string, unknown>> | null;
  readonly decision_evidence: Readonly<Record<string, unknown>>;
}

export interface EvalsetResult {
  readonly evalset_id: string;
  readonly status: "ready" | "quarantined" | "failed";
  readonly completed_count: number;
  readonly expected_count: number;
  readonly accepted_count: number;
  readonly quarantined_count: number;
  readonly terminal_status_counts: Readonly<Record<string, number>>;
  readonly offline_tokens: number;
  readonly generator_model: string;
  readonly generator_model_digest: string;
  readonly reviewer_model: string;
  readonly reviewer_model_digest: string;
  readonly accepted_tasks: readonly Readonly<Record<string, unknown>>[];
  readonly summary: Readonly<Record<string, unknown>>;
}

export class SourceClientError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "SourceClientError";
  }
}

export class SourceClient {
  private conversationId: string | null = null;

  constructor(private readonly transport: AuthorizedTransport) {}

  selectConversation(conversationId: string): void {
    if (!conversationId) {
      throw new Error("Conversation ID must be non-empty.");
    }
    this.conversationId = conversationId;
  }

  clearConversation(): void {
    this.conversationId = null;
  }

  async list(): Promise<readonly SourceView[]> {
    return this.request<readonly SourceView[]>("/api/sources");
  }

  async get(sourceId: string, revisionId?: string): Promise<SourceView> {
    const query = revisionId === undefined
      ? ""
      : `?${new URLSearchParams({ revision_id: revisionId }).toString()}`;
    return this.request<SourceView>(
      `/api/sources/${encodeURIComponent(sourceId)}${query}`,
    );
  }

  async getDescription(sourceId: string): Promise<SourceDescriptionView | null> {
    return this.request<SourceDescriptionView | null>(
      `/api/sources/${encodeURIComponent(sourceId)}/description`,
    );
  }

  async inspectDependencies(sourceId: string): Promise<SourceDependencyView> {
    return this.request<SourceDependencyView>(
      `/api/sources/${encodeURIComponent(sourceId)}/dependencies`,
    );
  }

  async inspectApiGraph(sourceId: string): Promise<ApiGraphView> {
    return this.request<ApiGraphView>(
      `/api/sources/${encodeURIComponent(sourceId)}/graph`,
    );
  }

  async listApiConnections(sourceId: string): Promise<readonly ApiConnectionProfile[]> {
    return this.request<readonly ApiConnectionProfile[]>(
      `/api/sources/${encodeURIComponent(sourceId)}/connections`,
    );
  }

  async listApiConnectionChecks(
    sourceId: string,
    revisionId: string,
  ): Promise<readonly ApiConnectionCheckRecord[]> {
    const query = new URLSearchParams({ revision_id: revisionId });
    return this.request<readonly ApiConnectionCheckRecord[]>(
      `/api/sources/${encodeURIComponent(sourceId)}/connection-checks?${query.toString()}`,
    );
  }

  async listContractRevisions(sourceId: string): Promise<readonly ContractRevisionProposal[]> {
    return this.request<readonly ContractRevisionProposal[]>(
      `/api/sources/${encodeURIComponent(sourceId)}/contract-revisions`,
    );
  }

  async inspectApiOperationCuration(
    sourceId: string,
    revisionId: string,
  ): Promise<ApiOperationCurationView> {
    const query = new URLSearchParams({ revision_id: revisionId });
    return this.request<ApiOperationCurationView>(
      `/api/sources/${encodeURIComponent(sourceId)}/operation-curation?${query.toString()}`,
    );
  }

  async currentApiRoutePlan(
    sourceId: string,
    revisionId: string,
  ): Promise<ApiRoutePlanView | null> {
    const query = new URLSearchParams({ revision_id: revisionId });
    return this.routePlanRequest<ApiRoutePlanView | null>(
      `/api/sources/${encodeURIComponent(sourceId)}/route-plans/current?${query.toString()}`,
    );
  }

  async createApiRoutePlan(
    sourceId: string,
    body: {
      readonly source_revision_id: string;
      readonly profile_id: string;
      readonly curation_id: string;
      readonly request_text: string;
      readonly provided_inputs: Readonly<Record<string, string | number | boolean>>;
    },
  ): Promise<ApiRoutePlanView> {
    return this.routePlanRequest<ApiRoutePlanView>(
      `/api/sources/${encodeURIComponent(sourceId)}/route-plans`,
      jsonRequest(body),
    );
  }

  async clarifyApiRoutePlan(
    sourceId: string,
    planId: string,
    body: {
      readonly source_revision_id: string;
      readonly expected_record_id: string;
      readonly answers: Readonly<Record<string, string | number | boolean>>;
    },
  ): Promise<ApiRoutePlanView> {
    return this.routePlanRequest<ApiRoutePlanView>(
      `/api/sources/${encodeURIComponent(sourceId)}/route-plans/${encodeURIComponent(planId)}/clarifications`,
      jsonRequest(body),
    );
  }

  async currentRoutedApiExecution(
    sourceId: string,
    planId: string,
  ): Promise<ApiRoutedExecutionView | null> {
    return this.routePlanRequest<ApiRoutedExecutionView | null>(
      `/api/sources/${encodeURIComponent(sourceId)}/route-plans/${encodeURIComponent(planId)}/execution`,
    );
  }

  async stageApiDefinition(name: string, file: File, description: File | null): Promise<StagedApiAttachment> {
    const body = new FormData();
    body.set("name", name);
    body.set("file", file);
    if (description !== null) body.set("description", description);
    return this.routePlanRequest<StagedApiAttachment>("/api/sources/api/attachments", {
      method: "POST",
      body,
    });
  }

  async currentStagedApiDefinition(): Promise<StagedApiAttachment | null> {
    return this.routePlanRequest<StagedApiAttachment | null>(
      "/api/sources/api/attachments/current",
    );
  }

  async stageApiDescription(file: File): Promise<StagedApiDescription> {
    const body = new FormData();
    body.set("file", file);
    return this.routePlanRequest<StagedApiDescription>(
      "/api/sources/api/description-attachments",
      { method: "POST", body },
    );
  }

  async currentStagedApiDescription(): Promise<StagedApiDescription | null> {
    return this.routePlanRequest<StagedApiDescription | null>(
      "/api/sources/api/description-attachments/current",
    );
  }

  async retrieve(
    sourceId: string,
    body: {
      readonly query: string;
      readonly top_k: number;
      readonly trace_mode: "bounded" | "full";
      readonly provided_params: Readonly<Record<string, unknown>> | null;
    },
  ): Promise<RetrievalResult> {
    return this.request<RetrievalResult>(
      `/api/sources/${encodeURIComponent(sourceId)}/retrieve`,
      jsonRequest(body),
    );
  }

  async generateEvalset(
    sourceId: string,
    body: {
      readonly evalset_id: string;
      readonly categories: readonly string[];
      readonly tasks_per_category: number;
      readonly max_generation_attempts: number;
      readonly max_review_attempts: number;
    },
  ): Promise<EvalsetResult> {
    return this.request<EvalsetResult>(
      `/api/sources/${encodeURIComponent(sourceId)}/evalsets`,
      jsonRequest(body),
    );
  }

  private async request<T>(url: string, init: RequestInit = {}): Promise<T> {
    let response: Response;
    try {
      response = await this.transport.fetch(url, init);
    } catch (error) {
      throw new SourceClientError(
        error instanceof Error ? error.message : "The Sources API is unavailable.",
        "source_network_failure",
        0,
      );
    }
    if (!response.ok) {
      const problem = await readProblem(response);
      throw new SourceClientError(
        problem.message ?? `The Sources request failed (${response.status}).`,
        problem.code ?? "source_request_failed",
        response.status,
      );
    }
    return response.json() as Promise<T>;
  }

  private async routePlanRequest<T>(
    url: string,
    init: RequestInit = {},
  ): Promise<T> {
    if (this.conversationId === null) {
      throw new SourceClientError(
        "Corpus has not selected a conversation for route preparation.",
        "source_conversation_required",
        0,
      );
    }
    const headers = new Headers(init.headers);
    headers.set("X-Corpus-Conversation-ID", this.conversationId);
    return this.request<T>(url, { ...init, headers });
  }
}


function jsonRequest(value: unknown): RequestInit {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(value),
  };
}


async function readProblem(
  response: Response,
): Promise<{ code?: string; message?: string }> {
  try {
    return await response.json() as { code?: string; message?: string };
  } catch {
    return {};
  }
}
