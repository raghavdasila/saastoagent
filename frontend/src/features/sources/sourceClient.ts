export type SourceState = "processing" | "ready" | "failed";

export interface SourceRevision {
  readonly revision_id: string;
  readonly source_id: string;
  readonly original_filename: string;
  readonly content_sha256: string;
  readonly state: SourceState;
  readonly created_at: string;
  readonly updated_at: string;
  readonly summary: Readonly<Record<string, unknown>>;
  readonly failure_code: string | null;
  readonly failure_message: string | null;
}

export interface SourceView {
  readonly source_id: string;
  readonly connector_key: string;
  readonly display_name: string;
  readonly created_at: string;
  readonly updated_at: string;
  readonly revision: SourceRevision;
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

class SourceClient {
  async list(): Promise<readonly SourceView[]> {
    return request<readonly SourceView[]>("/api/sources");
  }

  async uploadApi(name: string, file: File): Promise<SourceView> {
    const body = new FormData();
    body.set("name", name);
    body.set("file", file);
    return request<SourceView>("/api/sources/api", {
      method: "POST",
      body,
    });
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
    return request<RetrievalResult>(
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
    return request<EvalsetResult>(
      `/api/sources/${encodeURIComponent(sourceId)}/evalsets`,
      jsonRequest(body),
    );
  }
}


async function request<T>(url: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, { credentials: "include", ...init });
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


export const sourceClient = new SourceClient();
