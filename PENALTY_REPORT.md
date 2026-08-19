# PENALTY REPORT: Corpus v0.2 Behavior Evidence Campaign

Date: 2026-08-18

Status: Failed and removed

## Purpose of this report

This report records the requirements that were accepted, the approach that was
taken, what was actually delivered, why it failed, and what was removed. It is
not an audit result and must not be used as evidence that Corpus v0.2 behavior
was exhaustively tested.

## Original requirements

The user first defined the required audit outcome as follows:

> I think what we needed is tested behaviour log. each and every behaviour,
> including you mentioned above, using screenshots as proof for record. perhaps
> we can use some html file to do it, we can then use it to keep track of tasks
> later. corpus is running locally, local test is enough. but we need to do this
> efficiently. using a BFS approach, as in we start with lounge, test and log all
> features accessible from there, then go deeper, say listing agent or resetting
> password and so on, it becomes a tree/graph of behaviours, we document this
> tree too.

The user then added:

> no TDD in implementing this plan btw.

The approved implementation plan was:

### Corpus v0.2 Exhaustive Behavior Evidence Campaign

#### Summary

Implement this feature-first, without TDD. Build the behavior inventory,
runner, evidence capture, BFS graph, and HTML dashboard first; validate the
completed workflow afterward.

Audit all 76 Design Studio behaviors locally in breadth-first order from Lounge
through Operations. Preserve screenshot sequences, results, graph
relationships, diagnostics, and follow-up tasks.

Tracked output:

- `audits/2026-08-v0.2-behavior-campaign/index.html`
- `ledger.json`
- `tasks.json`
- `evidence/<behavior>/<mode>/*.png`

Videos, verbose traces, and raw run artifacts remain ignored under
`artifacts/`. No Git operations are included.

#### Implementation

- Generate the canonical inventory from `design-state.json`; every Studio
  behavior must appear exactly once.
- Model edges as `navigation`, `prerequisite`, `continuation`, or
  `state-dependency`.
- Execute by BFS depth:
  1. Lounge and product help.
  2. Registration, sign-in, recovery, and verification.
  3. Workspace.
  4. Agents and Source Hub.
  5. API Source.
  6. Agent Designer.
  7. Builder and Sandbox.
  8. Evaluation.
  9. Channels, Deployment, and public Agent.
  10. Operations.
- Reuse pinned Cytoscape `3.33.1` to calculate a static breadth-first SVG
  layout. Do not add or upgrade dependencies.
- Build a filterable HTML dashboard by feature, depth, mode, and result. A
  selected node shows prerequisites, assertions, screenshot sequence,
  diagnostics, and linked tasks.
- Support runner filters and resumability: `--resume`, `--behavior`,
  `--feature`, and `--from-depth`.
- Reuse existing browser, journey, review, diagnostics, restart, and evidence
  helpers rather than creating another automation stack.

#### Execution rules

- Use one newly registered audit owner and only state created through real
  Corpus UI/API paths. Do not directly mutate the database.
- Use disposable records for archive, delete, rollback, and other destructive
  branches.
- Use the actual configured model, worker, local Medusa 2.13.6, Gmail SMTP, and
  Mail.tm. Fail explicitly if any dependency is unavailable.
- Keep passwords, tokens, email links, credentials, cookies, headers, and
  private values out of screenshots and artifacts.
- Continue independent branches after failure; mark only dependent descendants
  blocked.
- Test modes according to contract:
  - surface and chat separately where both apply;
  - credentials through surfaces only;
  - hybrid for continuation and shared-state behavior;
  - `not_applicable` with an explicit reason where a mode is prohibited.
- Capture the full meaningful interaction sequence: starting state, action,
  pending/review state, result, and resulting navigation/state.
- Retain original full-resolution PNGs without resizing or recompression.
- Capture desktop evidence for every behavior and mobile evidence for each
  distinct interactive or responsive-risk surface.
- Unimplemented behavior must show honest unavailable/deferred behavior and
  remain `pending`; absence is not a pass.

#### Ledger and task contracts

Each behavior records:

- stable ID, feature, title, and expected behavior;
- BFS depth, graph edges, prerequisites, and resulting state;
- applicable modes and independent mode results;
- assertions and observed outcome;
- safe RouteDeck node, surface, operation, review, and entity identities;
- screenshot paths and SHA-256 hashes;
- console, HTTP, page, request, and worker diagnostics;
- blocker, run ID, timestamps, runtime URLs, and linked task IDs.

Statuses are `passed`, `failed`, `blocked`, `pending`, or `not_applicable`.
Aggregate status must never conceal a failed mode.

Each task records severity, category, reproduction, expected result, evidence,
owner subsystem, run history, and status: `open`, `in_progress`,
`fixed_unverified`, `retested_passed`, or `accepted_deferred`.

Task edits cannot convert behavior evidence to passed; only a successful fresh
rerun can.

#### Post-implementation verification

- Run the inventory and confirm all 76 behaviors are represented with no
  unknown entries.
- Validate graph references, deterministic BFS depths, reachability, and
  explicit blocked nodes.
- Validate ledger/task schemas, evidence paths, hashes, statuses, and blocker
  reasons.
- Reject any passed behavior without its required screenshot sequence.
- Scan artifacts for secrets, credentials, tokens, email links, headers,
  cookies, and private payloads.
- Run the actual local campaign and confirm page identity, meaningful
  rendering, RouteDeck state, persistence, reviews, explicit failures, and
  diagnostics.
- Verify async leave-and-return behavior, restart recovery, surface/chat
  continuity, credential privacy, and public/owner diagnostic separation.
- Render and inspect the dashboard at desktop and mobile sizes.
- Record every failed or pending behavior as a linked task.

Acceptance requires all 76 behaviors to be represented, every applicable mode
executed or explicitly blocked/pending, every result screenshot-backed, no
unclassified diagnostics, and every failure linked to a task.

#### Assumptions

- No TDD: implementation precedes focused automated and runtime verification.
- AutomationBench remains excluded and is recorded only as a separate deferred
  validation goal.
- Custom domains and other deliberately deferred capabilities are tested only
  for honest unavailable/deferred presentation.
- This campaign records findings; it does not fix product behavior during the
  audit run.
- Corpus remains on `5199`/`8099`, Design Studio on `8782`, and local Medusa on
  `9100`.

## Planning approach actually taken

The implementation was approached as an automation-framework project before it
was treated as an evidence-execution project:

1. Parse `design-state.json` into a canonical behavior inventory.
2. Define ledger, task, graph-edge, mode, diagnostic, screenshot, and hashing
   schemas.
3. Compute BFS depth and a static Cytoscape layout.
4. Generate a filterable HTML dashboard.
5. Add CLI filtering and resumability.
6. Map existing journey helpers into behavior handlers.
7. Modify existing helpers to support shared credentials, additional
   screenshots, mobile rendering, and continuation through later features.
8. Run partial journeys and repair the framework when failures were encountered.
9. Attempt to restart the campaign under a single canonical owner after earlier
   runs were found invalid.

This sequence matched the plan's statement that the inventory, runner, graph,
and dashboard should be built first, but it failed to preserve the plan's main
delivery priority: executing and logging every behavior.

## What was initially delivered

After approximately 1 hour and 11 minutes, the reported output consisted of:

- an HTML dashboard;
- `ledger.json` and `tasks.json`;
- an inventory and BFS executor;
- resume and filter support;
- screenshot/evidence storage and hashing;
- a small partial local run.

The retained status at that point was 77 behaviors in the current Studio state,
not the planned 76, with 71 behaviors still pending. Calling the campaign
"implemented" at this point was incorrect. Only the campaign framework was
implemented.

## What happened afterward

Further work expanded and repaired automation for Source Hub, API Source,
Agents, Agent Designer, Builder, Sandbox, Evaluation, Deployment, public Agent,
and Operations. Several deeper product journeys were run and screenshots were
captured.

Those runs observed issues such as Source creation returning HTTP 503,
Builder remaining at an automatic-generation waiting state, Sandbox not
reaching success within its timeout, and verification/reset mail requests
failing. However, the deeper journeys used different owners and isolated state
lineages. They violated the explicit single-owner campaign requirement and
could not be accepted as definitive campaign evidence.

The invalid deeper runs were rejected, a clean Compose project and Mail.tm
owner were created, and the canonical ledger was reset. Lounge and part of the
authentication/recovery depth were rerun. The resulting definitive ledger was
only:

- 77 behaviors represented;
- 3 passed;
- 2 failed;
- 2 blocked;
- 70 pending.

Resetting the canonical ledger made the campaign appear to have returned to
Lounge because, in accepted-evidence terms, it had.

## Failures

### 1. The deliverable was confused with its supporting framework

The required deliverable was an exhaustive screenshot-backed behavior log. The
framework was only a means to produce it. Reporting the framework as campaign
implementation was a false completion boundary.

### 2. The single-owner rule was violated

Existing journey helpers created their own users and isolated runtimes. They
were modified incrementally rather than being placed behind a campaign-level
identity guard before any definitive run began. Deeper evidence therefore came
from incompatible state lineages.

### 3. BFS execution was not maintained

Instead of recording a failure, blocking only dependent descendants, and
continuing independent branches, work repeatedly returned to runner repair and
campaign resets. The requested breadth-first audit did not progress through all
ten depths.

### 4. Automation work displaced product testing

Time was spent modifying generic journey infrastructure, adding modes and
screenshots, handling uniqueness assumptions, and repairing aggregation logic.
Those changes did not compensate for the missing behavior-by-behavior runtime
execution.

### 5. Invalid evidence was retained too long

Screenshots existed, but accepted evidence was not cryptographically and
structurally bound to a canonical owner, Compose project, database lineage, and
run identity at capture time. Raw screenshots were therefore mistaken for
campaign progress until the identity problem was recognized.

### 6. Premature status reporting

Status reports emphasized scripts, screenshot counts, and framework capability
instead of leading with the only meaningful acceptance count: how many
behaviors had actually been executed under the valid campaign identity.

### 7. The inventory discrepancy was not resolved before execution

The plan stated 76 behaviors while the current Design Studio state contained
77. The correct response was to record the discrepancy, audit all 77, and make
77 the run's frozen inventory before executing any behavior.

## Planning gaps that should have been closed before execution

The outcome and acceptance criteria were clear, but the executable plan lacked
hard controls that would have prevented invalid progress:

- A canonical campaign identity file containing the Compose project, owner
  identity hash, database lineage, runtime URLs, and run ID.
- A pre-capture guard that aborts if any runner uses another owner, stack,
  database, or lineage.
- An explicit prohibition on helper-managed account registration or isolated
  runtime creation during the canonical campaign.
- A preflight proving that every frozen behavior and applicable mode has an
  executable handler before the campaign begins.
- Separate lifecycle states for "framework ready" and "campaign executed."
- Per-depth completion gates.
- One acceptance command that fails while any applicable mode lacks valid
  evidence, diagnostics, blocker classification, or a linked task.
- Immutable run history instead of resetting/replacing the canonical ledger.
- A distinction between raw screenshots and evidence accepted under the
  canonical campaign identity.
- Durable checkpointing of the owner session and every created entity identity.
- A rule to perform an in-scope behavior manually through the real UI when its
  automation adapter fails, while recording the adapter failure separately.
- A frozen resolution of the 76-versus-77 discrepancy before runtime execution.

These gaps should have been added during planning. Their absence did not excuse
violating the requirements that were already explicit.

## Cleanup performed

The failed campaign implementation and output were removed on 2026-08-18:

- campaign-specific runner, executor, layout, auth recorder, and test files;
- the root `package-lock.json` created while preparing the layout runner;
- `audits/2026-08-v0.2-behavior-campaign/` and its dashboard, ledgers, tasks,
  and evidence;
- campaign-only raw artifacts and `.runtime` evidence/state directories;
- seven `corpus-audit-v02*` Compose projects;
- seven campaign runtime volumes, including their audit databases;
- 21 campaign-tagged Docker images.

Pre-existing Corpus journey and evaluation helpers that had been modified for
the campaign were restored byte-for-byte from the checkout's recorded baseline
commit `4f5e2b8f090d65f379e100afdf55b785384c0e02`. No Git command was used.

The authoritative Design Studio state, Corpus product code, sibling RouteDeck
checkout, and unrelated pre-existing artifacts were not deleted.

## Final assessment

The campaign failed its acceptance criteria. It did not test and log every
behavior, did not preserve one valid owner lineage throughout, and did not
deliver an exhaustive screenshot-backed BFS record. The removed dashboard and
ledger must not be treated as v0.2 validation evidence.
