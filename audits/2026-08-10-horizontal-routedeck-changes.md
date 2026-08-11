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

7. **Durable chat summary after review staging**
   - Files: `routedeck_core/ports/agent_driver.py`,
     `routedeck_core/supervision/{runner,review_staging,turns}.py`,
     `routedeck_core/conversation_runs.py`,
     `routedeck_langgraph/{agent_driver,middleware,tool_wrapper}.py`,
     `routedeck_fastapi/{conversation_stream,conversation_replay}.py`,
     `routedeck_fastapi/routes/conversation.py`, tests and framework docs.
   - Purpose: a review-requiring chat tool no longer terminates at the tool
     observation. RouteDeck keeps only that parent chat lease active, makes the
     post-stage model request text-only, rejects every same-turn tool call,
     streams and durably appends the model-authored public review summary, then
     records the parent mutation as `requires_review` and releases the lease.
     A later explicit user turn still owns accept/reject authority. Exact replay
     returns the saved assistant summary plus review metadata without invoking
     the model again.

8. **Cross-process stable NavGraph session identity**
   - RouteDeck files: `routedeck_core/app/compiled.py` and
     `tests/app/test_compiled_contract.py`.
   - Corpus evidence path: deployed public session
     `ses_9ae6292875e941b0b23d637ea9a95b2c` for immutable build NavGraph
     `dce97293bd28829c17fc04d088282f0c91f459109a21f65121cdab57c459c76f`.
   - Proven framework gap: `CompiledApplication.contract_documents()` passed
     Pydantic's process-order serialization of `frozenset[OperationSource]`
     directly into `compiled-navgraph.json`. RouteDeck session identity hashes
     that exact document. Fresh processes with `PYTHONHASHSEED=1`, `2`, and `3`
     produced three different hashes for one unchanged Medusa NavGraph; four
     fresh Corpus-container probes for one immutable Agent NavGraph alternated
     between `3ba08c...cb88` and `bd6b12...61fa`. An ordinary backend restart
     therefore made an unchanged deployed public session fail with
     `session_upgrade_required`.
   - Smallest change: recursively canonicalize only the unordered
     `allowed_sources` arrays in `compiled-navgraph.json`. Ordered semantic
     arrays, frontend contracts, executable paths, operations, transitions,
     policies, and surface declarations keep their declared order.
   - Purpose: the same immutable compiled NavGraph now has one RouteDeck
     `navgraph_version` across processes, so SQL session reload survives an
     ordinary backend restart without weakening schema or contract checks.
   - Compatibility: sessions written with a historical nondeterministic hash
     remain fail-closed as `session_upgrade_required`; no compatibility alias,
     hash suppression, fallback session, or state rewrite was added. New
     sessions use the stable canonical identity.
   - Validation: the new cross-seed regression failed with three distinct
     hashes before the change. After the change,
     `tests/app/test_compiled_contract.py`,
     `tests/state/test_runtime_builder.py`, and
     `tests/sqlite/test_persistent_runtime_smoke.py` pass 17/17.
   - Reason: retained Corpus chat run
     `20260810T160143Z-d352099c85` proved the review and user/tool history were
     durable and the session idle, but no post-tool model invocation or
     assistant terminal existed. RouteDeck's trusted prompt already required a
     summary and wait; Corpus could not repair the framework-owned model loop,
     lease, mutation, and replay transaction without duplicating RouteDeck.

## Explicitly rejected/removed approach

A generic mechanical “post-completion backtrack” guard was tested and removed.
It overblocked legitimate owner requests that explicitly required a later
return/navigation outcome. It is not part of the current RouteDeck behavior.

## Validation boundary

- Full RouteDeck Python suite after the observation/replay correction:
  604 passed with one dependency deprecation warning after the review-summary
  correction.
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
- The retained chat run `20260810T160143Z-d352099c85` remains failed historical
  evidence. Focused real SQLite chat now proves the second model call, durable
  assistant-plus-review terminal, text-only same-turn context, exact replay,
  and released lease; replacement Corpus chat-only and hybrid browser evidence
  is still required.
