import {
  RouteDeckNavigationControls,
  RouteDeckStatus,
  useRouteDeckContract,
  useRouteDeckCurrentNode,
} from "@routedeck/react";
import { Bot, CircleUserRound, LogOut } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { ownerAuthClient } from "./authClient";
import { useOwnerSession } from "./OwnerSessionContext";

export function CorpusHeader() {
  const contract = useRouteDeckContract();
  const currentNode = useRouteDeckCurrentNode();
  const { session, loading, setSession } = useOwnerSession();
  const [busy, setBusy] = useState(false);
  const currentTitle =
    currentNode === null
      ? "Starting"
      : (contract.nodes[currentNode]?.title ?? currentNode);

  return (
    <>
      <div className="corpus-brand" aria-label="Corpus home">
        <span className="corpus-mark" aria-hidden="true"><Bot /></span>
        <span>
          <strong>Corpus</strong>
          <small>Workspace / {currentTitle}</small>
        </span>
      </div>
      <div className="corpus-header-controls">
        <RouteDeckNavigationControls />
        <RouteDeckStatus>
          {({ code }) => (
            <span className="corpus-status" data-status={code}>
              <i aria-hidden="true" />
              {code === "ready" ? "Ready" : code}
            </span>
          )}
        </RouteDeckStatus>
        <span className="corpus-auth-state" data-verified={session?.owner.is_verified ?? false}>
          <CircleUserRound />
          {loading
            ? "Checking account"
            : session === null
              ? "Not signed in"
              : `${session.owner.display_name ?? session.owner.email} · ${session.organization.name} · ${session.owner.is_verified ? "verified" : "unverified"}`}
        </span>
        {session === null ? null : (
          <Button
            type="button"
            size="icon"
            variant="outline"
            aria-label="Sign out"
            disabled={busy}
            onClick={() => {
              setBusy(true);
              void ownerAuthClient.signOut().then(() => {
                setSession(null);
                window.location.assign("/");
              }).catch(() => setBusy(false));
            }}
          >
            <LogOut />
          </Button>
        )}
      </div>
    </>
  );
}
