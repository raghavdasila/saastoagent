import React from "react";
import { createRoot } from "react-dom/client";
import {
  createRouteDeckAgentClient,
  createRouteDeckClient,
} from "@routedeck/core";
import { RouteDeckBootstrapBoundary } from "@routedeck/react";

import { ApplicationShell } from "./app/ApplicationShell";
import { bootstrapCorpusConnection } from "./app/bootstrapConnection";
import { BootstrapLoadingShell } from "./app/BootstrapLoadingShell";
import { BootstrapRecoveryShell } from "./app/BootstrapRecoveryShell";
import { CorpusHeader } from "./app/CorpusHeader";
import { CorpusMainHeading } from "./app/CorpusMainHeading";
import { FeatureNavigation } from "./app/FeatureNavigation";
import { loadRouteDeck } from "./app/loadRouteDeck";
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
    const routeDeckClient = createRouteDeckClient({
      baseUrl: "/api/routedeck",
      fetch: bootstrap.conversationTransport.fetch,
      credentials: "omit",
    });
    const chatClient = createRouteDeckAgentClient({
      baseUrl: "/api/routedeck",
      fetch: bootstrap.conversationTransport.fetch,
    });
    const routeDeck = await loadRouteDeck(window, routeDeckClient);
    const initialConversation = await chatClient.loadConversation();
    window.addEventListener("pagehide", () => routeDeck.store.dispose(), {
      once: true,
    });
    root.render(
      <React.StrictMode>
        <RouteDeckBootstrapBoundary
          store={routeDeck.store}
          loading={<BootstrapLoadingShell />}
          recovery={(state) => <BootstrapRecoveryShell state={state} />}
        >
          <ApplicationShell
            routeDeck={routeDeck}
            registry={createCorpusSurfaceRegistry(sourceClient)}
            chatClient={chatClient}
            initialConversation={initialConversation}
            header={<CorpusHeader />}
            navigation={<FeatureNavigation />}
            mainHeader={<CorpusMainHeading />}
          />
        </RouteDeckBootstrapBoundary>
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
