import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { RouteDeckBootstrapActionRequiredState } from "@routedeck/react";
import { expect, it, vi } from "vitest";

import { CorpusRecoveryCoordinator } from "../app/CorpusRecoveryCoordinator";

it.each([
  ["navigation", "abandon_navigation"],
  ["resync", "resync"],
] as const)("recovers %s internally", async (reason, actionKind) => {
  const run = vi.fn(async () => undefined);
  render(
    <CorpusRecoveryCoordinator
      state={recovery(reason, actionKind, run)}
      replaceConversation={vi.fn()}
    />,
  );
  await waitFor(() => expect(run).toHaveBeenCalledOnce());
  expect(screen.queryByText(/RouteDeck|session recovery|resync/i)).toBeNull();
});

it.each(["resume_expired", "resume_missing", "resume_contract_mismatch"] as const)(
  "replaces the Corpus conversation for %s",
  async (reason) => {
    const replaceConversation = vi.fn(async () => undefined);
    render(
      <CorpusRecoveryCoordinator
        state={recovery(reason)}
        replaceConversation={replaceConversation}
      />,
    );
    await waitFor(() => expect(replaceConversation).toHaveBeenCalledOnce());
  },
);

it("fails closed with Corpus-owned copy and retries the same policy", async () => {
  const run = vi.fn()
    .mockRejectedValueOnce(new Error("private RouteDeck failure"))
    .mockResolvedValueOnce(undefined);
  render(
    <CorpusRecoveryCoordinator
      state={recovery("resync", "resync", run)}
      replaceConversation={vi.fn()}
    />,
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Corpus is temporarily unavailable",
  );
  expect(screen.queryByText(/RouteDeck|resync/i)).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  await waitFor(() => expect(run).toHaveBeenCalledTimes(2));
});

it("fails closed for invalid framework state without exposing its details", async () => {
  render(
    <CorpusRecoveryCoordinator
      state={recovery("invalid_state")}
      replaceConversation={vi.fn()}
    />,
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Corpus is temporarily unavailable",
  );
  expect(screen.queryByText(/invalid_state|RouteDeck/i)).toBeNull();
});

it("fails closed after the client runtime is disposed", async () => {
  render(
    <CorpusRecoveryCoordinator
      state={{
        phase: "disposed",
        syncStatus: "disposed",
        busy: false,
        error: { code: "disposed", message: "private RouteDeck failure" },
        actions: [],
      }}
      replaceConversation={vi.fn()}
    />,
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Corpus is temporarily unavailable",
  );
  expect(screen.queryByText(/disposed|RouteDeck/i)).toBeNull();
});

function recovery(
  reason: RouteDeckBootstrapActionRequiredState["reason"],
  actionKind?: RouteDeckBootstrapActionRequiredState["actions"][number]["kind"],
  run = vi.fn(async () => undefined),
): RouteDeckBootstrapActionRequiredState {
  return {
    phase: "recovery",
    syncStatus: "error",
    reason,
    busy: false,
    activeAction: null,
    error: { code: "private", message: "private RouteDeck failure" },
    actions: actionKind === undefined ? [] : [{ kind: actionKind, run }],
  };
}
