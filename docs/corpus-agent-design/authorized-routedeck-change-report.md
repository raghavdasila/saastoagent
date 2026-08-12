# Authorized RouteDeck change report

This report records only RouteDeck changes made under the owner's explicit
cross-repository authorization while completing Corpus integration. The
sibling RouteDeck checkout remains independently owned; unrelated existing
changes in that checkout are not part of this report.

## 2026-08-11 — accept a review on the immediately following chat turn

### Product requirement

Corpus can stage a required review in one ordinary chat turn and accept it in
the owner's immediately following chat turn. The review must still become
stale after any intervening finalized chat turn or incompatible projection
change, and all normal expiry, operation-spec, provider, guard, entity, and
accept-time checks remain authoritative.

### Proven framework gap

RouteDeck recorded the staged review before finalizing the assistant summary
for that chat turn. Starting the owner's next chat turn advanced the projection
again, so a legitimate review was exactly two projection versions behind and
was rejected as stale. The existing exception covered only one version.

### RouteDeck files and purpose

- `D:\Dev\AI Projects\routedeck\routedeck_core\supervision\review_actions.py`
  — allow a two-version projection delta only when the review was staged by a
  chat turn, the last durable conversation turn is the assistant finalization
  of that exact parent request, and the current interaction is the immediately
  following active chat turn. The existing one-version allowance is retained.
- `D:\Dev\AI Projects\routedeck\tests\supervision\test_review_lifecycle.py`
  — add the real stage/finalize/begin-next-turn/accept regression.

### Compatibility and safety boundary

This does not loosen operation legality, review policy, expiry, operation-spec
identity, providers, guards, entity bindings, or accept-time rechecks. A
different finalized chat turn, a non-chat projection change, a missing parent
turn, a mismatched request identity, or a larger projection delta still fails
closed as stale.

### Validation

- Targeted review lifecycle: `16 passed`.
- RouteDeck supervision suite: `130 passed`.
- Full RouteDeck suite: `546 passed`, with one pre-existing Starlette warning.
- Corpus replacement chat run proved the previously stale review completed;
  that retained run remained failed because it subsequently exposed a separate
  Corpus Source-surface revision-coherence defect. The retained failure was not
  rewritten as passing evidence.

## 2026-08-11 — inspect refreshed legal tools after navigation

### Product requirement

An ordinary owner request may require navigation followed by further legal
work. RouteDeck must keep the same user goal active across that navigation and
must not let the model claim the next action is unavailable when the refreshed
node exposes a legal operation that advances the still-unfinished request.

### Proven framework gap

Retained Corpus chat run `20260811T114034Z-a5069dc140` used the configured real
OpenAI model. It completed `workspace.open_sources`, received a refreshed
`sources.home` projection where `sources.open_api_creation` was legal and
visibly available, then stopped and incorrectly said that the next setup action
was unavailable. The existing trusted semantics said to continue after
navigation, but did not explicitly require checking the refreshed legal-tool
set before making an availability claim.

### RouteDeck files and purpose

- `D:\Dev\AI Projects\routedeck\routedeck_langgraph\prompt.py` — clarify the
  generic trusted navigation semantics: inspect refreshed `legal_tools`, call a
  legal operation that advances an unfinished explicit user outcome, and do not
  claim it is unavailable.
- `D:\Dev\AI Projects\routedeck\tests\test_langgraph_policy_prompt.py` — lock
  the refreshed-tool and unfinished-outcome wording.
- `D:\Dev\AI Projects\routedeck\docs\route-deck-reference.md` — document the
  same framework-owned behavior.

### Compatibility and safety boundary

This is prompt semantics only. It does not add an operation, infer completion,
dispatch a tool, alter arguments, expand legality, weaken review/guard/provider
checks, or prevent a navigation-only request from completing after its requested
destination opens. Every subsequent tool remains limited to the freshly loaded
legal set and the canonical RouteDeck runner.

### Validation

- RouteDeck prompt, real-driver, and middleware contract set: `24 passed`.
- Replacement Corpus chat-only and hybrid browser evidence remain required;
  the retained failed run remains immutable.

## 2026-08-11 — carry a bounded public surface outcome into the next chat turn

### Product requirement

After the owner performs a non-navigation action through a Corpus surface, the
configured Agent must be able to continue the same task from that public typed
outcome without asking the owner to repeat it or copying private form values
into model context.

### Proven framework gap

RouteDeck persisted the supervised operation result, but its model context did
not expose the most recent surface-only completion. A later chat turn could
therefore repeat or contradict a successful surface action even though the
same RouteDeck session already owned the result.

### RouteDeck files and purpose

- `D:\Dev\AI Projects\routedeck\routedeck_core\contracts\session.py`,
  `routedeck_core\state\effects.py`, and
  `routedeck_core\supervision\outcome_commits.py` — retain at most eight typed
  public non-navigation surface observations, preserve them across navigation,
  and clear them after any newer successful non-surface action so stale
  cross-source ordering is never presented as current.
- `D:\Dev\AI Projects\routedeck\routedeck_langgraph\model_context.py` and
  `routedeck_langgraph\prompt.py` — project the bounded argument-free public
  observations into trusted model context as actions since the last newer
  other-source action.
- RouteDeck supervision, model-context, prompt, and SQLite persistence tests —
  prove append, clearing, serialization, reload, and absence of arguments.

### Compatibility and safety boundary

Only the typed public operation observation is retained. Request arguments,
private forms, credentials, and entity identities are absent. Navigation does
not erase a still-current observation; a successful Agent or other non-surface
action does. This is context continuity, not new authority or execution.

### Validation

- Focused RouteDeck context/prompt tests passed during review.
- Full RouteDeck core suite passed during the same correction round.
- Replacement Corpus hybrid browser evidence remains required; retained failed
  runs were not rewritten.

## 2026-08-11 — fail closed on invented provider tool names

### Product requirement

The configured model must call only the exact provider-safe name exposed in
the current `legal_tools` list. Raw internal operation IDs, aliases, guessed
names, and reconstructed names must never execute. One safe correction may
help a serial model call recover without persisting invented arguments or stale
guidance into later conversation history.

### Proven framework gap

An unregistered provider name previously fell through as its own operation ID.
If that string collided with a real internal operation or review ID, it could
reach the canonical runner when otherwise legal. The first correction design
also risked retaining the rejected call's arbitrary arguments and temporary
legal-name guidance as a durable conversation tool turn.

### RouteDeck files and purpose

- `D:\Dev\AI Projects\routedeck\routedeck_langgraph\tool_wrapper.py` — require
  an exact provider-name registry match, reject every unknown name before the
  review or operation runner, permit at most one correction for one serial tool
  envelope, and reload the exact current legal-name snapshot for that
  correction.
- `D:\Dev\AI Projects\routedeck\routedeck_langgraph\conversation.py` — omit
  the complete typed provider-rejection call/result pair from durable turns so
  invented names, arbitrary arguments, and temporary guidance cannot enter
  future model history.
- `D:\Dev\AI Projects\routedeck\docs\route-deck-reference.md` — document exact
  opaque provider-name use, raw-ID non-execution, serial correction, fresh
  validation, and durable-history omission.
- RouteDeck middleware and real AgentDriver tests — cover raw internal IDs,
  review-ID collisions, parallel calls, a credential canary in rejected
  arguments, corrected execution, durable conversation output, and the next
  reconstructed turn.

### Compatibility and safety boundary

The correction contains only static framework text, one current session
version, and provider-safe legal names. It never copies the invented name or
arguments. A corrected registered call still passes the normal current-state
legality, review, guard, provider, entity, argument, and outcome checks. Parallel
or repeated unknown calls fail loudly without execution.

### Validation

- Targeted middleware and real-driver regressions passed.
- Focused RouteDeck set passed `61/61`; the reviewed full suite passed `538`
  tests.
- Replacement Corpus chat-only and hybrid browser evidence remains required.
