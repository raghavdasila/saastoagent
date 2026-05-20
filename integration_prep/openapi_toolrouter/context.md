# Standalone OpenAPI ToolRouter Prep Context

Last updated: 2026-05-20
Status: Standalone integration-prep bundle. Not wired into SaaStoAgent runtime, Corpus graph, RouteDeck store, or production UI.

## North Star

This folder is the isolated work area for turning the OpenAPI ToolRouter research benchmark into a SaaStoAgent-ready router module. Work here should make the router easier to test, inspect, train from output corrections, and eventually hand off to SaaStoAgent without modifying production SaaStoAgent code.

Use this folder when improving the adapter, guardrails, feedback loop, sandbox, local contracts, or integration readiness docs. Use `D:\Dev\AI Projects\agent-core\research\openapi_toolrouter_benchmark` when continuing pure research or benchmark optimization.

## Isolation Rules

- This prep bundle must run from inside this folder without importing SaaStoAgent production runtime code.
- Do not wire this code into Corpus, RouteDeck, the live SaaStoAgent frontend, or the live backend in this slice.
- Keep all prep-specific code, docs, reports, feedback logs, and sandbox assets under this folder.
- The copied vendor router is allowed to diverge from the research folder for integration-prep reasons.
- If the research folder changes later, refresh or compare explicitly. Do not assume this snapshot updates automatically.

## Source Of Truth

- Raw OpenAPI specs are the routing source of truth.
- Repaired OpenAPI specs are validation artifacts only.
- OpenAPI-derived endpoint metadata can be used for routing, validation, and guardrail evidence.
- Do not add Medusa endpoint maps, Medusa-specific routing rules, action lexicons, stopword lists, or hidden business-policy inference.
- Do not add GraphSAGE work to this prep slice.

## Runtime Boundary

The adapter returns structured decisions. It does not execute live SaaS writes.

Allowed decision behavior:

- High confidence: return a selected endpoint decision.
- Medium confidence: return top candidates for user or upstream-agent selection.
- Missing parameters: ask for exact missing values.
- Missing business policy: ask for a policy source or user decision.
- Write/delete risk: dry-run or require confirmation according to deterministic guardrails.
- Unsafe operation: block when guardrails require it.
- Every decision can emit a feedback event.

Writes remain dry-run-only in this prep bundle. A future SaaStoAgent execution layer must separately verify guardrail permission, explicit confirmation, credentials, and policy before any real write.

## Folder Map

- `vendor/openapi_toolrouter_benchmark/`: copied research snapshot with source, tests, data, artifacts, reports, and notebooks.
- `vendor/openapi_toolrouter_benchmark/context.md`: vendor-local run context for working directly inside the copied router.
- `vendor/openapi_toolrouter_benchmark/toolrouter/integration/`: SaaStoAgent-facing adapter, schemas, guardrails, feedback, and chat normalization.
- `vendor/openapi_toolrouter_benchmark/sandbox/`: local browser workbench for chat-style routing and output-based feedback.
- `docs/saastoagent_toolrouter_contract.md`: future UI rendering contract.
- `plans/openapi_toolrouter_integration_plan.md`: future integration sequence.
- `reports/saastoagent_integration_readiness.md`: readiness, boundaries, metrics, commands, and limitations.
- `SOURCE_SNAPSHOT.md`: source snapshot provenance and divergence rule.

## Main API

```python
from toolrouter.integration import route_tool_request

decision = route_tool_request(
    tenant_id="tenant-a",
    integration_id="medusa",
    user_query="list products",
    conversation_context=[],
    artifacts_path="artifacts",
    guardrail_config={"mode": "suggest"},
    feedback_log_path="data/feedback_events.jsonl",
    feedback_model_path=None,
)
```

## Local Runbook

Run these from `vendor/openapi_toolrouter_benchmark`:

```powershell
python -B -m pytest tests -q -p no:cacheprovider
python -m toolrouter chat-route --query "list products" --artifacts artifacts --guardrails "{\"mode\":\"suggest\"}"
python -m toolrouter sandbox --artifacts artifacts --feedback-log data/sandbox_feedback_events.jsonl
```

Sandbox URL:

```text
http://127.0.0.1:8765/
```

The sandbox uses deterministic passthrough normalization by default. Set `OPENAI_ROUTER_MODEL=gpt-5-nano` and pass `--use-model` only when a real OpenAI API key is intentionally available. If no key is configured, keep deterministic mode so tests stay local and repeatable.

## Current Verification

Last verified in this prep bundle:

```text
python -B -m pytest tests -q -p no:cacheprovider
47 passed
```

Snapshot copy check against `research/openapi_toolrouter_benchmark`:

```text
source_files=88
vendor_files=100
missing_from_vendor=0
different_hashes=1
different file: toolrouter/__main__.py
```

The changed copied file is expected because the prep snapshot adds SaaStoAgent-facing CLI commands. Extra files are expected prep additions.

## Feedback And Training

Feedback is output-based. User, agent, validator, executor, and benchmark corrections should become feedback events with tenant and integration fields.

Rules:

- Tenant-specific feedback models are preferred first.
- Global models should only use high-quality explicit feedback.
- Synthetic feedback must remain labeled separately.
- Do not silently promote a trained feedback model.
- Run shadow evaluation before promotion.
- Redact credentials and secret-looking values in feedback logs.

## Safe Improvement Areas

Good isolated follow-up work in this folder:

- Improve `toolrouter/integration/` schemas, guardrails, validation, and feedback quality.
- Improve sandbox UX and decision rendering.
- Add more contract examples in `docs/`.
- Add integration-prep tests for new decision paths.
- Add shadow-evaluation reports under `reports/`.
- Add sample feedback logs or fixtures only if credentials and secrets are redacted.

Avoid in this folder:

- Production SaaStoAgent runtime integration.
- Corpus or RouteDeck store writes.
- Live SaaS API execution.
- Research benchmark optimization unless the change directly supports integration readiness.
- Hardcoded app-specific routing shortcuts.
