import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { expect, it, vi } from "vitest";

import { Composer } from "../app/Composer";
import { OwnerSessionProvider } from "../features/lounge/OwnerSessionContext";
import { ResetPasswordSurface } from "../features/lounge/ResetPasswordSurface";
import { VerifyEmailSurface } from "../features/lounge/VerifyEmailSurface";
import {
  captureAuthTokenFragment,
  clearCapturedTokenFragment,
} from "../features/lounge/tokenFragment";


it("captures a reset token in memory and immediately removes the URL fragment", async () => {
  clearCapturedTokenFragment("password_reset");
  window.history.replaceState({}, "", "/reset-password#token=one-time-token");
  const fetch = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => ({
    ok: true,
    status: 204,
    json: async () => ({}),
  }));
  vi.stubGlobal("fetch", fetch);

  render(
    <OwnerSessionProvider loadSession={false}>
      <ResetPasswordSurface {...surfaceProps()} />
    </OwnerSessionProvider>,
  );

  expect(window.location.hash).toBe("");
  fireEvent.change(screen.getByLabelText("New password"), {
    target: { value: "a new sufficiently private password" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Change password" }));

  await waitFor(() => expect(fetch).toHaveBeenCalledOnce());
  const [, init] = fetch.mock.calls[0];
  expect(JSON.parse(String(init?.body))).toEqual({
    token: "one-time-token",
    new_password: "a new sufficiently private password",
  });
});


it("retains a verification token captured before RouteDeck replaces browser history", async () => {
  clearCapturedTokenFragment("verification");
  window.history.replaceState({}, "", "/verify#token=verification-token");
  captureAuthTokenFragment(window);
  expect(window.location.hash).toBe("");
  window.history.replaceState({}, "", "/verify");
  const fetch = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit) => ({
    ok: true,
    status: 204,
    json: async () => ({}),
  }));
  vi.stubGlobal("fetch", fetch);

  render(
    <OwnerSessionProvider loadSession={false}>
      <VerifyEmailSurface {...surfaceProps()} />
    </OwnerSessionProvider>,
  );

  const verify = screen.getByRole("button", { name: "Verify email" });
  expect(verify).toBeEnabled();
  fireEvent.click(verify);
  await waitFor(() => expect(fetch).toHaveBeenCalledOnce());
  const [, init] = fetch.mock.calls[0];
  expect(JSON.parse(String(init?.body))).toEqual({ token: "verification-token" });
});


it("locks the chat composer on credential-entry surfaces", () => {
  render(
    <Composer
      disabled
      showCancel={false}
      disabledReason="Chat is disabled while entering account credentials."
      onSend={vi.fn(async () => undefined)}
      onCancel={vi.fn()}
    />,
  );

  expect(screen.getByLabelText("Message the assistant")).toBeDisabled();
  expect(screen.getByText("Chat is disabled while entering account credentials.")).toBeVisible();
  expect(screen.queryByRole("button", { name: "Stop response" })).not.toBeInTheDocument();
});


function surfaceProps(): RouteDeckSurfaceComponentProps {
  return {
    surface: { surface_id: "lounge.reset_password", component: "lounge.reset_password", props: [] },
    slot: "active",
    props: {},
    spec: {
      id: "lounge.reset_password",
      component: "lounge.reset_password",
      lifecycle: "stable",
      public_props_schema: {},
      affordances: [{ id: "return_to_lounge", event: "open", operation: { id: "lounge.return_to_lounge" } }],
    },
    dispatchAffordance: vi.fn(async () => ({}) as never),
  };
}
