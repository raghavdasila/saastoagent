import { RouteDeckStatus, useRouteDeckCurrentNode } from "@routedeck/react";

const HEADING_BY_LOCATION = Object.freeze({
  lounge: {
    title: "Corpus Lounge",
    description: "Ask about Corpus or choose an account path when you are ready.",
  },
  sources: {
    title: "Corpus Sources",
    description: "Connect, inspect, and prepare the sources available to your Workspace.",
  },
  workspace: {
    title: "Corpus Workspace",
    description: "Ask Corpus what to explore, design, connect, or operate.",
  },
});

export function CorpusMainHeading() {
  const currentNode = useRouteDeckCurrentNode();
  const location = currentNode?.startsWith("lounge.")
    ? "lounge"
    : currentNode?.startsWith("sources.")
      ? "sources"
      : "workspace";
  const heading = HEADING_BY_LOCATION[location];

  return (
    <>
      <div>
        <h1>{heading.title}</h1>
        <p>{heading.description}</p>
      </div>
      <RouteDeckStatus>
        {({ code }) => (
          <span className="workspace-ready" data-status={code}>
            <i aria-hidden="true" />
            {code === "ready" ? "Ready" : "Working…"}
          </span>
        )}
      </RouteDeckStatus>
    </>
  );
}
