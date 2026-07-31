import { describe, expect, it, vi } from "vitest";

import {
  ClientSessionManager,
  type RefreshCredentialStore,
  type TokenPair,
} from "../app/clientSession";

const ANONYMOUS: TokenPair = {
  access_token: "access-one",
  access_expires_at: "2026-07-30T12:15:00Z",
  refresh_token: "refresh-one",
  refresh_idle_expires_at: "2026-08-06T12:00:00Z",
  refresh_absolute_expires_at: "2026-08-29T12:00:00Z",
  principal: { type: "anonymous" },
};

describe("client bearer session", () => {
  it("creates an anonymous identity and sends its bearer token", async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(json(ANONYMOUS))
      .mockResolvedValueOnce(json({ ok: true }));
    const store = memoryStore();
    const manager = new ClientSessionManager(store, immediateLock(), fetcher);
    await manager.bootstrap();
    await manager.authorizedFetch("/api/conversations");
    expect(store.value).toBe("refresh-one");
    expect(new Headers(fetcher.mock.calls[1][1].headers).get("Authorization"))
      .toBe("Bearer access-one");
  });

  it("rotates a stored refresh token before issuing requests", async () => {
    const rotated = { ...ANONYMOUS, access_token: "access-two", refresh_token: "refresh-two" };
    const fetcher = vi.fn()
      .mockResolvedValueOnce(json(rotated))
      .mockResolvedValueOnce(json({ ok: true }));
    const store = memoryStore("refresh-one");
    const manager = new ClientSessionManager(store, immediateLock(), fetcher);
    await manager.bootstrap();
    expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual({ refresh_token: "refresh-one" });
    expect(store.value).toBe("refresh-two");
  });

  it("re-reads the refresh credential after acquiring the cross-tab lock", async () => {
    const rotated = { ...ANONYMOUS, access_token: "access-two", refresh_token: "refresh-two" };
    const fetcher = vi.fn().mockResolvedValueOnce(json(rotated));
    const store = memoryStore("refresh-stale");
    const lock = {
      async run<T>(action: () => Promise<T>): Promise<T> {
        store.value = "refresh-current";
        return action();
      },
    };
    const manager = new ClientSessionManager(store, lock, fetcher);
    await manager.bootstrap();
    expect(JSON.parse(fetcher.mock.calls[0][1].body)).toEqual({
      refresh_token: "refresh-current",
    });
  });

  it("replaces only an expired refresh session with a new anonymous identity", async () => {
    const fetcher = vi.fn()
      .mockResolvedValueOnce(json({ message: "expired" }, 401))
      .mockResolvedValueOnce(json(ANONYMOUS, 201));
    const store = memoryStore("refresh-expired");
    const manager = new ClientSessionManager(store, immediateLock(), fetcher);
    await manager.bootstrap();
    expect(fetcher).toHaveBeenCalledTimes(2);
    expect(store.value).toBe("refresh-one");
  });

  it("does not erase credentials when refresh fails for a server reason", async () => {
    const fetcher = vi.fn().mockResolvedValueOnce(json({ message: "unavailable" }, 503));
    const store = memoryStore("refresh-current");
    const manager = new ClientSessionManager(store, immediateLock(), fetcher);
    await expect(manager.bootstrap()).rejects.toMatchObject({ status: 503 });
    expect(fetcher).toHaveBeenCalledTimes(1);
    expect(store.value).toBe("refresh-current");
  });

  it("accepts a rotated owner token pair from a supervised auth operation", async () => {
    const owner: TokenPair = {
      ...ANONYMOUS,
      access_token: "owner-access",
      refresh_token: "owner-refresh",
      principal: {
        type: "owner",
        owner: { email: "owner@example.com", display_name: null, is_verified: false },
        organization: { name: "Owner Workspace", slug: "owner-workspace" },
        membership: { role: "owner" },
      },
    };
    const operationResponse = json({ ok: true });
    operationResponse.headers.set("X-Corpus-Auth-Tokens", JSON.stringify(owner));
    const fetcher = vi.fn()
      .mockResolvedValueOnce(json(ANONYMOUS))
      .mockResolvedValueOnce(operationResponse)
      .mockResolvedValueOnce(json({ ok: true }));
    const store = memoryStore();
    const manager = new ClientSessionManager(store, immediateLock(), fetcher);
    await manager.bootstrap();
    await manager.authorizedFetch("/api/routedeck/dispatch", { method: "POST" });
    await manager.authorizedFetch("/api/auth/session");
    expect(store.value).toBe("owner-refresh");
    expect(new Headers(fetcher.mock.calls[2][1].headers).get("Authorization"))
      .toBe("Bearer owner-access");
  });
});

function json(value: unknown, status = 200) {
  return new Response(JSON.stringify(value), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function immediateLock() {
  return { run: <T>(action: () => Promise<T>) => action() };
}

function memoryStore(initial: string | null = null): RefreshCredentialStore & { value: string | null } {
  const store = {
    value: initial,
    async load() { return store.value; },
    async save(token: string) { store.value = token; },
    async clear() { store.value = null; },
  };
  return store;
}
