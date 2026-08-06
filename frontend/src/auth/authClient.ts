export interface AuthTransport {
  fetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response>;
}

export interface OwnerSessionView {
  type?: "owner";
  owner: {
    email: string;
    display_name: string | null;
    is_verified: boolean;
  };
  organization: { name: string; slug: string };
  membership: { role: "owner" | "admin" | "member" };
  route_session_state?: "adopted" | "resumed";
}

interface AnonymousSessionView {
  type: "anonymous";
}

export class AuthProblemError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

let authTransport: AuthTransport | null = null;
let revokeClientCredentials: (() => Promise<void>) | null = null;

export function configureOwnerAuthClient(options: {
  transport: AuthTransport;
  signOut: () => Promise<void>;
}): void {
  authTransport = options.transport;
  revokeClientCredentials = options.signOut;
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  if (authTransport === null) {
    throw new AuthProblemError(
      "authentication_transport_unconfigured",
      "Corpus owner authentication transport is unavailable.",
      0,
    );
  }
  const response = await authTransport.fetch(path, {
    ...init,
    headers: {
      ...(init.body === undefined ? {} : { "Content-Type": "application/json" }),
      ...init.headers,
    },
  });
  if (!response.ok) {
    const problem = await response.json().catch(() => null) as
      | { code?: string; message?: string }
      | null;
    throw new AuthProblemError(
      problem?.code ?? "authentication_failed",
      problem?.message ?? "Authentication failed.",
      response.status,
    );
  }
  if (response.status === 204 || response.status === 202) return undefined as T;
  return await response.json() as T;
}

export const ownerAuthClient = Object.freeze({
  async session(): Promise<OwnerSessionView | null> {
    const result = await request<OwnerSessionView | AnonymousSessionView>(
      "/api/auth/session",
    );
    return result.type === "anonymous" ? null : result;
  },
  async signOut(): Promise<void> {
    if (revokeClientCredentials !== null) {
      await revokeClientCredentials();
      return;
    }
    await request<void>("/api/auth/sign-out", { method: "POST" });
  },
});
