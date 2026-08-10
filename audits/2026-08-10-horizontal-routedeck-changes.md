# RouteDeck changes for horizontal Corpus evidence

Date: 2026-08-10

RouteDeck remained a separate repository. The user explicitly authorized the
following named framework changes, and Corpus rebuilt its local Docker images
from that checkout before the accepted hybrid run.

## Accepted changes

1. **Bounded surface-to-chat continuation context**
   - Files: `routedeck_core/contracts/session.py`,
     `routedeck_core/state/effects.py`,
     `routedeck_core/supervision/outcome_commits.py`,
     `routedeck_langgraph/model_context.py`, `routedeck_langgraph/prompt.py`,
     persistence/tests/docs.
   - Purpose: retain only typed public outcomes from successful
     non-navigation surface operations so a later chat turn can continue the
     same task without receiving private surface arguments. Navigation
     preserves the context; a newer successful non-navigation action from
     another source clears it.

2. **Chronological placement of surface facts**
   - Files: `routedeck_langgraph/prompt.py`,
     `routedeck_langgraph/middleware.py`, prompt/middleware tests and
     `docs/route-deck-reference.md`.
   - Purpose: place the same argument-free public surface chronology in a
     transient framework-owned system message after older durable history and
     before the current user turn. This corrected a real hybrid failure where
     older “waiting” history contradicted a newer succeeded Sandbox surface
     result. The message is not persisted as conversation history.

3. **Opaque provider-tool correction and fail-closed lookup**
   - Files: `routedeck_langgraph/tool_wrapper.py`,
     `routedeck_langgraph/conversation.py`, prompt/docs/tests.
   - Purpose: require the exact registered provider-safe tool name, reject raw
     internal operation/review IDs, permit at most one serial correction, and
     omit the rejected call, arguments, and recovery directive from durable
     conversation/model history. Corrected calls still pass normal current
     legality, review, guard, argument, and outcome validation.

4. **Generic navigation/completion semantics**
   - Files: `routedeck_langgraph/prompt.py` and
     `docs/route-deck-reference.md` plus tests.
   - Purpose: navigation continues an unfinished multi-outcome owner request;
     a successful non-navigation result stops further tool calls only when the
   entire current request is satisfied.

5. **Private journal versus public observation boundary**
   - Files: `routedeck_core/contracts/operations.py`,
     `routedeck_core/contracts/session.py`,
     `routedeck_core/supervision/outcome_results.py`,
     `routedeck_core/supervision/outcome_commits.py`, generated contracts,
     tests and reference documentation.
   - Purpose: keep executor/journal observations private by default. A product
     must separately declare `public_outcome_schemas` and supply
     `public_observation` before a value can enter an operation response,
     model tool message or retained surface chronology. Replay preserves both
     identities without projecting the private journal payload.

6. **Terminal conversation replay deduplication**
   - Files: `routedeck_fastapi/routes/conversation.py`, transport tests and
     documentation.
   - Purpose: terminal user-message replay returns the authoritative
     conversation snapshot and terminal metadata without re-emitting finalized
     user/assistant content as live message events. Assistant-initiated entry
     replay retains its explicit assistant content result.

## Explicitly rejected/removed approach

A generic mechanical “post-completion backtrack” guard was tested and removed.
It overblocked legitimate owner requests that explicitly required a later
return/navigation outcome. It is not part of the current RouteDeck behavior.

## Validation boundary

- Full RouteDeck Python suite after the observation/replay correction:
  602 passed with one dependency deprecation warning.
- RouteDeck React: 24 passed; generated contracts and context architecture
  checks passed.
- The live Medusa cart and delivery tests now invoke user operations through
  their declared `surface` source rather than the initializer-only `system`
  source; both execute through the real local Medusa integration.
- Corpus focused Source/Builder/horizontal-recorder suite against the corrected
  local RouteDeck checkout: 157 passed with six dependency warnings; strict
  frontend typecheck passed.
- The prior hybrid run remains historical evidence only. Replacement browser
  evidence is required after the broader Source-to-Agent behavior correction.
