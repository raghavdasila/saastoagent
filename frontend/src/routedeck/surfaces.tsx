import { defineRouteDeckSurfaceRegistry } from "@routedeck/react";

import { LoungeSurface } from "../features/lounge/LoungeSurface";
import { RegisterSurface } from "../features/lounge/RegisterSurface";
import { SignInSurface } from "../features/lounge/SignInSurface";
import { ForgotPasswordSurface } from "../features/lounge/ForgotPasswordSurface";
import { ResetPasswordSurface } from "../features/lounge/ResetPasswordSurface";
import { VerifyEmailSurface } from "../features/lounge/VerifyEmailSurface";
import { HomeSurface } from "../features/workspace/HomeSurface";
import { AgentsHomeSurface } from "../features/agents/AgentsHomeSurface";
import { CreateAgentSurface } from "../features/agents/CreateAgentSurface";
import type { AgentStore } from "../features/agents/store";
import type { WorkspaceStore } from "../features/workspace/store";
import { SourceDebugSurface } from "../features/sources/SourceDebugSurface";
import type { SourceClient } from "../features/sources/sourceClient";

export function createCorpusSurfaceRegistry(
  sourceClient: SourceClient,
  agentStore: AgentStore,
  workspaceStore: WorkspaceStore,
) {
  return defineRouteDeckSurfaceRegistry({
    "lounge.home": LoungeSurface,
    "lounge.sign_in": SignInSurface,
    "lounge.register": RegisterSurface,
    "lounge.forgot_password": ForgotPasswordSurface,
    "lounge.reset_password": ResetPasswordSurface,
    "lounge.verify_email": VerifyEmailSurface,
    "workspace.home": (props) => (
      <HomeSurface {...props} workspaceStore={workspaceStore} />
    ),
    "agents.home": (props) => (
      <AgentsHomeSurface {...props} store={agentStore} />
    ),
    "agents.create": (props) => (
      <CreateAgentSurface {...props} store={agentStore} />
    ),
    "sources.debug": (props) => <SourceDebugSurface {...props} sourceClient={sourceClient} />,
  });
}
