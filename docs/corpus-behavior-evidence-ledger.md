# Corpus Behavior Evidence Ledger

This document owns the repeatable process for recording what the authoritative
Corpus application actually does, with ordered screenshots as the proof record.
It describes the current recorder and ledger contract; it is not a product
specification and does not turn an audit into permission to fix product behavior.

## Canonical owners

| Concern | Owner |
| --- | --- |
| Behavior inventory | `docs/corpus-agent-design/workbench/design-state.json` |
| Direct Playwright recorder | `scripts/record_v02_behavior_audit.py` |
| Campaign plan and completed-run facts | `plans/2026-08-18-v02-behavior-evidence-audit.md` |
| Tracked ledger, tasks, dashboard, and PNG evidence | `audits/2026-08-v0.2-behavior-audit/` |
| Reusable operator procedure | `skills/audit-corpus-behaviors/SKILL.md` |
| Raw videos, traces, profiles, and render checks | ignored `artifacts/` |

The first canonical baseline is run
`RUN-20260818T192408Z-3bd810db`: 77 behaviors, 53 passed, 10 failed,
13 blocked, 1 pending, 231 screenshots, and 24 linked tasks.

## Audit boundary

- Run the authoritative local Corpus application as-is. Do not modify product
  behavior while collecting a campaign.
- Treat Design Studio state as the inventory authority and the current Corpus UI
  as the observed truth. A designed behavior is not a runtime pass.
- Use one newly registered disposable audit owner, one persistent browser
  profile, and state created only through real Corpus UI/API paths.
- Do not mutate the database directly or substitute fixtures, mock providers,
  cached output, synthetic data, or fallback services.
- Require the configured model, worker, Medusa 2.13.6, Corpus mail path, and
  Mail.tm where the behavior depends on them. Record an honest failure or block
  when a dependency is unavailable.
- Continue independent branches after a failure. Block only genuine
  descendants whose prerequisite state was not created.
- Keep credentials, cookies, authorization headers, private email addresses,
  one-time links, and private payloads out of tracked text and screenshots.

## Evidence layout

The tracked package is:

```text
audits/2026-08-v0.2-behavior-audit/
|-- index.html
|-- ledger.json
|-- tasks.json
`-- evidence/<behavior-id>/<mode>/*.png
```

`ledger.json` records the source hash, runtime identity, graph edges, dependency
checks, run identity, and one current record per behavior. A behavior record
contains the Design Studio intent and assertions, BFS depth, prerequisites,
surface and operation identities, mode, result, observation, ordered screenshot
paths and SHA-256 hashes, classified diagnostics, attempts, and an optional task
link.

`tasks.json` is derived from failed, blocked, and pending behavior records. Each
task retains severity, category, reproduction, expected and observed results,
evidence and hashes, owning feature, run history, and workflow status.

The graph uses four edge types:

- `navigation`: reachable through product navigation at the same breadth;
- `prerequisite`: a shallower behavior creates required state;
- `continuation`: the behavior continues an earlier chat or product task;
- `state-dependency`: required state comes from another point in the graph.

## Result semantics

- `passed`: the expected behavior was visibly observed through the real path.
- `failed`: the behavior ran and contradicted the expectation.
- `blocked`: a real dependency or prerequisite prevented execution.
- `pending`: the capability was visibly unavailable or unimplemented.
- `not_applicable`: the mode is prohibited by the behavior contract.

Never convert evidence to `passed` by editing a task. A pass requires a fresh
successful product observation. Every failed, blocked, or pending result must
have a linked task.

## Screenshot and diagnostic contract

For each applicable behavior, retain the meaningful sequence: starting state,
action, review or pending state when present, result, and resulting navigation
or state. Every classified result requires at least two screenshots. Capture
desktop evidence for every behavior and 390x844 evidence for each distinct
responsive-risk surface.

The recorder stores original PNG files and hashes each retained path. It hides
input and textarea text during capture, replaces known private values in page
text, and strips query strings and fragments from recorded runtime URLs.
Diagnostics are classified as `console`, `http`, `page`, `request`, or
`worker`; do not leave unexplained diagnostics outside those categories.

## Local runbook

Run from the repository root. Start the existing local services without an
alternate Compose project:

```powershell
docker compose --env-file .env.local up -d backend source-worker frontend
pnpm --dir docs/corpus-agent-design/workbench dev --host 0.0.0.0 --port 8782 --strictPort
```

The smoke-test URLs are:

- Corpus: `http://127.0.0.1:5199/`
- backend: `http://127.0.0.1:8099/`
- Design Studio: `http://127.0.0.1:8782/`
- Medusa: `http://127.0.0.1:9100/`

Inspect or create the frozen inventory without exercising the application:

```powershell
.\.venv\Scripts\python.exe scripts\record_v02_behavior_audit.py --freeze-only
```

Run the complete headless campaign, or use `--headed` when an operator needs to
watch it:

```powershell
.\.venv\Scripts\python.exe scripts\record_v02_behavior_audit.py
.\.venv\Scripts\python.exe scripts\record_v02_behavior_audit.py --headed
```

`--stop-after-depth N` is a calibration control. A stopped run classifies
unreached behaviors and is not a completed canonical campaign.

Validate the inventory, graph, task links, evidence existence and hashes,
statuses, diagnostics, and tracked-text secret patterns without exercising the
application again:

```powershell
.\.venv\Scripts\python.exe scripts\record_v02_behavior_audit.py --validate-only
```

Validation regenerates `ledger.json`, `tasks.json`, and `index.html` and updates
their timestamps. Run it before reviewing or staging the final diff.

## First run and incremental follow-up

The first run creates the ledger from the exact Design Studio inventory and
freezes its SHA-256. A later run loads that ledger only when the ordered behavior
IDs and source hash still match. If the Studio inventory changed, stop: updating
the recorder and defining the new campaign boundary is separate work.

The current recorder supports history in-place, not selective execution. A full
rerun appends attempt metadata and replaces each behavior's current result.
Screenshot sequence numbers restart on each process run, so re-executed stable
paths are overwritten; committed Git history is the durable prior-image
baseline. Commit a validated baseline before rerunning and then review the exact
ledger, task, dashboard, and PNG diff.

The current CLI does **not** implement `--resume`, `--behavior`, `--feature`, or
`--from-depth`. Do not claim or emulate those filters by manually changing
evidence. Adding selective, run-addressed evidence retention requires an
explicit recorder change and its own acceptance work.

Task workflow changes (`open`, `in_progress`, `fixed_unverified`,
`retested_passed`, or `accepted_deferred`) do not alter behavior truth. After a
product fix, rerun the real path, validate, inspect the dashboard at desktop and
mobile sizes, and commit only the changed tracked audit package. Keep raw
`artifacts/` ignored.

## Completion gate

A canonical campaign is complete only when:

1. all frozen behaviors are represented exactly once and the BFS graph is
   reachable;
2. every behavior is executed or honestly classified in its applicable mode;
3. every result has the required ordered screenshot proof and valid hashes;
4. all diagnostics are classified and every non-pass links to a task;
5. tracked outputs pass the credential/private-value scan;
6. the dashboard is inspected at desktop and mobile sizes; and
7. `--validate-only` reports `"valid": true` with no issues.
