export interface CorpusStatusInput {
  code: string;
  message: string | null;
  syncStatus: string;
}

export interface CorpusStatusPresentation {
  label: string;
  detail: string | null;
  tone: "ready" | "working" | "review" | "warning" | "error";
}

const WORKING_SYNC_STATES = new Set([
  "idle",
  "bootstrapping",
  "connecting",
  "navigating",
  "resync_required",
  "resyncing",
]);

export function presentCorpusStatus({
  code,
  message,
  syncStatus,
}: CorpusStatusInput): CorpusStatusPresentation {
  if (code === "ready" && WORKING_SYNC_STATES.has(syncStatus)) {
    return { label: "Working…", detail: null, tone: "working" };
  }
  if (code === "ready" && syncStatus === "live") {
    return { label: "Ready", detail: null, tone: "ready" };
  }
  if (code === "review_pending") {
    return {
      label: "Approval required",
      detail: message,
      tone: "review",
    };
  }
  if (code === "external_outcome_unknown") {
    return {
      label: "Check outcome",
      detail: message,
      tone: "warning",
    };
  }
  return {
    label: "Action needed",
    detail: message,
    tone: "error",
  };
}

