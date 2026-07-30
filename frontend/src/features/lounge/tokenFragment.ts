import { useState } from "react";

export type AuthTokenPurpose = "password_reset" | "verification";

interface AuthTokenBrowser {
  location: Pick<Location, "hash" | "pathname" | "search">;
  history: Pick<History, "replaceState" | "state">;
}

const capturedTokens = new Map<AuthTokenPurpose, string>();

export function captureAuthTokenFragment(browser: AuthTokenBrowser): void {
  const purpose = purposeForPath(browser.location.pathname);
  if (purpose === null || !browser.location.hash) return;
  const token = new URLSearchParams(browser.location.hash.slice(1)).get("token");
  if (token !== null) capturedTokens.set(purpose, token);
  browser.history.replaceState(
    browser.history.state,
    "",
    `${browser.location.pathname}${browser.location.search}`,
  );
}

export function clearCapturedTokenFragment(purpose: AuthTokenPurpose): void {
  capturedTokens.delete(purpose);
}

export function useCapturedTokenFragment(
  purpose: AuthTokenPurpose,
): string | null {
  const [token] = useState(() => {
    captureAuthTokenFragment(window);
    return capturedTokens.get(purpose) ?? null;
  });
  return token;
}

function purposeForPath(pathname: string): AuthTokenPurpose | null {
  if (pathname === "/verify") return "verification";
  if (pathname === "/reset-password") return "password_reset";
  return null;
}
