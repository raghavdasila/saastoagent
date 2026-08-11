import { describe, expect, it } from "vitest";

import { presentCorpusStatus } from "../app/corpusStatus";

describe("Corpus RouteDeck status presentation", () => {
  it("keeps synchronization work distinct from terminal product failure", () => {
    expect(presentCorpusStatus({ code: "ready", message: null, syncStatus: "resyncing" }))
      .toEqual({ label: "Working…", detail: null, tone: "working" });

    expect(presentCorpusStatus({
      code: "builder_unavailable",
      message: "Each accepted API Source revision needs a saved connection.",
      syncStatus: "live",
    })).toEqual({
      label: "Action needed",
      detail: "Each accepted API Source revision needs a saved connection.",
      tone: "error",
    });
  });

  it("presents review and uncertain outcomes without calling them progress", () => {
    expect(presentCorpusStatus({
      code: "review_pending",
      message: "This action requires explicit review.",
      syncStatus: "live",
    })).toEqual({
      label: "Approval required",
      detail: "This action requires explicit review.",
      tone: "review",
    });

    expect(presentCorpusStatus({
      code: "external_outcome_unknown",
      message: "Delivery may have occurred.",
      syncStatus: "live",
    })).toEqual({
      label: "Check outcome",
      detail: "Delivery may have occurred.",
      tone: "warning",
    });
  });
});
