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
import {
  frameworkContractFixture,
  frameworkProjectionFixture,
  renderRouteDeckComponent,
} from "./routeDeckHarness";


it("captures a reset token in memory and immediately removes the URL fragment", async () => {
  clearCapturedTokenFragment("password_reset");
  window.history.replaceState({}, "", "/reset-password#token=one-time-token");
  const dispatchAffordance = vi.fn(async () => ({}) as never);
  const rendered = await renderRouteDeckComponent(
    <OwnerSessionProvider loadSession={false}>
      <ResetPasswordSurface {...surfaceProps("lounge.reset_password", dispatchAffordance)} />
    </OwnerSessionProvider>,
    { contract: frameworkContractFixture(), projection: frameworkProjectionFixture() },
  );

  expect(window.location.hash).toBe("");
  fireEvent.change(await screen.findByLabelText("New password"), {
    target: { value: "a new sufficiently private password" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Change password" }));

  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledWith("change_owner_password", {}));
  expect(rendered.client.privateFormSaves.at(-1)).toMatchObject({
    formId: "lounge-password-reset-confirm",
    request: { value: {
      token: "one-time-token",
      new_password: "a new sufficiently private password",
    } },
  });
  rendered.dispose();
});


it("retains a verification token captured before RouteDeck replaces browser history", async () => {
  clearCapturedTokenFragment("verification");
  window.history.replaceState({}, "", "/verify#token=verification-token");
  captureAuthTokenFragment(window);
  expect(window.location.hash).toBe("");
  window.history.replaceState({}, "", "/verify");
  const fetch = vi.fn(async () => ({
    ok: false,
    status: 401,
    json: async () => ({ code: "authentication_required", message: "Authentication is required." }),
  }));
  vi.stubGlobal("fetch", fetch);
  const dispatchAffordance = vi.fn(async () => ({}) as never);

  const rendered = await renderRouteDeckComponent(
    <OwnerSessionProvider loadSession={false}>
      <VerifyEmailSurface {...surfaceProps("lounge.verify_email", dispatchAffordance)} />
    </OwnerSessionProvider>,
    { contract: frameworkContractFixture(), projection: frameworkProjectionFixture() },
  );

  const verify = await screen.findByRole("button", { name: "Verify email" });
  expect(verify).toBeEnabled();
  fireEvent.click(verify);
  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledWith("confirm_owner_email", {}));
  expect(rendered.client.privateFormSaves.at(-1)).toMatchObject({
    formId: "lounge-email-verification",
    request: { value: { token: "verification-token" } },
  });
  rendered.dispose();
});


it("locks the chat composer on credential-entry surfaces", () => {
  render(
    <Composer
      disabled
      showCancel={false}
      disabledReason="Chat is disabled while entering private account information."
      onSend={vi.fn(async () => undefined)}
      onCancel={vi.fn()}
    />,
  );

  expect(screen.getByLabelText("Message the assistant")).toBeDisabled();
  expect(screen.getByText("Chat is disabled while entering private account information.")).toBeVisible();
  expect(screen.queryByRole("button", { name: "Stop response" })).not.toBeInTheDocument();
});


function surfaceProps(
  surfaceId: string,
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"],
): RouteDeckSurfaceComponentProps {
  const formHandle = surfaceId === "lounge.reset_password"
    ? "lounge-password-reset-confirm"
    : "lounge-email-verification";
  return {
    surface: { surface_id: surfaceId, component: surfaceId, props: [] },
    slot: "active",
    props: { form_handle: formHandle },
    spec: {
      id: surfaceId,
      component: surfaceId,
      lifecycle: "stable",
      public_props_schema: {},
      affordances: [],
    },
    dispatchAffordance,
  };
}
