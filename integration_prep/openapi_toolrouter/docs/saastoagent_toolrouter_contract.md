# SaaStoAgent ToolRouter UI Contract

## Decision Rendering

`ROUTE`

- Show the selected method/path and a dry-run preview.
- For reads, allow Corpus to propose an auto-read action only if guardrails permit `auto_read`.
- For writes, keep the next action in review/confirmation flow.

`SHOW_TOPK`

- Show the top three endpoint cards.
- Each card should show method, path, summary, confidence, missing params, and risk.
- User selection becomes explicit feedback.

`ASK_PARAM`

- Ask for the exact missing OpenAPI fields or params.
- Preserve the selected endpoint context.
- Provided values become feedback `provided_params`.

`ASK_DISAMBIGUATE`

- Show the plausible endpoint choices and ask which workflow the user means.
- Do not hide ambiguity behind an automatic route.

`ASK_POLICY`

- Explain that OpenAPI exposes possible actions but not the business rule.
- Ask for a policy source or user decision.
- Do not infer hidden business policy from OpenAPI.

`BLOCK_UNSAFE`

- Show why the guardrail blocked or paused the route.
- Offer only allowed next steps: keep dry-run, request confirmation, ask for policy override, or change guardrail configuration.
- Do not execute the endpoint from this decision alone.

## Decision Shape

The adapter returns:

```json
{
  "decision_type": "ROUTE",
  "selected_endpoint": "fixture:ListProducts",
  "selected_method": "GET",
  "selected_path": "/store/products",
  "top_candidates": [],
  "confidence": 0.0,
  "missing_params": [],
  "follow_up_question": null,
  "guardrail_decision": {
    "mode": "auto_read",
    "requires_confirmation": false,
    "reason": "Read endpoint allowed by guardrails."
  },
  "validation": {
    "required_params_covered": true,
    "request_body_schema_pass": true,
    "validation_pass": true,
    "errors": []
  },
  "feedback_event_id": "uuid-or-null"
}
```

## Corpus/RouteDeck Boundary

- Corpus owns conversation, proposal copy, and which legal operation to request.
- RouteDeck/graph owns legal operation validation and state commits.
- ToolRouter owns endpoint ranking, guardrail decisioning, validation preview, and feedback event creation.
- The UI must not render raw eligible endpoints as default product controls. It renders agent-authored proposals, active surfaces, and diagnostics.
