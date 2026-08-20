# Corpus Behavior-First Delivery Process

Status: controlling process for behavior-led product changes

This document defines how an intended Corpus behavior moves from owner intent
to accepted implementation. It is separate from the behavior evidence ledger:
the process governs product delivery, while the ledger records what the real
application visibly did.

## Truth Owners

| Concern | Owner |
| --- | --- |
| Product intent and launch baseline | User-owned `docs/corpus-agent-design/feature-behavior-notes.md` |
| Product interaction design | Accepted Design Studio state in `docs/corpus-agent-design/workbench/design-state.json` |
| Studio-to-runtime identifier mapping | `contracts/corpus-agent-design-routedeck-manifest.json` |
| Framework mechanics | Current RouteDeck contracts, read-only unless a named change is authorized |
| Product implementation | Corpus source in the owning feature/module |
| Observed behavior truth | `docs/corpus-behavior-evidence-ledger.md` and `audits/2026-08-v0.2-behavior-audit/` |
| Repeatable audit operation | `skills/audit-corpus-behaviors/SKILL.md` |
| Isolated and horizontal video evidence | Owning feature recorder or `scripts/run_horizontal_product_journey.py`, with claims recorded in the owning validation document |
| Architecture ownership | `architecture/code-map.md` and the relevant component document |
| Test meaning and commands | `test_index/README.md` |
| Current restart state | `context.md` and the latest checkpoint |

The Behavior Notes are read-only to implementation agents. They are never
rewritten to make an implementation appear correct. Studio owns product
meaning, not technical identifiers. The manifest maps accepted Studio meaning
to compiled contracts but is not a substitute for product design.

## Delivery Flow

```text
Owner behavior
  -> accepted Studio design
  -> RouteDeck mapping gate
  -> Corpus vertical implementation
  -> isolated real-product validation
  -> canonical ledger retest
  -> release-level horizontal acceptance
```

Tests protect the flow. Test counts do not replace it.

## Evidence Levels

Do not substitute one evidence level for another:

1. **Focused contract checks** protect deterministic invariants and important
   regressions. They do not prove the owner-visible feature.
2. **Isolated feature evidence** proves one behavior and its immediate
   handoffs through the real product, with a short mandatory video.
3. **Canonical behavior-ledger evidence** records the current Design Studio
   inventory through ordered tracked screenshots and linked tasks. Its current
   schema is screenshot-backed; video is complementary and remains under
   ignored `artifacts/`.
4. **Horizontal release evidence** proves the complete lifecycle independently
   through chat-only, surface-only, and hybrid runs with full uncut videos.

An isolated video cannot change a canonical ledger status. A ledger screenshot
cannot replace required isolated or horizontal video. A horizontal pass cannot
fill an unproven behavior that was not actually exercised in that run.

## Two Lanes That Must Not Be Mixed

### Audit lane

The audit lane observes the authoritative application as-is. Product source,
Studio behavior, RouteDeck, and the database are read-only during the audit.
The canonical recorder produces `ledger.json`, `tasks.json`, the dashboard,
and screenshot evidence under `audits/2026-08-v0.2-behavior-audit/`.

The canonical ledger auditor does not currently record or submit video into
the ledger. Its videos, when separately captured, are ignored development
artifacts and do not replace the required ordered PNG evidence.

Use `skills/audit-corpus-behaviors/SKILL.md` and
`docs/corpus-behavior-evidence-ledger.md` for the exact audit procedure. A
failed, blocked, or pending record remains evidence truth. Editing its task does
not create a pass.

### Product-fix lane

The product-fix lane starts from an evidence-backed ledger task or an explicit
owner request. It may change only the authorized Corpus owners needed to
deliver the behavior. It must not edit ledger results to match the fix.

After a fix, narrow runtime evidence may prove the implementation slice, but
the canonical ledger changes only after a fresh real-product observation under
the audit contract.

The current audit recorder has no selective behavior, feature, resume, or
from-depth filter. Do not manufacture an incremental ledger update. If a
selective retest is required, stop and obtain explicit authorization for that
recorder capability; otherwise follow the existing full-campaign contract.

## Step 1: Establish Authority And Scope

Before the first mutation:

1. Read `critical_prompt.md`, `context.md`, the latest checkpoint,
   `instructions.md`, `context_pipeline.md`, `architecture/code-map.md`, the
   relevant component document, and any active plan.
2. Read the relevant owner-authored Behavior Note, accepted Studio behavior,
   manifest mapping, current ledger record/task, Corpus implementation, and
   RouteDeck contract.
3. Record what visibly works, what is merely implemented, what is integrated,
   and what is absent, broken, confusing, or unproven.
4. Identify the owning architecture row and both neighboring feature handoffs.
5. Declare the mutation allowlist: exact files, modules, repositories,
   services, environments, and data identities that may change. Everything
   else is read-only.
6. State the owner-visible acceptance evidence and failure semantics required
   for completion.
7. State the exact runtime location, real integration identities, owner/data
   lineage, and smoke URLs. Local runtime is the default unless the owner
   explicitly requests another host.
8. Preserve all unrelated working changes. Git operations, including a
   baseline commit required by a later ledger rerun, need explicit owner
   authorization.

If the behavior cannot be delivered inside that boundary, stop before changing
an adjacent owner and request an explicit decision.

## Step 2: Define One Owner-Observable Behavior

Translate the intended behavior into:

- initiating owner intent or product event;
- visible intermediate, waiting, and review states;
- successful outcome;
- failure, retry, cancellation, and recovery semantics;
- exact conversation, Agent, Source/revision, design, build, evaluation,
  channel, deployment, public-session, and interaction lineage that must
  survive where applicable;
- incoming and outgoing handoffs;
- chat-only, surface-only, and hybrid expectations; and
- sensitive values that must remain surface-only.

For API processing, Builder, Evaluation, and Deployment, define durable
queued/running/succeeded-or-ready/failed state, leave-and-return continuity,
reload and backend/worker restart behavior, and explicit owner retry. Failure
must remain failure; no automatic retry or fallback may present success.

For hybrid work, define one continuing task. Switching between chat and a
surface must not create another entity, repeat an operation, retarget lineage,
or restart completed work.

Use ordinary product language. Do not put feature names, operation IDs,
RouteDeck nodes, routes, entity IDs, or recorder-oriented click instructions in
owner chat prompts.

### Integration And Dependency Gate

When the behavior adds or changes a third-party integration:

1. identify the exact official SDK, tool, sample, or verified reference;
2. run that reference end-to-end locally against the real target behavior
   before writing a custom adapter;
3. record the reference version, prerequisites, configuration, expected and
   actual result, evidence, license, and ownership boundary; and
4. stop if the reference cannot perform the required behavior—do not hide it
   behind a custom integration, mock, cached output, or alternate provider.

When adding or materially expanding an open-source dependency, evaluate at
least three viable maintained candidates when such a set exists, compare
license/security/activity/platform/footprint/upgrade cost, present the
recommendation, and obtain explicit approval before adding it. Pin and document
the approved version and run its official minimal reference first.

## Step 3: Correct Product Design First

If the intended behavior materially differs from Studio, correct and accept
Studio before implementing it. Studio may define:

- user stories and natural owner intent;
- policies and safety boundaries;
- operations and product consequences;
- suggested actions;
- surfaces and navigation;
- review and clarification behavior; and
- explicit scope and deferred behavior.

Studio must not prescribe backend classes, providers, guards, bindings,
storage, or RouteDeck identifiers. Those belong to mapping and implementation.

## Step 4: Pass The RouteDeck Mapping Gate

Write this mapping before implementation:

```text
Studio concept -> existing RouteDeck contract -> Corpus implementation owner
```

Separate ownership explicitly:

- RouteDeck owns legal topology, reviews, projection, session mechanics, and
  supervised operation execution.
- Corpus owns product meaning, persistence, identities, services, adapters,
  routes, copy, and rendered product surfaces.
- The manifest owns accepted Studio-to-compiled identifier mapping.

Inspect RouteDeck before declaring a primitive missing. If a genuine gap is
proven, stop and report the exact repository/files, insufficient contract,
smallest proposed change, compatibility impact, and validation. Only a named,
authorized RouteDeck change may proceed, and its purpose must be recorded.

## Step 5: Implement The Smallest Complete Vertical Slice

Carry the behavior through every required layer:

```text
persistence
  -> domain/service
  -> supervised operation and policy
  -> frontend authoritative state
  -> rendered surface
  -> chat interaction where permitted
  -> failure/recovery
  -> both neighboring handoffs
```

Reuse working modules through their real public contracts. Do not reconstruct
a working module inside a surface, adapter, neighboring feature, or recorder.
Never use fixtures, canned responses, heuristic stand-ins, cached success,
automatic retry, or silent fallback in a product path.

Prioritize the usable behavior over broad test expansion and non-blocking
polish. Fix an observed regression immediately only when it blocks the active
behavior, violates ownership, safety, or lineage, corrupts data, or makes
evidence untruthful. Record lesser regressions in the evidence-backed task.

### One-Hour Delivery Clock

Each feature-delivery phase is one owner-visible product deliverable with a
hard 60-minute limit from authority read to written handoff:

- **0–10 minutes:** confirm Behavior Note, Studio, manifest, RouteDeck, Corpus,
  retained prerequisite, mutation allowlist, and exact deliverable;
- **10–35 minutes:** implement only the missing complete product slice;
- **35–50 minutes:** exercise the touched module at its current node through
  ordinary chat, direct surface controls, and one hybrid continuation;
- **50–55 minutes:** capture the mandatory short normal-speed maximized video,
  screenshots, exact lineage, and diagnostics; and
- **55–60 minutes:** stop all phase activity and record accepted or failed. No
  retry starts inside the same phase.

Reuse an exact retained prerequisite when it remains current. Do not start at
Lounge, register another owner, replay earlier accepted features, reprocess a
Source, or launch the complete horizontal recorder merely to prove the current
module. If the prerequisite is unavailable or stale, fail the phase with that
blocker instead of rebuilding the product journey. An offline milestone
verifier may validate an immutable retained artifact, but cannot replace a
missing real interaction mode or required video.

## Step 6: Validate The Feature In Isolation

Exercise the real product before broad testing:

1. real persistence and integrations;
2. owner-visible desktop interaction;
3. maximized split layout for work-heavy surfaces;
4. representative mobile interaction;
5. material failure, waiting, review, retry, and recovery states; and
6. focused tests for contracts actually at risk.

Every material non-sensitive behavior requires independent evidence for:

- **Chat-only:** the configured real model receives ordinary owner language and
  completes the behavior through legal operations. Expected operation IDs may
  be assertions but never prompt instructions.
- **Surface-only:** direct declared controls complete the behavior without chat
  assistance.
- **Hybrid:** chat and surfaces alternate while retaining the same task,
  identities, authoritative state, and operation chronology without replaying
  completed work.

Passwords, credentials, and similarly sensitive values remain surface-only.

An isolated evidence campaign has a **fifteen-minute hard wall-clock limit** and
one reviewed attempt. No automatic retry is permitted. On failure, stop,
finalize and retain the artifact, diagnose offline, and return to the owning
feature instead of replaying the complete product.

Every delivered feature requires a short, readable **normal-speed video** from
the first meaningful owner action through the terminal visible result. The
video contract is:

- 1.0x playback with no accelerated, omitted, or rewritten portions;
- include waiting, review, recovery, awkward, slow, and failing portions that
  occurred inside the attempt;
- finalize and retain the video even when the attempt fails;
- preserve the full raw recording; an excerpt must be labelled as extracted
  and link to the immutable raw recording;
- maximize a work-heavy surface before its first meaningful action; on wide
  screens chat remains readable on the left and the complete active surface on
  the right;
- prove independently usable 390x844 behavior for each responsive-risk
  surface;
- never visibly expose passwords, credentials, tokens, private mail values,
  one-time links, headers, cookies, query strings, or private payloads; and
- retain exact run/result identity, video path, duration, byte count, SHA-256,
  viewport, screenshots, safe-trace identity, and unexpected diagnostic
  counts.

The completion response must provide a directly playable local video link, not
merely say that video was recorded. If video is missing, unreadable, sped up,
cut at a load-bearing point, unfinalized after failure, or not linked in the
report, the behavior remains implemented-but-unproven.

The video is product-development evidence, not a tracked ledger replacement.
Store raw video below ignored `artifacts/`; record its path, hash, duration,
bytes, claim boundary, and relationship to the result JSON in the owning
tracked validation document.

## Step 7: Retest Through The Behavior Ledger

Use the task and its linked record as the retest contract:

- preserve the original expected and observed behavior;
- retain the exact feature, prerequisite graph, mode, and evidence lineage;
- change task workflow state without changing prior evidence truth;
- rerun only through capabilities supported by the canonical recorder;
- require a fresh visible product observation before recording `passed`;
- retain ordered screenshots, hashes, classified diagnostics, and attempt
  history; and
- keep every failed, blocked, or pending result linked to a task.

Before a canonical rerun:

- require the prior validated audit baseline to be committed; because Git is
  never implicit, obtain explicit owner authorization before that commit;
- require the exact ordered Design Studio behavior IDs and source SHA-256 to
  match the ledger, otherwise stop and define a new campaign boundary;
- use one disposable owner and state created only through real Corpus UI/API
  paths—never direct database mutation, fixtures, mocks, synthetic state,
  cached success, or fallback services;
- keep credentials and private values out of tracked text and screenshots;
- continue independent graph branches after failure and block only genuine
  descendants; and
- run `--validate-only`, inspect the regenerated diff, and inspect the dashboard
  at desktop and mobile sizes before accepting the audit package.

Keep result and task workflow semantics separate. Ledger results are `passed`,
`failed`, `blocked`, `pending`, or `not_applicable`. Task workflow may move
through `open`, `in_progress`, `fixed_unverified`, `retested_passed`, or
`accepted_deferred`; changing task workflow never changes observed result
truth.

The ledger result semantics remain owned by
`docs/corpus-behavior-evidence-ledger.md`. This process must not introduce a
second ledger schema, dashboard, runner, or status vocabulary.

## Step 8: Run Horizontal Acceptance Only At The Gate

Do not use a complete product journey to debug an isolated feature. A
release-level horizontal run is permitted only after every blocking behavior
record for that slice has fresh accepted evidence.

At that gate:

1. run broad backend, frontend, Studio, generated-contract, manifest parity,
   architecture, documentation, migration, and runtime-health gates once;
2. run exactly one current ordinary-chat-only journey, one surface-only
   journey, and one hybrid journey, each from an independent owner/conversation
   lineage;
3. use the current reviewed recorder or recorder set named in
   `test_index/README.md`; never assume
   `scripts/run_horizontal_product_journey.py` still owns product stages that
   a newer accepted architecture has superseded;
4. retain one continuous, uncut, 1.0x Playwright video from run start through
   terminal result for each mode, including failures and slow/awkward portions;
5. retain synchronized result JSON, video path/duration/bytes/SHA-256,
   screenshots, safe trace, exact entity lineage, responsive evidence, and
   unexpected diagnostic counts;
6. provide playable local video links for all three modes in the completion
   report; and
7. if a journey fails, preserve it as failed and return only to the owning
   behavior/task—never loop the complete journey as a debugger.

Chat requests must remain ordinary owner language without Corpus/RouteDeck
operation IDs, routes, nodes, hidden entity IDs, UI instructions, or a
recorder-scripted sequence. Credentials remain surface-only. Hybrid evidence
must retain exact versioned chat-operation provenance and direct surface
actions in one continuing conversation without duplicating an owner request.

## Step 9: Close And Reconcile Truth Owners

After acceptance, update only the owners whose meaning changed:

- accepted Studio state;
- Studio-to-implementation manifest;
- Corpus implementation and generated contract;
- authorized RouteDeck change report;
- code map and component documents;
- system-flow and test indexes;
- behavior ledger/task/dashboard through the canonical audit workflow;
- validation log and evidence hashes; and
- checkpoint and concise `context.md` restart state.

Record every authorized RouteDeck change with its exact purpose, repository
files, compatibility impact, and validation. Record every observed regression
with owning behavior, severity, evidence, and whether it blocked delivery.

Run broad gates only once after the usable feature rows are accepted. Do not
turn repeated broad suites into the deliverable. Perform Git operations only
when explicitly authorized, and stage only the approved file set while
preserving unrelated working changes.

Keep detailed contracts in their primary owners. `context.md` links to current
truth; it does not become the process, architecture, or evidence ledger.

## Replan And Stop Conditions

Stop before mutation and request an explicit decision when:

- the root cause belongs to a different owner than the authorized feature;
- the required fix changes a previously working or accepted subsystem;
- implementation requires a different architecture, persistence, identity,
  runtime, deployment, integration, or evidence strategy;
- a prerequisite requires modifying an adjacent repository or module;
- accepted evidence would use a different owner, database, environment,
  repository, runtime, or state lineage;
- the original acceptance test cannot be met inside the approved plan;
- significant work or evidence would need to be discarded, reset,
  regenerated, or re-baselined;
- the Design Studio inventory or canonical ledger source hash changed before a
  retest; or
- continuing would reinterpret the owner request merely to keep work moving.

Report the evidence creating the conflict, the additional boundary involved,
the smallest available options, and their consequences. Wait for the owner's
choice; urgency or prior permission does not expand the boundary.

## Completion Standard

A behavior is complete only when its current product path works, required
interaction modes are freshly observed, handoffs and lineage are preserved,
failure semantics are truthful, the canonical ledger record is current, and
all authority owners agree. Its development completion report must include the
mandatory playable normal-speed video and exact evidence identity.

A compiled surface, CRUD endpoint, passing test count, edited task, isolated
mock, or historical horizontal journey is not completion by itself.

## Anti-Drift Rules

- Behavior Notes remain the owner authority and are never rewritten by an
  implementation agent.
- Studio is corrected before materially different product behavior is coded.
- RouteDeck is inspected before a framework gap is claimed.
- Audit collection and product mutation never occur in the same campaign.
- Product semantics are not moved into recorder prompts or tests.
- Natural chat is not spoonfed with internal names or microscopic steps.
- A working feature is not reconstructed inside an integration layer.
- Isolated feature evidence precedes horizontal evidence.
- Mandatory video is delivered, playable, normal-speed, and tied to exact
  result identity; a filename or claim without the linked artifact is not
  evidence.
- Failures remain failed; no assertion weakening or fallback makes them pass.
- The canonical behavior ledger is observed truth, not a mutable progress
  narrative or implementation plan.
