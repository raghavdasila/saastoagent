import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { RouteDeckDispatchResult } from "@routedeck/core";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { expect, it, vi } from "vitest";

import { LoungeSurface } from "../features/lounge/LoungeSurface";
import { RegisterSurface } from "../features/lounge/RegisterSurface";
import { SignInSurface } from "../features/lounge/SignInSurface";
import { OwnerSessionProvider } from "../features/lounge/OwnerSessionContext";
import { configureOwnerAuthClient } from "../features/lounge/authClient";
import { SourceClient } from "../features/sources/sourceClient";
import { createCorpusSurfaceRegistry } from "../routedeck/surfaces";
import {
  frameworkContractFixture,
  frameworkProjectionFixture,
  renderRouteDeckComponent,
} from "./routeDeckHarness";


function surfaceProps(
  id: string,
  affordances: Array<{ id: string; operationId: string }>,
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"] = vi.fn(
    async () => dispatchResult(),
  ),
): RouteDeckSurfaceComponentProps {
  const formHandle = FORM_HANDLES[id];
  return {
    surface: { surface_id: id, component: id, props: [] },
    slot: "active",
    props: formHandle === undefined ? {} : { form_handle: formHandle },
    spec: {
      id,
      component: id,
      lifecycle: "stable",
      public_props_schema: {},
      affordances: affordances.map((affordance) => ({
        id: affordance.id,
        event: "open",
        operation: { id: affordance.operationId },
      })),
    },
    dispatchAffordance,
  };
}

const FORM_HANDLES: Readonly<Record<string, string>> = Object.freeze({
  "lounge.register": "lounge-register",
  "lounge.sign_in": "lounge-sign-in",
  "lounge.forgot_password": "lounge-password-reset-request",
  "lounge.reset_password": "lounge-password-reset-confirm",
  "lounge.verify_email": "lounge-email-verification",
});


it("registers Lounge, Workspace, and Sources surfaces", () => {
  expect(Object.keys(surfaceRegistry()).sort()).toEqual([
    "lounge.forgot_password",
    "lounge.home",
    "lounge.register",
    "lounge.reset_password",
    "lounge.sign_in",
    "lounge.verify_email",
    "sources.debug",
    "workspace.home",
  ]);
});

function surfaceRegistry() {
  return createCorpusSurfaceRegistry(
    new SourceClient({ fetch: async () => new Response("{}") }),
  );
}


it("dispatches Lounge actions through declared RouteDeck affordances", () => {
  const dispatchAffordance = vi.fn(async () => dispatchResult());
  render(
    <LoungeSurface
      {...surfaceProps(
        "lounge.home",
        [
          { id: "open_sign_in", operationId: "lounge.open_sign_in" },
          {
            id: "open_registration",
            operationId: "lounge.open_registration",
          },
        ],
        dispatchAffordance,
      )}
    />,
  );

  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
  fireEvent.click(screen.getByRole("button", { name: "Create account" }));

  expect(dispatchAffordance).toHaveBeenNthCalledWith(1, "open_sign_in", {});
  expect(dispatchAffordance).toHaveBeenNthCalledWith(2, "open_registration", {});
});


it("saves sign-in privately and dispatches the declared RouteDeck operation", async () => {
  const dispatchAffordance = vi.fn(async () => dispatchResult());
  const fetcher = vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => ownerSession(),
  })) as unknown as typeof fetch;
  vi.stubGlobal("fetch", fetcher);
  configureOwnerAuthClient({
    transport: { fetch: fetcher },
    signOut: async () => undefined,
  });
  const rendered = await renderRouteDeckComponent(
    <OwnerSessionProvider loadSession={false}>
      <SignInSurface
        {...surfaceProps(
          "lounge.sign_in",
          [
            { id: "return_to_lounge", operationId: "lounge.sign_in.return_to_lounge" },
            { id: "open_password_recovery", operationId: "lounge.sign_in.open_password_recovery" },
            { id: "authenticate_owner", operationId: "lounge.authenticate_owner_account" },
            { id: "continue_to_workspace", operationId: "lounge.sign_in.continue_to_workspace" },
          ],
          dispatchAffordance,
        )}
      />
    </OwnerSessionProvider>,
    {
      contract: frameworkContractFixture(),
      projection: frameworkProjectionFixture(),
    },
  );

  fireEvent.change(await screen.findByLabelText("Email"), {
    target: { value: "owner@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "a sufficiently private password" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledWith("authenticate_owner", {}));
  expect(rendered.client.privateFormSaves.at(-1)).toMatchObject({
    formId: "lounge-sign-in",
    request: {
      value: {
        email: "owner@example.com",
        password: "a sufficiently private password",
      },
      complete: true,
    },
  });
  rendered.dispose();
});


it("keeps authentication valid when Workspace continuation fails and offers retry", async () => {
  const dispatchAffordance = vi.fn(async (id: string) => {
    if (id === "authenticate_owner") throw new Error("RouteDeck unavailable");
    return dispatchResult();
  });
  const fetcher = vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => ownerSession(),
  })) as unknown as typeof fetch;
  vi.stubGlobal("fetch", fetcher);
  configureOwnerAuthClient({
    transport: { fetch: fetcher },
    signOut: async () => undefined,
  });
  const rendered = await renderRouteDeckComponent(
    <OwnerSessionProvider loadSession={false}>
      <SignInSurface
        {...surfaceProps(
          "lounge.sign_in",
          [
            { id: "return_to_lounge", operationId: "lounge.sign_in.return_to_lounge" },
            { id: "open_password_recovery", operationId: "lounge.sign_in.open_password_recovery" },
            { id: "authenticate_owner", operationId: "lounge.authenticate_owner_account" },
            { id: "continue_to_workspace", operationId: "lounge.sign_in.continue_to_workspace" },
          ],
          dispatchAffordance,
        )}
      />
    </OwnerSessionProvider>,
    { contract: frameworkContractFixture(), projection: frameworkProjectionFixture() },
  );
  fireEvent.change(await screen.findByLabelText("Email"), { target: { value: "owner@example.com" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "a sufficiently private password" } });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Authenticated. Workspace continuation failed",
  );
  expect(screen.queryByLabelText("Email")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Continue to Workspace" })).toBeEnabled();
  rendered.dispose();
});


it("recovers an authenticated session with one explicit continuation and no credential replay", async () => {
  const dispatchAffordance = vi.fn(async () => dispatchResult());
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  const rendered = await renderRouteDeckComponent(
    <OwnerSessionProvider initialSession={ownerSession()} loadSession={false}>
      <SignInSurface
        {...surfaceProps(
          "lounge.sign_in",
          [
            { id: "return_to_lounge", operationId: "lounge.sign_in.return_to_lounge" },
            { id: "open_password_recovery", operationId: "lounge.sign_in.open_password_recovery" },
            { id: "authenticate_owner", operationId: "lounge.authenticate_owner_account" },
            { id: "continue_to_workspace", operationId: "lounge.sign_in.continue_to_workspace" },
          ],
          dispatchAffordance,
        )}
      />
    </OwnerSessionProvider>,
    { contract: frameworkContractFixture(), projection: frameworkProjectionFixture() },
  );

  expect(screen.queryByLabelText("Email")).not.toBeInTheDocument();
  expect(screen.queryByLabelText("Password")).not.toBeInTheDocument();
  expect(dispatchAffordance).not.toHaveBeenCalled();
  fireEvent.click(await screen.findByRole("button", { name: "Continue to Workspace" }));

  await waitFor(() =>
    expect(dispatchAffordance).toHaveBeenCalledWith("continue_to_workspace", {}),
  );
  expect(fetch).not.toHaveBeenCalled();
  rendered.dispose();
});


it("validates registration password policy and keeps a typed return action", async () => {
  const dispatchAffordance = vi.fn(async () => dispatchResult());
  const rendered = await renderRouteDeckComponent(
    <OwnerSessionProvider loadSession={false}>
      <RegisterSurface
        {...surfaceProps(
          "lounge.register",
          [
            { id: "return_to_lounge", operationId: "lounge.registration.return_to_lounge" },
            { id: "create_owner_account", operationId: "lounge.create_owner_account" },
            { id: "continue_to_workspace", operationId: "lounge.registration.continue_to_workspace" },
          ],
          dispatchAffordance,
        )}
      />
    </OwnerSessionProvider>,
    { contract: frameworkContractFixture(), projection: frameworkProjectionFixture() },
  );

  fireEvent.change(await screen.findByLabelText("Email"), {
    target: { value: "owner@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "owner@example.com-safe" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create account" }));
  expect(screen.getByRole("alert")).toHaveTextContent("email address");
  fireEvent.click(screen.getByRole("button", { name: "Back to Lounge" }));
  expect(dispatchAffordance).toHaveBeenCalledWith("return_to_lounge", {});
  rendered.dispose();
});

function ownerSession() {
  return {
    owner: { email: "owner@example.com", display_name: "Owner", is_verified: false },
    organization: { name: "Owner's Workspace", slug: "owner-workspace" },
    membership: { role: "owner" as const },
    route_session_state: "resumed" as const,
  };
}


function dispatchResult(): RouteDeckDispatchResult {
  return {
    disposition: "completed" as const,
    operation_id: "workspace.navigation",
    request_id: "workspace-surface-test",
    session_version: 2,
    projection_version: 2,
    evidence: {
      source: "surface" as const,
      phases: ["received", "completed"],
      attempt_id: "attempt-workspace",
      request_fingerprint: "fingerprint-workspace",
      delivery_phase: "response_received" as const,
      result_id: "result-workspace",
      result_fingerprint: "result-fingerprint-workspace",
    },
    review: null,
    outcome: "opened",
    failure: null,
  };
}
