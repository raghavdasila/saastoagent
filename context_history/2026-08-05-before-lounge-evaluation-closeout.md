# Corpus Context Before Lounge Evaluation Closeout

Archived: 2026-08-05

This snapshot supersedes the 2026-08-03 live context. At that point Corpus had
the public Lounge, owner authentication, Workspace Home, experimental
Sources/API path, server-owned conversations, RouteDeck Agent Context
inspection, and selectable Ollama/OpenAI runtime support.

The context still described the following as pending or blocked:

- all Corpus operations needed explicit `Operation.allowed_sources` mappings;
- Lounge behavior and conversation eval definitions existed but product-journey
  execution had not yet been recorded;
- the next step was still framed as deciding how to wire the Lounge-specific
  prompt;
- validation counts were from the 2026-07-31 conversation closeout.

During the 2026-08-05 session, operation-source parity was restored, Studio
authoring gained product journeys and source-availability controls, the real
Lounge product-journey runner was added, and eight browser journeys produced
four passes plus four actionable feature failures. The new live state is in
`context.md`; the full handoff is
`context_checkpoints/2026-08-05-lounge-evaluation-and-foundation-handoff.md`.
