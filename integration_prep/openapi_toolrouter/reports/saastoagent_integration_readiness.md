# SaaStoAgent ToolRouter Integration Readiness

## Current Status

This prep bundle is standalone and runnable. It is not integrated with production SaaStoAgent, Corpus, RouteDeck, or the database.

Implemented:

- Full copied OpenAPI ToolRouter research snapshot.
- SaaStoAgent adapter API: `route_tool_request(...) -> ToolRouteDecision`.
- Deterministic guardrails for route, suggest, dry-run, auto-read, confirm-write, and block-write modes.
- Standard tenant/integration feedback events with secret redaction.
- Chat normalization with deterministic fallback and optional `gpt-5-nano` model path.
- Local sandbox UI for routing, sandbox-account intake, top-k review, and feedback capture.

## Product-Readiness Metrics From Snapshot

Selected decision config:

- Route confidence: `0.3`
- Route margin: `0.0`
- Param confidence: `0.0`
- Top-k confidence: `0.18`
- Unsafe write threshold: `0.2`

Headline tracks:

- Natural routing: 100 tasks, top-1 route `72.0%`, top-3 recoverability `92.0%`, top-10 recall `100.0%`, false execution `0.0%`.
- Recovery follow-up: 85 tasks, decision type `65.9%`, follow-up type `65.9%`, param questions `94.1%`, policy gaps `100.0%`, false execution `7.1%`.
- Synthetic feedback experiment: 185 synthetic events, trained model artifact present, reported separately from runtime feedback.

## Supported Decision Types

- `ROUTE`
- `SHOW_TOPK`
- `ASK_PARAM`
- `ASK_DISAMBIGUATE`
- `ASK_POLICY`
- `BLOCK_UNSAFE`

## Supported Guardrails

- `observe`
- `suggest`
- `dry_run`
- `auto_read`
- `confirm_write`
- `block_write`
- endpoint allowlist/denylist
- tag allowlist/denylist
- auth scope allowlist/denylist
- method policy override
- missing-param policy
- destructive operation detection from OpenAPI-derived method, operation class, path, summary, and description

## Can Be Integrated Now

- One-function route decisions.
- Top-k candidate cards.
- Missing-param follow-up surfaces.
- Policy-gap prompts.
- Dry-run previews.
- Feedback logging and tenant-scoped feedback model loading.

## Must Remain Dry-Run Or Confirmed

- `POST`, `PATCH`, and `PUT` routes.
- `DELETE` routes.
- Any endpoint denied by endpoint, tag, auth, or method policy.
- Any route with missing OpenAPI-required parameters.
- Any business-policy-dependent action until the user or a policy source supplies the rule.

## Known Limitations

- This bundle does not execute real API calls.
- The optional OpenAI model path only normalizes chat input; it does not choose endpoints.
- Validation depends on repaired specs and available validation libraries.
- Product-readiness metrics come from Medusa benchmark artifacts and are not a guarantee for every SaaS API.
- Training promotion is intentionally manual and requires shadow evaluation.

## Commands

From `vendor/openapi_toolrouter_benchmark`:

```powershell
python -m pytest tests/test_saastoagent_integration.py -q
python -m toolrouter chat-route --query "list products" --artifacts artifacts --guardrails "{\"mode\":\"suggest\"}"
python -m toolrouter feedback-log --out data/feedback_events.jsonl --tenant-id tenant-a --integration-id medusa --query "list products" --decision-type ROUTE
python -m toolrouter train-feedback --feedback data/feedback_events.jsonl --artifacts artifacts --out artifacts/feedback_ranker.joblib
python -m toolrouter evaluate-feedback --feedback data/feedback_events.jsonl --artifacts artifacts --out reports/feedback_shadow_eval.json
python -m toolrouter sandbox --artifacts artifacts --feedback-log data/sandbox_feedback_events.jsonl
```

## Latest Prep Verification

- `python -m pytest tests/test_saastoagent_integration.py -q`: 12 passed.
- `python -B -m pytest tests -q -p no:cacheprovider`: 47 passed.
- `chat-route`, `feedback-log`, `evaluate-feedback`, `train-feedback`, and `sandbox --help` were exercised through Typer's CLI runner.
