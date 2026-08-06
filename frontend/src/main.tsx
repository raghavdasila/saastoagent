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

const rootElement = document.getElementById("root");
if (rootElement === null) {
  throw new Error("Corpus requires a #root element.");
}

const root = createRoot(rootElement);
captureAuthTokenFragment(window);
root.render(<BootstrapLoadingShell />);
void start();

async function start(): Promise<void> {
  try {
    const bootstrap = await bootstrapCorpusConnection(window);
    configureOwnerAuthClient({
      transport: bootstrap.authorized,
      signOut: () => bootstrap.session.signOut(),
    });
    const sourceClient = new SourceClient(bootstrap.authorized);
    const agentStore = new AgentStore(new AgentClient(bootstrap.authorized));
    const workspaceStore = new WorkspaceStore(
      new WorkspaceClient(bootstrap.authorized),
    );
    const lifecycle = new ConversationLifecycle(
      window,
      bootstrap.authorized,
      bootstrap.conversations,
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
          )}
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
  onMounted,
  isAnonymous,
}: {
  initial: MountedConversation;
  lifecycle: ConversationLifecycle;
  session: BootstrappedCorpusConnection["session"];
  registry: ReturnType<typeof createCorpusSurfaceRegistry>;
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
