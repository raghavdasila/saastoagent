import { expect, it, vi } from "vitest";

import {
  markInitialSessionHealthy,
  recoverInitialSession,
} from "../app/sessionRecovery";


function storage() {
  const values = new Map<string, string>();
  return {
    getItem: (key: string) => values.get(key) ?? null,
    setItem: (key: string, value: string) => values.set(key, value),
    removeItem: (key: string) => values.delete(key),
  };
}


it("clears a broken selected session and reopens Corpus once", async () => {
  const state = storage();
  const recover = vi.fn(async () => undefined);
  const reopen = vi.fn();

  expect(await recoverInitialSession(state, recover, reopen)).toBe(true);
  expect(recover).toHaveBeenCalledOnce();
  expect(reopen).toHaveBeenCalledOnce();
  expect(await recoverInitialSession(state, recover, reopen)).toBe(false);
});


it("allows a future recovery after a healthy session loads", async () => {
  const state = storage();

  await recoverInitialSession(state, async () => undefined, () => undefined);
  markInitialSessionHealthy(state);

  expect(
    await recoverInitialSession(state, async () => undefined, () => undefined),
  ).toBe(true);
});
