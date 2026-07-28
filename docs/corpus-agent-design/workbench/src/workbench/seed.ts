import type { WorkbenchState } from "@/workbench/types"

export function createSeedState(): WorkbenchState {
  return {
    version: 3,
    features: [
      {
        id: "workspace",
        name: "Workspace",
        stories: [
          {
            id: "enter-workspace",
            title: "Enter the workspace",
            story: "As an owner opening Corpus, I want one clear entry point into my workspace, so I can start creating an agent without understanding the whole system.",
            messages: [
              {
                id: "workspace-message-1",
                actor: "Corpus",
                content: "This is your workspace. We can create an agent together, then test how it should behave.",
              },
              {
                id: "workspace-message-2",
                actor: "Owner",
                content: "Let’s create an agent for the support workflow.",
              },
            ],
            mockSurfacePath: "/mock-surfaces/workspace/enter-workspace.html",
            status: "draft",
            rejectionReason: "",
          },
          {
            id: "owner-auth-register",
            title: "Create an owner account",
            story: "An owner exploring Corpus as a guest wants to keep the Workspace they have started. They can create an account with an optional display name, email, and a 12-128 character password. Corpus creates their personal Workspace, adopts the current guest session, signs them in, and continues to Home. If authentication succeeds but Workspace continuation fails, the signed-in state remains valid and Corpus offers an explicit retry.",
            messages: [
              {
                id: "owner-auth-register-message-1",
                actor: "Corpus",
                content: "You can keep exploring as a guest, or create an owner account to keep this Workspace.",
              },
              {
                id: "owner-auth-register-message-2",
                actor: "Owner",
                content: "I want to keep this Workspace and return to it later.",
              },
            ],
            mockSurfacePath: "/mock-surfaces/workspace/authentication.html#register",
            status: "approved",
            rejectionReason: "",
          },
          {
            id: "owner-auth-sign-in",
            title: "Sign in and resume a Workspace",
            story: "An existing owner arrives at the guest Lounge and wants to return to their private Workspace. They can sign in with email and password. Corpus resumes only the Workspace claimed by that owner through the current browser session and opaque owner route handle; invalid credentials remain a visible failure.",
            messages: [
              {
                id: "owner-auth-sign-in-message-1",
                actor: "Owner",
                content: "I already have a Corpus account.",
              },
              {
                id: "owner-auth-sign-in-message-2",
                actor: "Corpus",
                content: "Sign in to resume the Workspace already claimed by that account.",
              },
            ],
            mockSurfacePath: "/mock-surfaces/workspace/authentication.html#sign-in",
            status: "approved",
            rejectionReason: "",
          },
          {
            id: "owner-auth-sign-out",
            title: "Sign out to a fresh Lounge",
            story: "An authenticated owner wants to end access on the current browser. They can sign out from the Corpus header or Workspace Home. Corpus revokes the browser auth session and owner route handle, clears the browser credentials, and returns to a fresh anonymous Lounge without making the claimed Workspace anonymous.",
            messages: [
              {
                id: "owner-auth-sign-out-message-1",
                actor: "Owner",
                content: "Sign me out on this browser.",
              },
              {
                id: "owner-auth-sign-out-message-2",
                actor: "Corpus",
                content: "I will end this browser session and return you to a fresh guest Lounge. Your Workspace remains private.",
              },
            ],
            mockSurfacePath: "/mock-surfaces/workspace/authentication.html#sign-out",
            status: "approved",
            rejectionReason: "",
          },
          {
            id: "owner-auth-request-reset",
            title: "Request a password reset",
            story: "An owner who cannot sign in submits their email address. Corpus always shows the same generic confirmation so the surface does not reveal whether an account exists. When the account exists, Corpus requests a one-hour reset link; delivery failure does not masquerade as successful delivery.",
            messages: [
              {
                id: "owner-auth-request-reset-message-1",
                actor: "Owner",
                content: "I cannot sign in.",
              },
              {
                id: "owner-auth-request-reset-message-2",
                actor: "Corpus",
                content: "Request a reset with your email. I will show the same confirmation whether or not an account exists.",
              },
            ],
            mockSurfacePath: "/mock-surfaces/workspace/authentication.html#request-reset",
            status: "approved",
            rejectionReason: "",
          },
          {
            id: "owner-auth-confirm-reset",
            title: "Set a new password",
            story: "An owner opens a one-time password-reset link and chooses a new 12-128 character password. Corpus captures the token in memory, removes it from the visible URL, changes the password, revokes every existing auth session and owner route handle for that owner, and returns them to sign in. A missing, invalid, or expired token remains an explicit failure.",
            messages: [
              {
                id: "owner-auth-confirm-reset-message-1",
                actor: "Corpus",
                content: "This one-time link can change your password. Completing it signs out every existing browser session.",
              },
              {
                id: "owner-auth-confirm-reset-message-2",
                actor: "Owner",
                content: "Change it and return me to sign in.",
              },
            ],
            mockSurfacePath: "/mock-surfaces/workspace/authentication.html#reset-password",
            status: "approved",
            rejectionReason: "",
          },
          {
            id: "owner-auth-request-verification",
            title: "Resend email verification",
            story: "A signed-in owner can use their Workspace while email verification is still pending. Workspace Home shows the advisory state and lets the owner request another verification email. Corpus shows success only when delivery succeeds and visibly reports delivery unavailability.",
            messages: [
              {
                id: "owner-auth-request-verification-message-1",
                actor: "Corpus",
                content: "Your Workspace is available. Email verification is still pending.",
              },
              {
                id: "owner-auth-request-verification-message-2",
                actor: "Owner",
                content: "Send the verification email again.",
              },
            ],
            mockSurfacePath: "/mock-surfaces/workspace/authentication.html#verification-pending",
            status: "approved",
            rejectionReason: "",
          },
          {
            id: "owner-auth-confirm-verification",
            title: "Confirm the owner email",
            story: "An owner opens a one-time verification link. Corpus captures the token before navigation can replace it, removes the token from the visible URL, verifies the address, refreshes the owner state, and shows a visible confirmation. Missing, invalid, or expired verification tokens remain explicit failures.",
            messages: [
              {
                id: "owner-auth-confirm-verification-message-1",
                actor: "Owner",
                content: "Verify this email address.",
              },
              {
                id: "owner-auth-confirm-verification-message-2",
                actor: "Corpus",
                content: "I will use the one-time link and keep its token out of the visible URL.",
              },
            ],
            mockSurfacePath: "/mock-surfaces/workspace/authentication.html#verify-email",
            status: "approved",
            rejectionReason: "",
          },
        ],
      },
      {
        id: "agents",
        name: "Agents",
        stories: [
          {
            id: "create-draft-agent",
            title: "Create a draft agent",
            story: "As an owner, I want to describe an agent’s job in plain language and confirm the proposed behavior, so I get a named draft without implying it is deployed.",
            messages: [
              {
                id: "agents-message-1",
                actor: "Corpus",
                content: "What job should this agent own? A short description is enough to start.",
              },
              {
                id: "agents-message-2",
                actor: "Owner",
                content: "Help support leads turn repeated customer questions into reviewed help articles.",
              },
              {
                id: "agents-message-3",
                actor: "Corpus",
                content: "I’ll create a draft called Support Knowledge Agent. It will propose articles, but a lead must approve them before publishing.",
              },
            ],
            mockSurfacePath: "/mock-surfaces/agents/create-agent.html",
            status: "draft",
            rejectionReason: "",
          },
        ],
      },
    ],
  }
}
