# RouteDeck change report: review-staging tool semantics

Date: 2026-08-09

Authority: the user explicitly authorized RouteDeck changes provided every change is reported with its purpose.

## Problem proven from Corpus

Corpus chat run `20260809T014947Z-8827b2b700` exposed a legal
`sources.approve_contract_revision` tool with `review_required: true`. The user
asked to create the corrected revision but see the final review before anything
changed. The model returned a prose-only review and refused to call the tool.
RouteDeck's model context exposed `review_required` only as JSON data; no trusted
framework instruction explained that calling the tool stages durable review and
cannot execute the operation.

## Authorized RouteDeck files changed

- `D:\Dev\AI Projects\routedeck\routedeck_langgraph\prompt.py`
  - Adds a trusted tool-semantics section before untrusted RouteDeck context.
  - Explains that a legal `review_required=true` tool stages durable review
    without execution, and that only a separate explicit acceptance can execute
    it.
  - Tells the model not to replace a requested staged review with prose.
- `D:\Dev\AI Projects\routedeck\tests\test_langgraph_policy_prompt.py`
  - Adds a regression proving the semantics are trusted prompt instructions,
    precede JSON context, and preserve the separate-acceptance boundary.

## Boundary

No RouteDeck operation, review lifecycle, persistence, tool wrapper, public
contract, or execution behavior changed. This change only makes the existing
framework-owned review semantics explicit to the model.

## Verification

```text
.venv\Scripts\python.exe -m pytest \
  tests\test_langgraph_policy_prompt.py \
  tests\test_langgraph_model_context.py \
  tests\supervision\test_review_lifecycle.py \
  tests\fastapi\test_transport_smoke.py -q

41 passed, 1 existing Starlette/httpx deprecation warning
```
