import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { RouteDeckDispatchResult } from "@routedeck/core";
import type { RouteDeckSurfaceComponentProps } from "@routedeck/react";
import { expect, it, vi } from "vitest";

import { LoungeSurface } from "../features/workspace/LoungeSurface";
import { RegisterSurface } from "../features/workspace/RegisterSurface";
import { SignInSurface } from "../features/workspace/SignInSurface";
import { OwnerSessionProvider } from "../features/workspace/OwnerSessionContext";
import { corpusSurfaceRegistry } from "../routedeck/surfaces";


function surfaceProps(
  id: string,
  affordances: Array<{ id: string; operationId: string }>,
  dispatchAffordance: RouteDeckSurfaceComponentProps["dispatchAffordance"] = vi.fn(
    async () => dispatchResult(),
  ),
): RouteDeckSurfaceComponentProps {
  return {
    surface: { surface_id: id, component: id, props: [] },
    slot: "active",
    props: {},
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


it("registers all owner authentication Workspace surfaces", () => {
  expect(Object.keys(corpusSurfaceRegistry).sort()).toEqual([
    "sources.debug",
    "workspace.forgot_password",
    "workspace.home",
    "workspace.lounge",
    "workspace.register",
    "workspace.reset_password",
    "workspace.sign_in",
    "workspace.verify_email",
  ]);
});


it("dispatches Lounge actions through declared RouteDeck affordances", () => {
  const dispatchAffordance = vi.fn(async () => dispatchResult());
  render(
    <LoungeSurface
      {...surfaceProps(
        "workspace.lounge",
        [
          { id: "open_sign_in", operationId: "workspace.open_sign_in" },
          {
            id: "open_registration",
            operationId: "workspace.open_registration",
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


it("signs in and continues through the declared RouteDeck affordance", async () => {
  const dispatchAffordance = vi.fn(async () => dispatchResult());
  vi.stubGlobal("fetch", vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => ownerSession(),
  })));
  render(
    <OwnerSessionProvider loadSession={false}>
      <SignInSurface
        {...surfaceProps(
          "workspace.sign_in",
          [
            { id: "return_to_lounge", operationId: "workspace.return_to_lounge" },
            { id: "open_forgot_password", operationId: "workspace.open_forgot_password" },
            { id: "authentication_completed", operationId: "workspace.authentication_completed" },
          ],
          dispatchAffordance,
        )}
      />
    </OwnerSessionProvider>,
  );

  fireEvent.change(screen.getByLabelText("Email"), {
    target: { value: "owner@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "a sufficiently private password" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

  await waitFor(() => expect(dispatchAffordance).toHaveBeenCalledWith("authentication_completed", {}));
});


it("keeps authentication valid when Workspace continuation fails and offers retry", async () => {
  const dispatchAffordance = vi.fn(async (id: string) => {
    if (id === "authentication_completed") throw new Error("RouteDeck unavailable");
    return dispatchResult();
  });
  vi.stubGlobal("fetch", vi.fn(async () => ({
    ok: true,
    status: 200,
    json: async () => ownerSession(),
  })));
  render(
    <OwnerSessionProvider loadSession={false}>
      <SignInSurface
        {...surfaceProps(
          "workspace.sign_in",
          [
            { id: "return_to_lounge", operationId: "workspace.return_to_lounge" },
            { id: "open_forgot_password", operationId: "workspace.open_forgot_password" },
            { id: "authentication_completed", operationId: "workspace.authentication_completed" },
          ],
          dispatchAffordance,
        )}
      />
    </OwnerSessionProvider>,
  );
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: "owner@example.com" } });
  fireEvent.change(screen.getByLabelText("Password"), { target: { value: "a sufficiently private password" } });
  fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

  expect(await screen.findByRole("alert")).toHaveTextContent(
    "Signed in. Workspace continuation failed",
  );
  expect(screen.queryByLabelText("Email")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Continue to Workspace" })).toBeEnabled();
});


it("recovers an authenticated session with one explicit continuation and no credential replay", async () => {
  const dispatchAffordance = vi.fn(async () => dispatchResult());
  const fetch = vi.fn();
  vi.stubGlobal("fetch", fetch);
  render(
    <OwnerSessionProvider initialSession={ownerSession()} loadSession={false}>
      <SignInSurface
        {...surfaceProps(
          "workspace.sign_in",
          [
            { id: "return_to_lounge", operationId: "workspace.return_to_lounge" },
            { id: "open_forgot_password", operationId: "workspace.open_forgot_password" },
            { id: "authentication_completed", operationId: "workspace.authentication_completed" },
          ],
          dispatchAffordance,
        )}
      />
    </OwnerSessionProvider>,
  );

  expect(screen.queryByLabelText("Email")).not.toBeInTheDocument();
  expect(screen.queryByLabelText("Password")).not.toBeInTheDocument();
  expect(dispatchAffordance).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Continue to Workspace" }));

  await waitFor(() =>
    expect(dispatchAffordance).toHaveBeenCalledWith("authentication_completed", {}),
  );
  expect(fetch).not.toHaveBeenCalled();
});


it("validates registration password policy and keeps a typed return action", () => {
  const dispatchAffordance = vi.fn(async () => dispatchResult());
  render(
    <OwnerSessionProvider loadSession={false}>
      <RegisterSurface
        {...surfaceProps(
          "workspace.register",
          [
            { id: "return_to_lounge", operationId: "workspace.return_to_lounge" },
            { id: "authentication_completed", operationId: "workspace.authentication_completed" },
          ],
          dispatchAffordance,
        )}
      />
    </OwnerSessionProvider>,
  );

  fireEvent.change(screen.getByLabelText("Email"), {
    target: { value: "owner@example.com" },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: "owner@example.com-safe" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create account" }));
  expect(screen.getByRole("alert")).toHaveTextContent("email address");
  fireEvent.click(screen.getByRole("button", { name: "Back to Lounge" }));
  expect(dispatchAffordance).toHaveBeenCalledWith("return_to_lounge", {});
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
