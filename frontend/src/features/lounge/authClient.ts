export interface OwnerSessionView {
  owner: {
    email: string;
    display_name: string | null;
    is_verified: boolean;
  };
  organization: { name: string; slug: string };
  membership: { role: "owner" | "admin" | "member" };
  route_session_state: "adopted" | "resumed";
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

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const response = await fetch(path, {
    credentials: "same-origin",
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
  register(input: { email: string; password: string; display_name?: string }) {
    return request<OwnerSessionView>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },
  signIn(input: { email: string; password: string }) {
    return request<OwnerSessionView>("/api/auth/sign-in", {
      method: "POST",
      body: JSON.stringify(input),
    });
  },
  session() {
    return request<OwnerSessionView>("/api/auth/session");
  },
  signOut() {
    return request<void>("/api/auth/sign-out", { method: "POST", body: "{}" });
  },
  sendVerification() {
    return request<void>("/api/auth/verification-email", { method: "POST", body: "{}" });
  },
  verify(token: string) {
    return request<void>("/api/auth/verify", {
      method: "POST",
      body: JSON.stringify({ token }),
    });
  },
  requestPasswordReset(email: string) {
    return request<void>("/api/auth/password-reset/request", {
      method: "POST",
      body: JSON.stringify({ email }),
    });
  },
  confirmPasswordReset(token: string, newPassword: string) {
    return request<void>("/api/auth/password-reset/confirm", {
      method: "POST",
      body: JSON.stringify({ token, new_password: newPassword }),
    });
  },
  recover() {
    return request<void>("/api/auth/recover", { method: "POST", body: "{}" });
  },
});
