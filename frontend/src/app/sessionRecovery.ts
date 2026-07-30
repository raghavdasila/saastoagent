const RECOVERY_MARKER = "corpus.initial-session-recovery.v1";

interface RecoveryStorage {
  getItem(key: string): string | null;
  setItem(key: string, value: string): void;
  removeItem(key: string): void;
}

export async function recoverInitialSession(
  storage: RecoveryStorage,
  recover: () => Promise<void>,
  reopen: () => void,
): Promise<boolean> {
  if (storage.getItem(RECOVERY_MARKER) === "attempted") return false;
  storage.setItem(RECOVERY_MARKER, "attempted");
  await recover();
  reopen();
  return true;
}

export function markInitialSessionHealthy(storage: RecoveryStorage): void {
  storage.removeItem(RECOVERY_MARKER);
}
