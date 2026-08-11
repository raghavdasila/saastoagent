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
import { AgentLifecycleReviewSurface } from "../features/agents/AgentLifecycleReviewSurface";
import type { AgentStore } from "../features/agents/store";
import type { WorkspaceStore } from "../features/workspace/store";
import { SourceHubSurface } from "../features/sources/SourceHubSurface";
import type { SourceClient } from "../features/sources/sourceClient";
import { ContractRevisionStore } from "../features/sources/contractRevisionStore";
import { ApiContractRevisionPanel } from "../features/sources/ApiContractRevisionPanel";
import { ApiContractRevisionReviewSurface } from "../features/sources/ApiContractRevisionReviewSurface";
import { ApiOperationTestPanel } from "../features/sources/ApiOperationTestPanel";
import { RoutedApiWriteReviewSurface } from "../features/sources/RoutedApiWriteReviewSurface";
import { RoutedExecutionStore } from "../features/sources/routedExecutionStore";
import { SourceLifecycleStore } from "../features/sources/sourceLifecycleStore";
import { SourceDeleteReviewSurface } from "../features/sources/SourceDeleteReviewSurface";
import { PrivateFormGate, requireFormHandle } from "./PrivateFormGate";
import { DesignerSurface } from "../features/designer/DesignerSurface";
import { DesignerReviewSurface } from "../features/designer/DesignerReviewSurface";
import type { DesignerClient } from "../features/designer/client";
import { DesignerRefreshStore } from "../features/designer/refreshStore";
import { BuilderSurface } from "../features/builder/BuilderSurface";
import { BuilderDeleteReviewSurface } from "../features/builder/BuilderDeleteReviewSurface";
import { SandboxSurface } from "../features/builder/SandboxSurface";
import type { AgentRuntimeClient } from "../features/builder/client";
import { EvaluationSurface } from "../features/evaluation/EvaluationSurface";
import { EvaluationDeleteReviewSurface } from "../features/evaluation/EvaluationDeleteReviewSurface";
import { ChannelsSurface } from "../features/delivery/ChannelsSurface";
import { ChannelDraftStore } from "../features/delivery/channelDraftStore";
import { DeploymentReviewSurface } from "../features/delivery/DeploymentReviewSurface";
import { OperationsSurface } from "../features/operations/OperationsSurface";

export function createCorpusSurfaceRegistry(
  sourceClient: SourceClient,
  agentStore: AgentStore,
  workspaceStore: WorkspaceStore,
  designerClient?: DesignerClient,
  agentRuntimeClient?: AgentRuntimeClient,
) {
  const contractRevisionStore = new ContractRevisionStore(sourceClient);
  const routedExecutionStore = new RoutedExecutionStore(sourceClient);
  const sourceLifecycleStore = new SourceLifecycleStore(sourceClient);
  const activeDesignerClient = designerClient ?? {
    get: async () => { throw new Error("Agent Designer client is unavailable."); },
  } as unknown as DesignerClient;
  const designerRefreshStore = new DesignerRefreshStore();
  const channelDraftStore = new ChannelDraftStore();
  const activeAgentRuntimeClient = agentRuntimeClient ?? {
    builds: async () => { throw new Error("Agent Builds client is unavailable."); },
    sandbox: async () => { throw new Error("Agent Sandbox client is unavailable."); },
    evaluations: async () => { throw new Error("Agent Evaluations are unavailable."); },
    channels: async () => { throw new Error("Agent Channels are unavailable."); },
    deployments: async () => { throw new Error("Agent Deployments are unavailable."); },
    operations: async () => { throw new Error("Agent Operations are unavailable."); },
  } as unknown as AgentRuntimeClient;
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
      <AgentsHomeSurface {...props} store={agentStore} sourceClient={sourceClient} />
    ),
    "agents.create": (props) => (
      <CreateAgentSurface {...props} store={agentStore} />
    ),
    "agents.lifecycle_review": (props) => (
      <AgentLifecycleReviewSurface {...props} store={agentStore} />
    ),
    "designer.home": (props) => (
      <DesignerSurface {...props} agentStore={agentStore} client={activeDesignerClient} refreshStore={designerRefreshStore} />
    ),
    "designer.review": (props) => <DesignerReviewSurface {...props} refreshStore={designerRefreshStore} />,
    "builder.home": (props) => (
      <BuilderSurface {...props} agentStore={agentStore} designerClient={activeDesignerClient} runtimeClient={activeAgentRuntimeClient} />
    ),
    "builder.delete_review": BuilderDeleteReviewSurface,
    "sandbox.home": (props) => (
      <SandboxSurface {...props} agentStore={agentStore} runtimeClient={activeAgentRuntimeClient} />
    ),
    "evaluation.home": (props) => (
      <EvaluationSurface {...props} agentStore={agentStore} runtimeClient={activeAgentRuntimeClient} />
    ),
    "evaluation.delete_case_review": EvaluationDeleteReviewSurface,
    "channels.home": (props) => (
      <ChannelsSurface {...props} agentStore={agentStore} runtimeClient={activeAgentRuntimeClient} draftStore={channelDraftStore} />
    ),
    "deployment.deploy_review": (props) => <DeploymentReviewSurface {...props} kind="deploy" />,
    "deployment.retry_review": (props) => <DeploymentReviewSurface {...props} kind="retry" />,
    "deployment.rollback_review": (props) => <DeploymentReviewSurface {...props} kind="rollback" />,
    "channels.availability_review": (props) => <DeploymentReviewSurface {...props} kind="availability" />,
    "operations.home": (props) => (
      <OperationsSurface {...props} runtimeClient={activeAgentRuntimeClient} agentStore={agentStore} />
    ),
    "sources.home": (props) => (
      <SourceHubSurface
        {...props}
        view="hub"
        sourceClient={sourceClient}
        privateForm={null}
        contractRevisionStore={contractRevisionStore}
        lifecycleStore={sourceLifecycleStore}
      />
    ),
    "sources.api_intake": (props) => (
      <SourceHubSurface
        {...props}
        view="api"
        sourceClient={sourceClient}
        privateForm={null}
        contractRevisionStore={contractRevisionStore}
        lifecycleStore={sourceLifecycleStore}
      />
    ),
    "sources.api": (props) => (
      <PrivateFormGate formId={requireFormHandle(props.props)}>
        {(privateForm) => (
          <SourceHubSurface
            {...props}
            view="api"
            sourceClient={sourceClient}
            privateForm={privateForm}
            contractRevisionStore={contractRevisionStore}
            lifecycleStore={sourceLifecycleStore}
          />
        )}
      </PrivateFormGate>
    ),
    "sources.contract_revision_proposal": (props) => (
      <ApiContractRevisionPanel {...props} store={contractRevisionStore} />
    ),
    "sources.contract_revision_review": (props) => (
      <ApiContractRevisionReviewSurface {...props} store={contractRevisionStore} />
    ),
    "sources.api_operation_test": (props) => (
      <ApiOperationTestPanel
        {...props}
        sourceClient={sourceClient}
        executionStore={routedExecutionStore}
      />
    ),
    "sources.routed_api_write_review": (props) => (
      <RoutedApiWriteReviewSurface {...props} store={routedExecutionStore} />
    ),
    "sources.delete_review": (props) => (
      <SourceDeleteReviewSurface {...props} store={sourceLifecycleStore} />
    ),
  });
}
