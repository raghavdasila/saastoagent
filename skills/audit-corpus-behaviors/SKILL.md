---
name: audit-corpus-behaviors
description: Record, validate, inspect, or incrementally update the screenshot-backed Corpus behavior evidence ledger. Use for local as-is Design Studio behavior campaigns, BFS behavior audits, ledger/task/dashboard maintenance, evidence-backed retesting, or explaining the canonical audit process; not for fixing product behavior during the audit.
---

# Audit Corpus Behaviors

Use the existing direct Playwright recorder and the authoritative local Corpus
application. Do not create another runner, dashboard, schema, or automation
layer.

## Establish authority

1. Work only in the authoritative Corpus checkout.
2. Read `AGENTS.md`, `critical_prompt.md`, `context.md`, the latest checkpoint,
   `instructions.md`, `context_pipeline.md`, and `architecture/code-map.md`.
3. Read `docs/corpus-behavior-evidence-ledger.md` for the canonical process,
   data contract, commands, privacy rules, and completion gate.
4. Read the active or completed campaign plan relevant to the requested run.
5. Treat `docs/corpus-agent-design/workbench/design-state.json` as inventory
   authority, the running Corpus UI as observed truth, and the sibling RouteDeck
   checkout as read-only.

## Choose the operation

- For status, interpretation, or evidence review, inspect `ledger.json`,
  `tasks.json`, `index.html`, and referenced PNGs without running or mutating the
  application.
- For structural verification, run the existing recorder with
  `--validate-only`; expect regenerated timestamps and review its diff.
- For a new canonical campaign or post-fix retest, verify all documented local
  dependencies and run the existing recorder through the real UI.
- Use `--stop-after-depth` only for explicitly requested calibration. Do not
  present a depth-limited run as campaign completion.

Before a write or runtime action, state the exact audit paths, application
runtime, owner identity boundary, and acceptance evidence in scope. Product
source is read-only during an audit campaign unless the user separately
authorizes a product change outside that run.

## Preserve evidence truth

- Use one disposable owner and real UI/API-created state; never mutate the
  database or substitute fixtures, mocks, cached results, synthetic data, or a
  fallback dependency.
- Capture the full meaningful interaction sequence and responsive-risk mobile
  states. Preserve original PNGs and their SHA-256 hashes.
- Keep credentials, private mail values, tokens, cookies, headers, and one-time
  links out of tracked output.
- Continue independent branches after failure and block only genuine
  descendants.
- A missing behavior remains pending. A failed behavior remains failed. Task
  edits never create a pass.
- Keep verbose traces, videos, browser profiles, calibration runs, and dashboard
  render checks under ignored `artifacts/`.

## Handle follow-up runs

Confirm that the baseline is committed before rerunning. The recorder reuses
the ledger and appends attempt metadata only while the ordered inventory and
Design Studio source hash remain unchanged. Re-executed screenshot paths may be
overwritten; use Git history as the prior evidence baseline and review the exact
tracked diff after validation.

The current CLI has no selective behavior, feature, resume, or from-depth
filter. If the requested outcome requires one, stop and request authorization
for a recorder change. Do not manually manufacture an incremental result.

## Stop conditions

Stop and report the exact blocker when:

- the Design Studio inventory or source hash no longer matches the ledger;
- a required real dependency is unavailable;
- completion would require a database mutation, fixture, mock, or fallback;
- the run would mix another user, database, repository, runtime, or state
  lineage into the canonical evidence;
- a credential or private value may have entered tracked output;
- product or RouteDeck changes are needed to make an audit pass; or
- the required selective rerun capability is absent.

## Complete and report

Run `--validate-only`, inspect the resulting diff, and verify the HTML dashboard
at desktop and mobile sizes. Report the local runtime, exact commands, run ID,
behavior counts, screenshot count, task count, validation result, limitations,
and tracked versus ignored evidence boundary. Perform Git operations only when
the user explicitly authorizes them.
