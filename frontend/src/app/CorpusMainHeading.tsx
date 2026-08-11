import { RouteDeckStatus, useRouteDeckCurrentNode } from "@routedeck/react";

import { presentCorpusStatus } from "./corpusStatus";
import { corpusLocation } from "./corpusLocation";

export function CorpusMainHeading() {
  const currentNode = useRouteDeckCurrentNode();
  const heading = corpusLocation(currentNode);

  return (
    <>
      <div>
        <h1>{heading.title}</h1>
        <p>{heading.description}</p>
      </div>
      <RouteDeckStatus>
        {(status) => {
          const presented = presentCorpusStatus(status);
          return (
            <span
              className="workspace-ready"
              data-status={status.code}
              data-status-tone={presented.tone}
            >
              <i aria-hidden="true" />
              <span>{presented.label}</span>
              {presented.detail === null ? null : (
                <small>{presented.detail}</small>
              )}
            </span>
          );
        }}
      </RouteDeckStatus>
    </>
  );
}
