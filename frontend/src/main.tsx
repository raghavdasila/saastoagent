import React, { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { RouteDeckBootstrapBoundary } from "@routedeck/react";

import { ApplicationShell } from "./app/ApplicationShell";
import { bootstrapCorpusConnection } from "./app/bootstrapConnection";
import type { BootstrappedCorpusConnection } from "./app/bootstrapConnection";
import { BootstrapLoadingShell } from "./app/BootstrapLoadingShell";
import { CorpusRecoveryCoordinator } from "./app/CorpusRecoveryCoordinator";
import { CorpusHeader } from "./app/CorpusHeader";
import { CorpusMainHeading } from "./app/CorpusMainHeading";
import {
  ConversationLifecycle,
  type MountedConversation,
} from "./app/conversationLifecycle";
import { FeatureNavigation } from "./app/FeatureNavigation";
import {
  configureOwnerAuthClient,
} from "./auth/authClient";
import { LOUNGE_SIGN_IN_PATH } from "./features/lounge/routes";
import { SourceClient } from "./features/sources/sourceClient";
import { AgentClient } from "./features/agents/client";
import { AgentStore } from "./features/agents/store";
import { DesignerClient } from "./features/designer/client";
import { AgentRuntimeClient } from "./features/builder/client";
import { PublicAgentApp } from "./features/delivery/PublicAgentApp";
import { WorkspaceClient } from "./features/workspace/client";
import { WorkspaceStore } from "./features/workspace/store";
import {
  captureAuthTokenFragment,
} from "./features/lounge/tokenFragment";
import { createCorpusSurfaceRegistry } from "./routedeck/surfaces";
import "./styles.css";
import "./features/workspace/workspace.css";
import "./features/sources/sources.css";
import "./features/agents/agents.css";
import "./features/designer/designer.css";
import "./features/builder/builder.css";
import "./features/evaluation/evaluation.css";
import "./features/delivery/delivery.css";
import "./features/operations/operations.css";

const rootElement = document.getElementById("root");
if (rootElement === null) {
  throw new Error("Corpus requires a #root element.");
}

const root = createRoot(rootElement);
captureAuthTokenFragment(window);
root.render(<BootstrapLoadingShell />);
void start();

async function start(): Promise<void> {
  const publicMatch = /^\/public\/agents\/([a-z0-9]+(?:-[a-z0-9]+)*)\/?$/.exec(window.location.pathname);
  if (publicMatch !== null) {
    root.render(<PublicAgentApp slug={publicMatch[1]} />);
    return;
  }
  try {
    const bootstrap = await bootstrapCorpusConnection(window);
    const sourceClient = new SourceClient(bootstrap.authorized);
    configureOwnerAuthClient({
      transport: bootstrap.authorized,
      signOut: () => {
        sourceClient.clearConversation();
        return bootstrap.session.signOut();
      },
    });
    const agentStore = new AgentStore(new AgentClient(bootstrap.authorized));
    const designerClient = new DesignerClient(bootstrap.authorized);
    const agentRuntimeClient = new AgentRuntimeClient(bootstrap.authorized);
    const workspaceStore = new WorkspaceStore(
      new WorkspaceClient(bootstrap.authorized),
    );
    const lifecycle = new ConversationLifecycle(
      window,
      bootstrap.authorized,
      bootstrap.conversations,
      (conversationId) => sourceClient.selectConversation(conversationId),
    );
    const initial = await lifecycle.mount(
      bootstrap.conversation,
      bootstrap.conversationTransport,
    );
    let current = initial;
    window.addEventListener("pagehide", () => lifecycle.dispose(current), {
      once: true,
    });
    root.render(
      <React.StrictMode>
        <CorpusApplication
          initial={initial}
          lifecycle={lifecycle}
          session={bootstrap.session}
          registry={createCorpusSurfaceRegistry(
            sourceClient,
            agentStore,
            workspaceStore,
            designerClient,
            agentRuntimeClient,
          )}
          uploadChatSource={(file) => uploadChatSource(sourceClient, file)}
          isAnonymous={() => bootstrap.session.principal?.type === "anonymous"}
          onMounted={(mounted) => { current = mounted; }}
        />
      </React.StrictMode>,
    );
  } catch (error) {
    root.render(
      <FatalShell
        fallback="Corpus could not establish an authenticated conversation."
      />,
    );
  }
}

function CorpusApplication({
  initial,
  lifecycle,
  session,
  registry,
  uploadChatSource,
  onMounted,
  isAnonymous,
}: {
  initial: MountedConversation;
  lifecycle: ConversationLifecycle;
  session: BootstrappedCorpusConnection["session"];
  registry: ReturnType<typeof createCorpusSurfaceRegistry>;
  uploadChatSource(file: File): Promise<{ attachmentId: string; displayName: string; kind: "api_definition" | "api_description" }>;
  onMounted(mounted: MountedConversation): void;
  isAnonymous(): boolean;
}) {
  const [mounted, setMounted] = useState(initial);
  const previous = useRef<MountedConversation | null>(null);

  useEffect(() => {
    if (previous.current !== null && previous.current !== mounted) {
      lifecycle.dispose(previous.current);
    }
    previous.current = mounted;
    onMounted(mounted);
  }, [lifecycle, mounted, onMounted]);

  const startNext = useCallback(async (anonymous: boolean) => {
    const next = await lifecycle.createNext(mounted.summary, anonymous);
    setMounted(next);
  }, [lifecycle, mounted]);

  const remountAfterCredentialRevocation = useCallback(async () => {
    const next = await lifecycle.createFresh(LOUNGE_SIGN_IN_PATH);
    lifecycle.dispose(mounted);
    previous.current = next;
    setMounted(next);
  }, [lifecycle, mounted]);

  useLayoutEffect(
    () => session.setCredentialRevocationHandler(
      remountAfterCredentialRevocation,
    ),
    [remountAfterCredentialRevocation, session],
  );

  return (
    <RouteDeckBootstrapBoundary
      key={mounted.summary.id}
      store={mounted.routeDeck.store}
      loading={<BootstrapLoadingShell />}
      recovery={(state) => (
        <CorpusRecoveryCoordinator
          state={state}
          replaceConversation={() => startNext(isAnonymous())}
        />
      )}
    >
      <ApplicationShell
          routeDeck={mounted.routeDeck}
          registry={registry}
          chatClient={mounted.chatClient}
          initialConversation={mounted.initialConversation}
          onUploadApiSource={uploadChatSource}
          header={(
            <CorpusHeader
              onNewConversation={startNext}
            />
          )}
          navigation={<FeatureNavigation />}
          mainHeader={<CorpusMainHeading />}
      />
    </RouteDeckBootstrapBoundary>
  );
}

async function uploadChatSource(
  sourceClient: SourceClient,
  file: File,
): Promise<{ attachmentId: string; displayName: string; kind: "api_definition" | "api_description" }> {
  if (/\.(?:md|markdown)$/i.test(file.name)) {
    const staged = await sourceClient.stageApiDescription(file);
    return {
      attachmentId: staged.attachment_id,
      displayName: staged.filename,
      kind: "api_description",
    };
  }
  const displayName = file.name.replace(/\.(?:json|ya?ml)$/i, "").trim() || "Uploaded API";
  const staged = await sourceClient.stageApiDefinition(displayName, file, null);
  return { attachmentId: staged.attachment_id, displayName: staged.display_name, kind: "api_definition" };
}

function FatalShell({ fallback }: { fallback: string }) {
  return (
    <section className="bootstrap-error" role="alert">
      <h1>Corpus could not load</h1>
      <p>{fallback}</p>
      <button type="button" onClick={() => window.location.reload()}>
        Retry
      </button>
    </section>
  );
}
