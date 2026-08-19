# Corpus v0.2 As-Is Behavior Evidence Audit Plan

Date: 2026-08-18

## Goal

Run the authoritative local Corpus application without changing its product
behavior, exercise every current Design Studio behavior in breadth-first order,
capture screenshot-backed observations, and render the results in a static HTML
ledger.

## Frozen scope

- Authority: `docs/corpus-agent-design/workbench/design-state.json`.
- Current inventory: 77 behavior stories across 10 features.
- Corpus: `http://127.0.0.1:5199/`.
- Backend: `http://127.0.0.1:8099/`.
- Design Studio: `http://127.0.0.1:8782/`.
- Local Medusa: `http://127.0.0.1:9100/`.
- One newly registered audit owner, one persistent browser profile, one Corpus
  database/state lineage.
- No isolated Corpus stacks, product changes, RouteDeck changes, direct database
  mutation, mocks, fallback services, TDD, or Git operations.

## Files

- Create `scripts/record_v02_behavior_audit.py`: one direct Playwright recorder
  containing the inventory reader, behavior actions, screenshot capture,
  ledger updates, and static HTML rendering.
- Create `audits/2026-08-v0.2-behavior-audit/ledger.json`.
- Create `audits/2026-08-v0.2-behavior-audit/tasks.json`.
- Create `audits/2026-08-v0.2-behavior-audit/index.html`.
- Create evidence beneath
  `audits/2026-08-v0.2-behavior-audit/evidence/<behavior-id>/<mode>/`.
- Keep videos, verbose traces, calibration runs, and dashboard-render checks
  under ignored `artifacts/`. Use one private persistent Playwright context for
  the entire canonical run, then discard its temporary credential-bearing
  browser profile when the context closes.

## Execution

1. Start the existing services without an alternate Compose project:

   ```powershell
   docker compose --env-file .env.local up -d backend source-worker frontend
   pnpm --dir docs/corpus-agent-design/workbench dev --host 0.0.0.0 --port 8782 --strictPort
   ```

2. Require HTTP 200 from Corpus, backend health/readiness, Studio, and Medusa.
   Require the configured model, worker, Mail.tm, and Corpus mail delivery path
   before behaviors that depend on them. Record explicit dependency failures.
3. Freeze all 77 stories in the ledger before the first interaction. Record each
   story's ID, feature, title, expected behavior, applicable modes, prerequisite,
   and BFS depth.
4. Register one owner through the visible Corpus account surface and retain the
   same Playwright profile for the complete run. Never serialize credentials or
   private mail links into tracked output.
5. Execute in breadth-first order: Lounge; authentication/recovery;
   Workspace; Agents and Source Hub; API Source; Agent Designer; Builder and
   Sandbox; Evaluation; Channels/Deployment/public Agent; Operations.
6. For every applicable mode, capture starting state, action, review or pending
   state, result, and resulting navigation/state. Every behavior gets desktop
   evidence; responsive-risk surfaces also get 390x844 evidence. The canonical
   ledger uses screenshots as its proof record; videos are not required.
7. A product failure remains a failed observation. A missing implementation is
   captured honestly and remains pending. A dependency failure blocks only its
   genuine descendants. Independent branches continue.
8. Append every attempt to the ledger immediately and regenerate the HTML after
   each behavior. Never reset or replace earlier run history.
9. Create one linked task for every failed, blocked, or pending behavior.
10. Validate that all 77 behaviors are represented, every applicable mode is
    classified, every result has evidence, every evidence path exists, tracked
    files contain no private values, and the HTML renders at desktop and mobile
    sizes.

## Status meanings

- `passed`: the expected behavior was visibly observed.
- `failed`: the behavior executed and contradicted the expectation.
- `blocked`: a required dependency or prerequisite prevented execution.
- `pending`: the behavior is visibly unavailable or unimplemented.
- `not_applicable`: the mode is prohibited by the behavior contract.

## Recorder commands

Run the complete canonical campaign after the local stack is ready:

```powershell
.venv\Scripts\python.exe scripts\record_v02_behavior_audit.py
```

Validate the frozen inventory, graph, task records, evidence paths and hashes,
classification completeness, diagnostics, and tracked-text secret scan without
running the application again:

```powershell
.venv\Scripts\python.exe scripts\record_v02_behavior_audit.py --validate-only
```

## Acceptance

The audit is complete only when all 77 frozen behaviors have been exercised or
visibly classified in every applicable mode, every result is screenshot-backed,
all diagnostics are classified, every non-pass links to a task, the evidence is
free of credentials/private values, and the static ledger has been inspected at
desktop and mobile sizes.

## Completed campaign

- Canonical run: `RUN-20260818T192408Z-3bd810db`.
- Local execution: 2026-08-19 00:54:08 to 01:08:37 IST.
- Results: 53 passed, 10 failed, 13 blocked, 1 pending.
- Evidence: 231 original PNG screenshots (27.1 MiB).
- Follow-up tasks: 24 total; 23 open and 1 accepted deferred.
- `--validate-only`: valid, zero issues.
- Dashboard behavior: failed-result filtering returned exactly 10 behavior
  cards and 10 graph nodes; graph-node selection opened the evidence record.
- Dashboard render inspection completed at 1440x1000 and 390x844; retained
  screenshots are ignored under `artifacts/2026-08-v0.2-behavior-audit/`.
