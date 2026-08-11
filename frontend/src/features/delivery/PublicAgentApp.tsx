import type { AgentConversationMessage, AgentStreamStatus } from "@routedeck/react";
import { Bot, LockKeyhole } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Composer } from "@/app/Composer";
import { Conversation } from "@/app/Conversation";
import { Button } from "@/components/ui/button";

interface PublicAgentProjection {
  readonly revision: number;
  readonly messages: readonly Readonly<Record<string, unknown>>[];
  readonly awaiting_clarification: boolean;
}

const EMPTY_AGENT: PublicAgentProjection = {
  revision: 0,
  messages: [],
  awaiting_clarification: false,
};

export function PublicAgentApp({ slug }: { slug: string }) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [agent, setAgent] = useState<PublicAgentProjection>(EMPTY_AGENT);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [conversationGeneration, setConversationGeneration] = useState(0);
  const messages = useMemo(() => publicMessages(agent), [agent]);
  const status: AgentStreamStatus = error !== null ? "error" : busy ? "streaming" : "idle";

  useEffect(() => {
    let active = true;
    const key = publicSessionKey(slug);
    const retainedSessionId = window.sessionStorage.getItem(key);
    const request = retainedSessionId === null
      ? fetch(`/api/public/agents/${encodeURIComponent(slug)}/sessions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" })
          .then(async (response) => {
            if (!response.ok) throw new Error(await problem(response));
            const value = await response.json() as { session: { session_id: string }; agent: PublicAgentProjection };
            window.sessionStorage.setItem(key, value.session.session_id);
            return { sessionId: value.session.session_id, agent: value.agent };
          })
      : fetch(`/api/public/agents/${encodeURIComponent(slug)}/sessions/${encodeURIComponent(retainedSessionId)}`)
          .then(async (response) => {
            if (!response.ok) throw new Error(await problem(response));
            return { sessionId: retainedSessionId, agent: await response.json() as PublicAgentProjection };
          });
    void request
      .then((value) => { if (active) { setSessionId(value.sessionId); setAgent(value.agent); setError(null); } })
      .catch((caught) => active && setError(text(caught)))
      .finally(() => active && setBusy(false));
    return () => { active = false; };
  }, [conversationGeneration, slug]);

  async function send(message: string) {
    if (sessionId === null || message.trim() === "") return;
    setBusy(true); setError(null);
    try {
      const response = await fetch(`/api/public/agents/${encodeURIComponent(slug)}/sessions/${encodeURIComponent(sessionId)}/messages`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: message.trim() }),
      });
      if (!response.ok) throw new Error(await problem(response));
      const value = await response.json() as { agent: PublicAgentProjection };
      setAgent(value.agent);
    } catch (caught) {
      setError(text(caught));
      throw caught;
    } finally { setBusy(false); }
  }

  function startNewConversation() {
    window.sessionStorage.removeItem(publicSessionKey(slug));
    setSessionId(null);
    setAgent(EMPTY_AGENT);
    setError(null);
    setBusy(true);
    setConversationGeneration((value) => value + 1);
  }

  return <div className="public-agent" data-public-agent-application="">
    <header className="public-agent__header">
      <div className="public-agent__brand"><span className="corpus-mark" aria-hidden="true"><Bot /></span><span><strong>{displayName(slug)}</strong><small>Hosted by Corpus</small></span></div>
      <span className="public-agent__status" data-status={status}><i aria-hidden="true" />{busy ? "Working…" : error === null ? "Ready" : "Unavailable"}</span>
    </header>
    <main className="public-agent__main">
      <section className="public-agent__identity" aria-labelledby="public-agent-title">
        <div><p>Deployed Agent</p><h1 id="public-agent-title">{displayName(slug)}</h1><span>Ask a question and continue the same request when the Agent needs one more detail.</span></div>
        <span><LockKeyhole aria-hidden="true" /> Session-scoped conversation</span>
      </section>
      {error === null ? null : <div className="public-agent__error" data-public-agent-recovery="">
        <p role="alert">{error}</p>
        <Button type="button" variant="outline" onClick={startNewConversation}>Start a new conversation</Button>
      </div>}
      {agent.awaiting_clarification ? <section className="public-agent__clarification" aria-label="Agent needs more information">
        <p>Current request</p><h2>One detail needed</h2>
        <span>Answer the Agent's question below to continue the same request.</span>
      </section> : null}
      <section className="public-agent__workspace" aria-label={`${displayName(slug)} conversation`}>
        {messages.length === 0 && !busy ? <p className="public-agent__empty">Ask the deployed Agent a question.</p> : null}
        <Conversation messages={messages} status={status} suggestedActions={null} />
        <div data-agent-input-dock="">
          <Composer disabled={busy || sessionId === null} showCancel={false} disabledReason={error === null ? undefined : "This Agent is currently unavailable."} onSend={send} onCancel={() => undefined} />
        </div>
      </section>
    </main>
  </div>;
}

function publicMessages(agent: PublicAgentProjection): AgentConversationMessage[] {
  return agent.messages.flatMap((item, index) => {
    const role = item.role;
    const content = item.content;
    if ((role !== "user" && role !== "assistant") || typeof content !== "string") return [];
    return [{ id: `public:${agent.revision}:${index}`, requestId: null, role, content, status: "finalized" as const }];
  });
}

function displayName(slug: string): string {
  const words = slug.split("-").filter(Boolean).map((word) => word[0]?.toUpperCase() + word.slice(1));
  return words.join(" ") || "Deployed Agent";
}

function publicSessionKey(slug: string): string {
  return `corpus.public-agent-session.v1:${slug}`;
}

async function problem(response: Response) { const value = await response.json().catch(() => ({})) as { message?: string }; return value.message ?? "This public Agent is unavailable."; }
function text(value: unknown) { return value instanceof Error ? value.message : "This public Agent is unavailable."; }
