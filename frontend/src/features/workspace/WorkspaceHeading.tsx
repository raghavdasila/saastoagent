import { RouteDeckStatus } from "@routedeck/react";

export function WorkspaceHeading() {
  return (
    <>
      <div>
        <h1>Corpus Workspace</h1>
        <p>Ask Corpus what to explore, design, connect, or operate.</p>
      </div>
      <RouteDeckStatus>
        {({ code }) => (
          <span className="workspace-ready" data-status={code}>
            <i aria-hidden="true" />
            {code === "ready" ? "Ready" : code}
          </span>
        )}
      </RouteDeckStatus>
    </>
  );
}
