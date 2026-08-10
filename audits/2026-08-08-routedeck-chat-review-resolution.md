# RouteDeck Change Report: Chat Review Resolution

Date: 2026-08-08

Authorization: the user explicitly authorized RouteDeck changes on 2026-08-08
provided every change is reported with its purpose. The sibling checkout is
otherwise still treated as a separate repository.

## Why the framework change was necessary

Corpus already staged durable RouteDeck reviews and could accept or reject them
from a review surface. A normal user chat turn could observe that a review was
pending, but the LangGraph adapter exposed no model-callable way to resolve the
current review. Corpus could not correctly duplicate that lifecycle, and asking
the user to provide a review ID or click a named surface would be spoon-fed
choreography rather than a genuine chat path.

## Exact RouteDeck changes

Source:

- `routedeck_langgraph/review_tools.py`: defines two framework-owned,
  empty-input actions, accept current review and reject current review.
- `routedeck_langgraph/model_context.py`: when one current review is pending,
  exposes only those two tools and suppresses normal product tools and suggested
  actions for that invocation. It never includes the review ID.
- `routedeck_langgraph/tool_wrapper.py`: resolves the pending review from the
  current server-side session and invokes the existing runner accept/reject
  lifecycle using the active user chat turn.
- `routedeck_core/supervision/review_actions.py`: permits accept/reject to reuse
  an active chat lease and its fenced child-attempt path. The ordinary FastAPI
  review path remains backward compatible. Acceptance still rechecks version,
  expiry, operation spec, entities, providers, guards, and current authority.

Focused proof:

- `tests/test_langgraph_model_context.py`: pending review exposes only two
  empty-input tools and serializes no review ID.
- `tests/supervision/test_review_lifecycle.py`: current-chat acceptance reuses
  the parent lease, executes exactly once, leaves the parent turn active for
  assistant completion, and the actual wrapper accepts without an ID or direct
  handler execution.

Canonical RouteDeck documentation updated:

- `docs/route-deck-reference.md`
- `architecture/components/langgraph-adapter.md`
- `architecture/feature-coverage.md`
- `SYSTEM_FLOW_INDEX.md`
- `test_index/README.md`

## Ownership boundary

RouteDeck owns only durable review state, legal resolution, lease/fencing, and
accept-time revalidation. Corpus continues to own product review copy,
consequences, product handlers, surfaces, prompts, and business outcomes. No
Corpus behavior, product operation, or fallback was added inside RouteDeck.

## Validation

Focused command:

```powershell
D:\Dev\AI Projects\routedeck\.venv\Scripts\python.exe -m pytest tests\test_langgraph_model_context.py tests\supervision\test_review_lifecycle.py -q
```

Result: `27 passed`.

Expanded affected command:

```powershell
D:\Dev\AI Projects\routedeck\.venv\Scripts\python.exe -m pytest tests\app tests\supervision tests\context tests\test_langgraph_agent_driver.py tests\test_langgraph_model_context.py tests\test_langgraph_policy_prompt.py tests\test_public_api.py -q
```

Result: `255 passed`.

This report records the framework edit only. It is not evidence that Corpus's
chat-only, surface-only, or hybrid product journeys are complete; those require
separate real-product evidence under the non-spoon-fed rubric.
