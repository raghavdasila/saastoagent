# RouteDeck change report: declared operation observations in agent tool results

Date: 2026-08-09

## Purpose

Corpus chat correctly invoked `sources.inspect_current_api`, whose handler returned an observation validated against the operation's declared `outcome_schema`. RouteDeck durably journaled that observation, but `OperationResult` and the LangGraph tool message omitted it. The next model call therefore saw only `outcome=inspected` and could not use the inspected operation inventory to satisfy a natural-language curation request.

This was a framework-owned gap: Corpus could not safely duplicate RouteDeck execution results or inject private state into prompts. The change exposes only the already schema-validated operation observation through the canonical RouteDeck result path.

## RouteDeck files changed

- `D:\Dev\AI Projects\routedeck\routedeck_core\contracts\operations.py`
  - Added an empty-by-default `observation` field to `OperationResult`.
- `D:\Dev\AI Projects\routedeck\routedeck_core\supervision\outcome_results.py`
  - Propagates the validated journaled observation into completed results and exact idempotent replays.
- `D:\Dev\AI Projects\routedeck\routedeck_langgraph\tool_wrapper.py`
  - Includes a non-empty observation in the typed `routedeck_operation_result` tool artifact returned to the model.
- `D:\Dev\AI Projects\routedeck\routedeck_fastapi\responses.py`
  - Explicitly excludes model-only observations from the existing public surface-dispatch response model, preserving that HTTP contract.
- `D:\Dev\AI Projects\routedeck\tests\supervision\test_external_outcome_unknown.py`
  - Proves live completion, typed tool output, durable replay, and exact observation identity.
- `D:\Dev\AI Projects\routedeck\tests\fastapi\test_public_response_models.py`
  - Proves a completed result with an observation still serializes through surface HTTP without exposing that observation.

## Boundaries preserved

- No operation input, review, guard, provider, state-transition, or execution semantics changed.
- No observation is invented or loaded from Corpus outside RouteDeck.
- The observation has already passed the operation's declared outcome schema before it is journaled.
- Empty observations remain omitted from tool artifacts.
- Generic surface-dispatch HTTP responses remain unchanged and observation-free.
- Failure, pending-review, and private-form data are unchanged.

## Verification

`D:\Dev\AI Projects\routedeck\.venv\Scripts\python.exe -m pytest tests\fastapi\test_public_response_models.py tests\fastapi\test_transport_smoke.py tests\supervision\test_external_outcome_unknown.py tests\supervision\test_durable_supervision.py tests\supervision\test_operation_runner.py tests\supervision\test_review_lifecycle.py tests\test_langgraph_model_context.py tests\test_langgraph_agent_driver.py tests\test_langgraph_policy_prompt.py -q`

Result: `120 passed`, with one existing Starlette deprecation warning.
