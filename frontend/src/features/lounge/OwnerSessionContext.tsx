import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  AuthProblemError,
  ownerAuthClient,
  type OwnerSessionView,
} from "./authClient";

interface OwnerSessionState {
  session: OwnerSessionView | null;
  loading: boolean;
  setSession(session: OwnerSessionView | null): void;
  refresh(): Promise<OwnerSessionView | null>;
}

const OwnerSessionContext = createContext<OwnerSessionState | null>(null);

export function OwnerSessionProvider({
  children,
  initialSession = null,
  loadSession = true,
}: {
  children: ReactNode;
  initialSession?: OwnerSessionView | null;
  loadSession?: boolean;
}) {
  const [session, setSession] = useState<OwnerSessionView | null>(initialSession);
  const [loading, setLoading] = useState(loadSession);
  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const current = await ownerAuthClient.session();
      setSession(current);
      return current;
    } catch (error) {
      if (error instanceof AuthProblemError && error.status === 401) {
        setSession(null);
        return null;
      } else {
        throw error;
      }
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    if (loadSession) void refresh().catch(() => setLoading(false));
  }, [loadSession, refresh]);
  const value = useMemo(
    () => ({ session, loading, setSession, refresh }),
    [loading, refresh, session],
  );
  return (
    <OwnerSessionContext.Provider value={value}>
      {children}
    </OwnerSessionContext.Provider>
  );
}

export function useOwnerSession(): OwnerSessionState {
  const value = useContext(OwnerSessionContext);
  if (value === null) throw new Error("OwnerSessionProvider is required.");
  return value;
}
