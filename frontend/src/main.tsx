import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { RouteDeckBootstrapBoundary } from "@routedeck/react";

import { ApplicationShell } from "./app/ApplicationShell";
import { bootstrapCorpusConnection } from "./app/bootstrapConnection";
import { BootstrapLoadingShell } from "./app/BootstrapLoadingShell";
import { BootstrapRecoveryShell } from "./app/BootstrapRecoveryShell";
import { CorpusHeader } from "./app/CorpusHeader";
import { CorpusMainHeading } from "./app/CorpusMainHeading";
import {
  ConversationLifecycle,
  type MountedConversation,
} from "./app/conversationLifecycle";
import { FeatureNavigation } from "./app/FeatureNavigation";
import {
  configureOwnerAuthClient,
} from "./features/lounge/authClient";
import { SourceClient } from "./features/sources/sourceClient";
import {
  captureAuthTokenFragment,
} from "./features/lounge/tokenFragment";
import { createCorpusSurfaceRegistry } from "./routedeck/surfaces";
import "./styles.css";
import "./features/workspace/workspace.css";
import "./features/sources/sources.css";

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
          registry={createCorpusSurfaceRegistry(sourceClient)}
          onMounted={(mounted) => { current = mounted; }}
        />
      </React.StrictMode>,
    );
  } catch (error) {
    root.render(
      <FatalShell
        error={error}
        fallback="Corpus could not establish an authenticated conversation."
      />,
    );
  }
}

function CorpusApplication({
  initial,
  lifecycle,
  registry,
  onMounted,
}: {
  initial: MountedConversation;
  lifecycle: ConversationLifecycle;
  registry: ReturnType<typeof createCorpusSurfaceRegistry>;
  onMounted(mounted: MountedConversation): void;
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

  return (
    <RouteDeckBootstrapBoundary
      key={mounted.summary.id}
      store={mounted.routeDeck.store}
      loading={<BootstrapLoadingShell />}
      recovery={(state) => <BootstrapRecoveryShell state={state} />}
    >
      <ApplicationShell
        routeDeck={mounted.routeDeck}
        registry={registry}
        chatClient={mounted.chatClient}
        initialConversation={mounted.initialConversation}
        header={(
          <CorpusHeader
            onNewConversation={async (anonymous) => {
              const next = await lifecycle.createNext(mounted.summary, anonymous);
              setMounted(next);
            }}
          />
        )}
        navigation={<FeatureNavigation />}
        mainHeader={<CorpusMainHeading />}
      />
    </RouteDeckBootstrapBoundary>
  );
}

function FatalShell({ error, fallback }: { error: unknown; fallback: string }) {
  return (
    <section className="bootstrap-error" role="alert">
      <h1>Corpus could not load</h1>
      <p>{error instanceof Error ? error.message : fallback}</p>
      <button type="button" onClick={() => window.location.reload()}>
        Retry
      </button>
    </section>
  );
}
