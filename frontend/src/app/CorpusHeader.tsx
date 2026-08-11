import {
  RouteDeckStatus,
  useRouteDeckContract,
  useRouteDeckCurrentNode,
  useRouteDeckProjection,
} from "@routedeck/react";
import { Bot, CircleUserRound, LogOut, MessageSquarePlus } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { CorpusNavigationControls } from "./CorpusNavigationControls";
import { presentCorpusStatus } from "./corpusStatus";
import { corpusLocation } from "./corpusLocation";
import { ownerAuthClient } from "../auth/authClient";
import { useOwnerSession } from "../auth/OwnerSessionContext";

export function CorpusHeader({
  onNewConversation,
}: {
  onNewConversation(anonymous: boolean): Promise<void>;
}) {
  const contract = useRouteDeckContract();
  const currentNode = useRouteDeckCurrentNode();
  const projection = useRouteDeckProjection();
  const { session, loading, setSession } = useOwnerSession();
  const [busy, setBusy] = useState(false);
  const [conversationError, setConversationError] = useState<string | null>(null);
  const interactionActive = projection?.interaction.phase === "active";
  const currentTitle =
    currentNode === null
      ? "Starting"
      : (contract.nodes[currentNode]?.title ?? currentNode);
  const currentFeature = currentNode === null
    ? "Corpus"
    : corpusLocation(currentNode).feature;

  return (
    <>
      <div className="corpus-brand" aria-label="Corpus home">
        <span className="corpus-mark" aria-hidden="true"><Bot /></span>
        <span>
          <strong>Corpus</strong>
          <small>{currentFeature} / {currentTitle}</small>
        </span>
      </div>
      <div className="corpus-header-controls">
        <Button
          type="button"
          className="corpus-new-conversation"
          variant="outline"
          aria-label="New conversation"
          disabled={busy || loading || interactionActive}
          onClick={() => {
            setBusy(true);
            setConversationError(null);
            void onNewConversation(session === null)
              .catch((error: unknown) => {
                setConversationError(
                  error instanceof Error
                    ? error.message
                    : "Corpus could not start a new conversation.",
                );
              })
              .finally(() => setBusy(false));
          }}
        >
          <MessageSquarePlus />
          <span>New conversation</span>
        </Button>
        {conversationError === null ? null : (
          <span className="corpus-header-error" role="alert">
            {conversationError}
          </span>
        )}
        <CorpusNavigationControls />
        <RouteDeckStatus>
          {(status) => {
            const presented = presentCorpusStatus(status);
            return (
              <span
                className="corpus-status"
                data-status={status.code}
                data-status-tone={presented.tone}
                title={presented.detail ?? undefined}
              >
                <i aria-hidden="true" />
                {presented.label}
              </span>
            );
          }}
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
