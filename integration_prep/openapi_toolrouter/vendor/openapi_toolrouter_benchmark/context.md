# OpenAPI ToolRouter Vendor Snapshot Context

Last updated: 2026-05-20
Status: Runnable copied snapshot inside the standalone SaaStoAgent prep bundle.

## Purpose

This folder is the runnable router workspace for isolated SaaStoAgent ToolRouter prep. It contains the copied research benchmark plus prep-only adapter, guardrail, feedback, chat, CLI, tests, and sandbox additions.

Work here when changing executable router code. Work one level up when changing handoff docs, integration plans, source provenance, or readiness reports.

## Boundary

- This folder must not import SaaStoAgent production backend, frontend, Corpus, or RouteDeck code.
- OpenAPI artifacts remain the source of truth for routing.
- Repaired OpenAPI artifacts are validation-only.
- Do not add endpoint maps, Medusa-specific routing rules, action lexicons, stopword lists, or hidden business-policy inference.
- This workspace returns route decisions and feedback events only. It does not execute real SaaS writes.

## Important Paths

- `toolrouter/`: copied router package.
- `toolrouter/integration/`: SaaStoAgent-facing adapter API, schemas, guardrails, feedback, and chat normalization.
- `sandbox/`: local browser workbench for chat-style routing and output-based feedback.
- `tests/test_saastoagent_integration.py`: prep integration tests.
- `artifacts/`: copied router artifacts.
- `data/`: copied data and local feedback logs.
- `reports/`: copied benchmark and readiness reports.

## Primary API

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

## Commands

```powershell
python -B -m pytest tests -q -p no:cacheprovider
python -m toolrouter route --help
python -m toolrouter chat-route --query "list products" --artifacts artifacts
python -m toolrouter feedback-log --help
python -m toolrouter train-feedback --help
python -m toolrouter evaluate-feedback --help
python -m toolrouter sandbox --artifacts artifacts --feedback-log data/sandbox_feedback_events.jsonl
```

Sandbox URL:

```text
http://127.0.0.1:8765/
```

## Chat Normalization

Default mode is deterministic passthrough. Optional OpenAI normalization can be enabled with `--use-model` and `OPENAI_ROUTER_MODEL`, defaulting to `gpt-5-nano` when configured.

The model may normalize user conversation into:

- `router_query`
- `provided_params`
- confirmation intent
- policy text

The model must not choose endpoint IDs, invent business policy, override guardrails, or authorize writes.

## Guardrail Modes

Supported modes:

- `observe`
- `suggest`
- `dry_run`
- `auto_read`
- `confirm_write`
- `block_write`

Writes and destructive operations must remain dry-run, confirm-required, or blocked according to deterministic guardrails. This snapshot has no live execution layer.

## Development Notes

- Prefer focused tests in `tests/test_saastoagent_integration.py` for adapter behavior.
- Keep feedback events tenant- and integration-scoped.
- Redact sandbox credentials and secret-looking fields.
- Keep prep additions independent from the original research benchmark unless intentionally refreshing the snapshot.
