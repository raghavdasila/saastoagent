import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import type { RouteDeckDispatchResult } from "@routedeck/core";
import { expect, it, vi } from "vitest";

import { Composer } from "../app/Composer";
import { OwnerSessionProvider } from "../auth/OwnerSessionContext";
import { ResetPasswordSurface } from "../features/lounge/ResetPasswordSurface";
import { ForgotPasswordSurface } from "../features/lounge/ForgotPasswordSurface";
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
  const dispatchAffordance = vi.fn(async () => completedOperation());
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

it("shows known recovery-service unavailability without claiming a reset request", async () => {
  const publicMessage = "Password recovery is temporarily unavailable. Try again later.";
  const dispatchAffordance = vi.fn(async () => failedOperation(
    "lounge.request_password_recovery",
    "mail_service_unavailable",
    publicMessage,
  ));
  const rendered = await renderRouteDeckComponent(
    <ForgotPasswordSurface
      {...surfaceProps("lounge.forgot_password", dispatchAffordance)}
    />,
    { contract: frameworkContractFixture(), projection: frameworkProjectionFixture() },
  );

  fireEvent.change(await screen.findByLabelText("Email"), {
    target: { value: "owner@example.com" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Request reset" }));

  expect(await screen.findByRole("alert")).toHaveTextContent(publicMessage);
  expect(screen.queryByText(/password-reset email has been requested/i)).not.toBeInTheDocument();
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
    : surfaceId === "lounge.forgot_password"
      ? "lounge-password-reset-request"
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

function completedOperation(): RouteDeckDispatchResult {
  return {
    disposition: "completed",
    request_id: "request-1",
    operation_id: "lounge.account_operation",
    session_version: 2,
    projection_version: 2,
    evidence: {
      source: "surface",
      phases: [],
      attempt_id: "attempt-1",
      request_fingerprint: "fingerprint",
      delivery_phase: "response_received",
    },
    outcome: "completed",
    review: null,
    failure: null,
  };
}

function failedOperation(
  operationId: string,
  code: string,
  publicMessage: string,
): RouteDeckDispatchResult {
  return {
    disposition: "failed",
    request_id: "request-failed",
    operation_id: operationId,
    session_version: 2,
    projection_version: 2,
    evidence: {
      source: "surface",
      phases: ["received", "tool_failed"],
      attempt_id: "attempt-failed",
      request_fingerprint: "fingerprint-failed",
      delivery_phase: "not_sent",
    },
    outcome: null,
    review: null,
    failure: {
      kind: "business",
      code,
      phase: "tool_failed",
      correlation_id: "correlation-failed",
      operation_id: operationId,
      request_id: "request-failed",
      public_message: publicMessage,
      recovery_directive: null,
      safe_details: {},
    },
  };
}
