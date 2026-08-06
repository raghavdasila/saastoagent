export interface AnonymousPrincipal {
  type: "anonymous";
}

export interface OwnerPrincipal {
  type: "owner";
  owner: { email: string; display_name: string | null; is_verified: boolean };
  organization: { name: string; slug: string };
  membership: { role: "owner" | "admin" | "member" };
}

export interface TokenPair {
  access_token: string;
  access_expires_at: string;
  refresh_token: string;
  refresh_idle_expires_at: string;
  refresh_absolute_expires_at: string;
  principal: AnonymousPrincipal | OwnerPrincipal;
}

export interface RefreshCredentialStore {
  load(): Promise<string | null>;
  save(refreshToken: string): Promise<void>;
  clear(): Promise<void>;
}

export interface RefreshLock {
  run<T>(action: () => Promise<T>): Promise<T>;
}

export type CredentialRevocationHandler = () => Promise<void>;

export class ClientSessionManager {
  private current: TokenPair | null = null;
  private bootstrapPromise: Promise<TokenPair> | null = null;
  private credentialRevocationHandler: CredentialRevocationHandler | null = null;

  constructor(
    private readonly store: RefreshCredentialStore,
    private readonly lock: RefreshLock,
    private readonly fetcher: typeof fetch = globalThis.fetch,
  ) {}

  get principal(): TokenPair["principal"] | null {
    return this.current?.principal ?? null;
  }

  async bootstrap(): Promise<TokenPair> {
    this.bootstrapPromise ??= this.restoreOrCreateAnonymous();
    try {
      return await this.bootstrapPromise;
    } finally {
      this.bootstrapPromise = null;
    }
  }

  async authorizedFetch(
    input: RequestInfo | URL,
    init: RequestInit = {},
  ): Promise<Response> {
    const token = this.current ?? await this.bootstrap();
    let response = await this.fetchWithToken(input, init, token.access_token);
    if (response.status !== 401) {
      await this.acceptOperationCredentials(response);
      return response;
    }
    const refreshed = await this.refresh();
    response = await this.fetchWithToken(input, init, refreshed.access_token);
    await this.acceptOperationCredentials(response);
    return response;
  }

  async accept(pair: TokenPair): Promise<void> {
    validateTokenPair(pair);
    await this.store.save(pair.refresh_token);
    this.current = Object.freeze(pair);
  }

  setCredentialRevocationHandler(
    handler: CredentialRevocationHandler,
  ): () => void {
    if (this.credentialRevocationHandler !== null) {
      throw new AuthenticationUnavailableError(
        "Corpus already has a credential-revocation coordinator.",
      );
    }
    this.credentialRevocationHandler = handler;
    return () => {
      if (this.credentialRevocationHandler === handler) {
        this.credentialRevocationHandler = null;
      }
    };
  }

  async signOut(): Promise<void> {
    if (this.current !== null) {
      await this.fetchWithToken(
        "/api/auth/sign-out",
        { method: "POST" },
        this.current.access_token,
      );
    }
    this.current = null;
    await this.store.clear();
  }

  private async restoreOrCreateAnonymous(): Promise<TokenPair> {
    const refreshToken = await this.store.load();
    if (refreshToken !== null) {
      try {
        return await this.refresh();
      } catch (error) {
        if (
          !(error instanceof AuthenticationUnavailableError) ||
          error.status !== 401
        ) {
          throw error;
        }
        await this.store.clear();
      }
    }
    const response = await this.fetcher("/api/auth/anonymous", { method: "POST" });
    const pair = await tokenResponse(response);
    await this.accept(pair);
    return pair;
  }

  private refresh(): Promise<TokenPair> {
    return this.lock.run(async () => {
      const refreshToken = await this.store.load();
      if (refreshToken === null) {
        throw new AuthenticationUnavailableError("No refresh credential is available.");
      }
      const response = await this.fetcher("/api/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      const pair = await tokenResponse(response);
      await this.accept(pair);
      return pair;
    });
  }

  private fetchWithToken(
    input: RequestInfo | URL,
    init: RequestInit,
    token: string,
  ): Promise<Response> {
    const headers = new Headers(init.headers);
    headers.set("Authorization", `Bearer ${token}`);
    return this.fetcher(input, { ...init, headers, credentials: "omit" });
  }

  private async acceptOperationCredentials(response: Response): Promise<void> {
    if (response.headers.get("X-Corpus-Auth-Revoked") === "true") {
      this.current = null;
      await this.store.clear();
      const handler = this.credentialRevocationHandler;
      if (handler === null) {
        throw new AuthenticationUnavailableError(
          "Corpus cannot complete credential revocation without an application coordinator.",
        );
      }
      await handler();
      return;
    }
    const serialized = response.headers.get("X-Corpus-Auth-Tokens");
    if (serialized === null) return;
    let pair: TokenPair;
    try {
      pair = JSON.parse(serialized) as TokenPair;
    } catch (error) {
      throw new AuthenticationUnavailableError(
        "Corpus returned invalid operation credentials.",
        null,
        { cause: error },
      );
    }
    await this.accept(pair);
  }
}

export class AuthenticationUnavailableError extends Error {
  constructor(
    message: string,
    readonly status: number | null = null,
    options?: ErrorOptions,
  ) {
    super(message, options);
  }
}

async function tokenResponse(response: Response): Promise<TokenPair> {
  if (!response.ok) {
    const body = await response.json().catch(() => null) as
      | { message?: string }
      | null;
    throw new AuthenticationUnavailableError(
      body?.message ?? `Authentication failed with HTTP ${response.status}.`,
      response.status,
    );
  }
  const pair = await response.json() as TokenPair;
  validateTokenPair(pair);
  return pair;
}

function validateTokenPair(pair: TokenPair): void {
  if (
    typeof pair.access_token !== "string" || pair.access_token.length === 0 ||
    typeof pair.refresh_token !== "string" || pair.refresh_token.length === 0 ||
    (pair.principal.type !== "anonymous" && pair.principal.type !== "owner")
  ) {
    throw new AuthenticationUnavailableError("Corpus returned invalid credentials.");
  }
}
