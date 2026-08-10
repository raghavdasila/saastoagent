import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface PublicAgentProjection {
  readonly revision: number;
  readonly messages: readonly Readonly<Record<string, unknown>>[];
  readonly awaiting_clarification: boolean;
}

export function PublicAgentApp({ slug }: { slug: string }) {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [agent, setAgent] = useState<PublicAgentProjection>({ revision: 0, messages: [], awaiting_clarification: false });
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void fetch(`/api/public/agents/${encodeURIComponent(slug)}/sessions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" })
      .then(async (response) => {
        if (!response.ok) throw new Error(await problem(response));
        return response.json() as Promise<{ session: { session_id: string }; agent: PublicAgentProjection }>;
      })
      .then((value) => { if (active) { setSessionId(value.session.session_id); setAgent(value.agent); } })
      .catch((caught) => active && setError(text(caught)))
      .finally(() => active && setBusy(false));
    return () => { active = false; };
  }, [slug]);

  async function send() {
    if (sessionId === null || message.trim() === "") return;
    const submitted = message.trim();
    setBusy(true); setError(null); setMessage("");
    try {
      const response = await fetch(`/api/public/agents/${encodeURIComponent(slug)}/sessions/${encodeURIComponent(sessionId)}/messages`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: submitted }),
      });
      if (!response.ok) throw new Error(await problem(response));
      const value = await response.json() as { agent: PublicAgentProjection };
      setAgent(value.agent);
    } catch (caught) { setError(text(caught)); } finally { setBusy(false); }
  }

  return <main className="public-agent">
    <header><p>Hosted by Corpus</p><h1>{slug}</h1></header>
    {error === null ? null : <p role="alert">{error}</p>}
    {agent.awaiting_clarification ? <section className="public-agent__clarification" aria-label="Agent needs more information">
      <p>Current request</p><h2>One detail needed</h2>
      <span>Answer the Agent's question below to continue the same request.</span>
    </section> : null}
    <section className="public-agent__messages" aria-live="polite">{agent.messages.length === 0 ? <p>{busy ? "Starting the deployed Agent…" : "Ask the deployed Agent a question."}</p> : agent.messages.map((item, index) => <article key={`${agent.revision}-${index}`}><strong>{String(item.role ?? "agent")}</strong><p>{String(item.content ?? "")}</p></article>)}</section>
    <form onSubmit={(event) => { event.preventDefault(); void send(); }}><label htmlFor="public-agent-message">Message</label><Input id="public-agent-message" value={message} disabled={busy || sessionId === null} onChange={(event) => setMessage(event.target.value)} /><Button type="submit" disabled={busy || sessionId === null || message.trim() === ""}>Send</Button></form>
  </main>;
}

async function problem(response: Response) { const value = await response.json().catch(() => ({})) as { message?: string }; return value.message ?? "This public Agent is unavailable."; }
function text(value: unknown) { return value instanceof Error ? value.message : "This public Agent is unavailable."; }
