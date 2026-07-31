import {
  AuthenticationUnavailableError,
  type RefreshCredentialStore,
  type RefreshLock,
} from "./clientSession";

/** Browser-only persistence and cross-tab rotation adapters. */
export function createBrowserRefreshLock(navigatorTarget: Navigator): RefreshLock {
  const locks = (navigatorTarget as Navigator & {
    locks?: { request<T>(name: string, callback: () => Promise<T>): Promise<T> };
  }).locks;
  if (locks === undefined) {
    throw new AuthenticationUnavailableError(
      "This browser cannot coordinate rotating Corpus credentials.",
    );
  }
  return { run: (action) => locks.request("corpus-auth-refresh", action) };
}

export function createIndexedDbCredentialStore(
  indexedDb: IDBFactory = globalThis.indexedDB,
): RefreshCredentialStore {
  const open = () => new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDb.open("corpus-auth", 1);
    request.onupgradeneeded = () => {
      if (!request.result.objectStoreNames.contains("credentials")) {
        request.result.createObjectStore("credentials");
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
  const transact = async <T>(
    mode: IDBTransactionMode,
    operation: (store: IDBObjectStore) => IDBRequest<T>,
  ): Promise<T> => {
    const database = await open();
    try {
      const transaction = database.transaction("credentials", mode);
      const request = operation(transaction.objectStore("credentials"));
      return await new Promise<T>((resolve, reject) => {
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
    } finally {
      database.close();
    }
  };
  return {
    async load() {
      const value = await transact<unknown>("readonly", (store) =>
        store.get("refresh_token"),
      );
      return typeof value === "string" ? value : null;
    },
    save: (token) => transact("readwrite", (store) =>
      store.put(token, "refresh_token"),
    ).then(() => undefined),
    clear: () => transact("readwrite", (store) =>
      store.delete("refresh_token"),
    ).then(() => undefined),
  };
}
