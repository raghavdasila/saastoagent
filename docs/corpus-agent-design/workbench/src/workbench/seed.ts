import type { WorkbenchState } from "@/workbench/types"

export function createSeedState(): WorkbenchState {
  return {
    version: 6,
    features: [
      {
        id: "workspace",
        name: "Workspace",
        stories: [
          {
            id: "enter-workspace",
            title: "Enter the workspace",
            userIntent: "Return to my private Workspace and understand its current state.",
            agentIntent: "Establish the authenticated owner's Workspace as the active context and provide a truthful orientation with valid next choices.",
            story: "An authenticated owner enters Corpus after creating an account, signing in, or returning in an existing session. Corpus opens that owner's one private Workspace, identifies it as the active context, and truthfully summarizes its agents, sources, and related activity. Empty sections remain visibly empty. Corpus does not automatically create or open an agent; entry is complete when the owner can see where they are and choose a next action.",
            messages: [
              {
                id: "workspace-message-1",
                actor: "Corpus",
                content: "You're in your Workspace. It currently has no agents or sources.",
              },
              {
                id: "workspace-message-2",
                actor: "Owner",
                content: "I want to create my first agent.",
              },
            ],
            actions: [{ id: "create-agent", label: "Create an agent" }],
            mockSurfacePath: null,
            status: "draft",
            rejectionReason: "",
          },
          {
            id: "owner-auth-register",
            title: "Create an owner account",
            userIntent: "Keep the Workspace I started as a guest by creating an owner account.",
            agentIntent: "Create the owner identity, preserve the guest Workspace by adopting the session, and continue the authenticated owner without overstating continuation success.",
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
            actions: [],
            mockSurfacePath: "/mock-surfaces/workspace/authentication.html#register",
            status: "approved",
            rejectionReason: "",
          },
          {
            id: "owner-auth-sign-in",
            title: "Sign in and resume a Workspace",
            userIntent: "Return to the private Workspace associated with my existing account.",
            agentIntent: "Authenticate the owner and resume only the Workspace claimed by that account, or report invalid credentials clearly.",
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
            actions: [],
            mockSurfacePath: "/mock-surfaces/workspace/authentication.html#sign-in",
            status: "approved",
            rejectionReason: "",
          },
          {
            id: "owner-auth-sign-out",
            title: "Sign out to a fresh Lounge",
            userIntent: "End access to my Workspace on this browser while keeping the Workspace private.",
            agentIntent: "Revoke the current browser's owner access and return to a fresh guest Lounge without changing Workspace ownership.",
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
            actions: [],
            mockSurfacePath: "/mock-surfaces/workspace/authentication.html#sign-out",
            status: "approved",
            rejectionReason: "",
          },
          {
            id: "owner-auth-request-reset",
            title: "Request a password reset",
            userIntent: "Regain access to my account because I cannot use my current password.",
            agentIntent: "Accept the reset request without revealing account existence, request delivery when an account exists, and report delivery unavailability truthfully.",
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
            actions: [],
            mockSurfacePath: "/mock-surfaces/workspace/authentication.html#request-reset",
            status: "approved",
            rejectionReason: "",
          },
          {
            id: "owner-auth-confirm-reset",
            title: "Set a new password",
            userIntent: "Replace my password using the one-time reset link and return to sign-in.",
            agentIntent: "Validate the reset link, change the password, revoke existing access, and return the owner to sign-in or an explicit token failure.",
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
            actions: [],
            mockSurfacePath: "/mock-surfaces/workspace/authentication.html#reset-password",
            status: "approved",
            rejectionReason: "",
          },
          {
            id: "owner-auth-request-verification",
            title: "Resend email verification",
            userIntent: "Receive a fresh verification email for my signed-in owner account.",
            agentIntent: "Request a new verification message and state whether delivery succeeded or is unavailable without blocking Workspace use.",
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
            actions: [],
            mockSurfacePath: "/mock-surfaces/workspace/authentication.html#verification-pending",
            status: "approved",
            rejectionReason: "",
          },
          {
            id: "owner-auth-confirm-verification",
            title: "Confirm the owner email",
            userIntent: "Confirm that this email address belongs to my owner account.",
            agentIntent: "Use the one-time link to verify the address, refresh owner state, and produce a visible confirmation or explicit token failure.",
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
            actions: [],
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
            userIntent: "Turn a plain-language job description into a new agent draft.",
            agentIntent: "Determine a proposed name and responsibility from the description, producing a clearly labeled draft without implying deployment.",
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
            actions: [],
            mockSurfacePath: "/mock-surfaces/agents/create-agent.html",
            status: "draft",
            rejectionReason: "",
          },
        ],
      },
    ],
  }
}
