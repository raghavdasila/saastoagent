# Corpus Horizontal Plumbing and Behavior Audit

Date: 2026-08-09

Authority: `critical_prompt.md`, the owner-authored
`docs/corpus-agent-design/feature-behavior-notes.md`, current live source, the
compiled RouteDeck frontend contract, and the Studio-to-RouteDeck manifest.
The behavior-notes file was read only and was not modified.

## Executive verdict

The minimal Source-to-Operations product spine is now implemented as one
RouteDeck application. Surface-only has passed the full joined lifecycle, but
it is not yet valid to call the requested evidence complete: chat-only and
hybrid still need current full passes. The earlier joined 13/13 run remains
useful historical evidence but does not satisfy the new independent-mode
requirement and is no longer treated as completion.

The current work is horizontal completion, not another round of isolated
feature polishing. The three evidence modes must traverse the same real
Source, Agent, design, build, Sandbox, evaluation, hosted deployment, public
interaction, and Operations state. Credentials remain a masked private-surface
exception.

## Architecture plumbing

```text
ordinary owner intent or independent product surface
  -> current RouteDeck node and legal model context
  -> one typed operation chosen by the model or dispatched by the surface
  -> RouteDeck legality, review, transition, and projection
  -> Corpus-owned service, persistence, adapter, and product copy
  -> same conversation, selected Agent, exact Source revision, build, and deployment
```

Chat evidence is not allowed to contain a destination name, operation ID,
RouteDeck term, entity ID, or scripted multi-step instruction. Expected
operation IDs exist only in the post-hoc verifier. The verifier observes
RouteDeck's deterministic provider-safe tool name and durable tool-turn ID;
it does not constrain or invoke the model.

The same rule rejects conversational choreography. A user is not asked to
name or enter a feature, leave one screen, open another screen, and then name
the control to press. One ordinary goal may produce several legal RouteDeck
operations chosen by the model; those operations are correlated only after
the assistant turn has completed. Human review remains a separate natural
confirmation because the decision itself must not be inferred.

Representative chat-only proof boundaries:

| Ordinary user intent | Post-turn verifier expectation, never model input |
| --- | --- |
| Attach an API definition for the assistant being built | return/open the Source workspace, then inspect the uploaded API |
| Create a named taxonomy assistant from the prepared API | leave Source work, reach Agent creation, and create the Agent |
| Shape the assistant from the approved capabilities | reach Designer and append the proposal |
| Make the accepted design runnable | return to the Agent, reach Builds, and assemble exactly once |
| Try the runnable assistant privately with a taxonomy question | reach Sandbox and start one isolated run |
| Measure the successful trial for publishing | reach Evaluation, then create and run the exact case from ordinary follow-up intent |
| Make the assistant available at the chosen hosted address | reach Channels, create the channel, then stage review; acceptance remains a separate owner decision |
| Show how the published assistant was actually used | reach Operations and read the persisted owner-only records |

## Behavior-note matrix

| Area | Current horizontal plumbing | Chat / surface ownership | Remaining truth |
| --- | --- | --- | --- |
| Lounge | Real anonymous help/auth and owner registration | General help is chat-capable; credentials are private surfaces only | New horizontal recordings use surface registration because credentials are excluded from chat |
| Workspace | Real owner landing page and navigation spine | Ordinary intent can route to features; quick actions work independently | Broad workspace questions are implemented by the primary agent but are not part of the minimal lifecycle proof |
| Agents | Immutable versions, edit, archive/delete review, exact Source-revision attachment, selected-Agent hub | Typed operations are legal to chat; full independent controls exist | Current horizontal journey proves create + attach; edit/archive/delete remain separate depth evidence |
| Source Hub | Real YAML/Markdown intake, worker processing, persisted Source inventory | File-bearing ordinary chat and surface upload both enter the same Source state | Source deletion from the notes is not implemented |
| API Source | ToolRouter normalization, semantic graph, semantic groups, recorded node-by-node stage playback, protected profile, contract review, curation, planning, routed execution | Non-secret operations are chat-capable; credential material is surface-only | Progressive live construction is recorded-stage playback rather than a live worker stream |
| Selected Agent hub | One private Agent binding with Designer, Builds, Sandbox, Evaluation, Channels, and Operations destinations | Navigation-only tools and independent controls preserve the same binding | Implemented; current three-mode full proof pending |
| Designer | Source/curation-derived features, behaviors, policies, capabilities and tools; visible RouteDeck design topology; immutable approval and build request | Ordinary design intent and independent customize/review controls | Deeper planner/executor design remains outside the launch baseline |
| Builder | Exact accepted design/profile/curation bindings; isolated runtime assembly; visible compiled RouteDeck NavGraph | Chat and surface can assemble the same pending build | Stop, pause, delete, and explicit run lifecycle from the notes are not implemented; automatic evalset generation is not yet Builder-owned |
| Sandbox | Real isolated draft runtime, real safe API read, visible RouteDeck projection/NavGraph and ToolRouter clarification, same-run resume, safe event trace | Ordinary trial/clarification chat and independent form controls share one run | Implemented baseline; destructive sandbox actions remain outside the journey |
| Evaluation | Version-bound cases, category/difficulty, immutable run and deployment eligibility | Ordinary chat and list/form controls create and run the same case | ToolRouter evalset generation and full add/edit/remove CRUD are incomplete |
| Channels | Hosted Web channel identity and availability state | Ordinary intent and independent controls share the same selected Agent | Only hosted Web is in scope, matching the launch notes |
| Deployment | Eligible exact build, durable required review, accept-time recheck, restart-safe public URL and rollback operation | Chat can stage/resolve the review without IDs; surfaces independently stage/accept/reject | Deploy is in the journey; rollback needs separate depth evidence |
| Public agent | Real deployed runtime, conversation isolation, natural same-run clarification and supervised tool execution | End-user message is natural chat; public HTTP/UI expose no runtime surface IDs, operation candidates, RouteDeck, NavGraph, or ToolRouter internals | Owner-only runtime diagnostics remain visible in Sandbox and Operations and are retained in the internal development video |
| Operations | Owner-only public interaction records, result, API count, redacted decision events, promote-to-evaluation action | Ordinary intent and independent surface reach the same records | Baseline implemented; promotion is not required in every horizontal recording |

## Evidence truth as of this audit

- Surface-only run `20260808T230857Z-3d60c30abc` passed `21/21` across the
  full Source -> Agent -> Designer -> Builder -> Sandbox -> Evaluation ->
  Channels/Deployment -> public hosted interaction -> Operations lifecycle.
  It retains 12 screenshots and one uncut raw Playwright WebM at normal speed
  (`180.72s`, SHA-256
  `155c8150b213979d00a866c73edeb69593f1d0235a6994ae9dbe7c2dce71e2a9`).
  The recording is not post-processed. It remains valid product evidence, but
  it predates the strengthened readability gate below and will be re-recorded
  for the final evidence set.
- Current chat runs show a real ordinary file message creating a Source and
  autonomously choosing `workspace.open_sources` followed by
  `sources.inspect_current_api` in one assistant turn. Run
  `20260809T001914Z-8180a0f41e` proved those operations executed but exposed a
  recorder ordering bug: post-turn inspection ran before the streamed chat
  request began. Run `20260809T002246Z-9f9fc61a1c` closed that race and captured
  the exact durable events, then exposed a second recorder-only issue: the same
  execution appeared as a recent event, tool message, and invocation trace and
  was falsely counted three times. The durable recent-operation event is now
  authoritative, while the other two projections remain separate diagnostic
  evidence; the focused recorder gate is `19 passed`. A full chat pass is still
  pending. Navigation-sized prompt choreography has been removed:
  Agent creation, Designer proposal, build assembly, Sandbox start, and later
  area handoffs require the model to choose the necessary operation sequence
  from one ordinary goal.
- Surface run `20260808T213456Z-2adeda7146` passed Source processing, visible
  semantic graph, exact approved contract, protected profile, exhaustive
  curation, and exact Agent/Source attachment. It then exposed a real Designer
  context-provider defect: the provider called a method that does not exist on
  a runtime `OperationRequest`, so RouteDeck failed closed before staging
  review. The Corpus provider now reads the real immutable arguments object and
  has a focused runtime-request regression. A later `0/23` launch was rejected
  by the fixed-hour registration limiter and exercised no product feature.
- Surface run `20260808T221456Z-fe8f241483` proved the corrected Designer and
  concurrent Sandbox runtime through two real ToolRouter-routed Medusa reads,
  both HTTP 200, with a grounded response. It remained failed because the
  evidence script demanded a clarification even though the model had split the
  broad request into two calls. The Agent model contract now forwards one
  unresolved external intent to ToolRouter and splits only explicit multi-fact
  requests; a live model probe plus the persisted semantic graph produce a real
  `ASK_DISAMBIGUATE` without an operation name in the user prompt.
- Surface run `20260808T222806Z-4e926153e0` then visibly proved that natural
  request reaching the ToolRouter clarification subagent with zero API calls.
  Resume exposed a Corpus boundary defect: its private selected-operation marker
  entered RouteDeck's public tool arguments and was correctly rejected. Corpus
  now removes router-only coordination values before RouteDeck validation while
  retaining exact path/query/header/cookie/body inputs. Public clarification
  also resolves unique human choices such as `Use product types.` and presents
  natural option labels instead of internal operation IDs.
- Hybrid full evidence is pending. The fixed-hour registration limiter is
  treated as a hard launch gate rather than an expected or suppressed error.
- All retained videos are raw Playwright page recordings with playback rate
  1.0 and no post-processing. Failed runs remain failed artifacts.
- The final recorder now holds every captured proof state for 2.5 seconds
  before and after the screenshot while the raw 1x recording continues. This
  adds real reading time; it does not speed, slow, cut, or assemble footage.
  A 10-second contact-sheet audit of the earlier surface video confirmed why
  this was needed: Source and deployment states persisted across samples while
  several dense Designer/Builder/Sandbox states were too brief to appear in a
  coarse review even though their screenshots existed.

## Visual product audit of the passing surface run

The 12 retained screenshots were inspected as rendered product states, not
treated as proof by filename alone.

| State | Visible architecture/product truth | Visual verdict |
| --- | --- | --- |
| Source | Semantic graph visualization, semantic groups, exact processed revision, and recorded construction playback are visible | Functionally strong; dense but legible |
| Designer | RouteDeck-powered blueprint with features, behavior, policies, capabilities, tools, and topology is visible | Correctly exposes the design rather than a generic form; further interaction polish is depth work |
| Builder | Compiled NavGraph and exact immutable Source/design/runtime bindings are visible | Architecture is no longer hidden; layout remains utilitarian |
| Sandbox | Owner-only RouteDeck projection/NavGraph, ToolRouter clarification subagent, zero-call waiting state, resumed call, and safe trace are visible | Strongest downstream diagnostic surface |
| Evaluation | Exact build/case/run/eligibility state is visible | Complete baseline, sparse CRUD ergonomics |
| Deployment | Exact build/channel/review/public URL/availability state is visible | Functionally complete but visually sparse; it should not be described as polished |
| Public hosted Agent | Natural clarification and resolved answer are visible, while owner RouteDeck/NavGraph/ToolRouter internals are absent | Intentionally minimal public boundary, not evidence of missing owner diagnostics |
| Operations | Deployed interaction, response, call count, and redacted decision evidence are visible at desktop and 390x844 | Complete baseline; promotion depth remains optional to the horizontal proof |

## Horizontal blockers versus later depth

Horizontal completion blockers:

1. pass one uncut normal-speed chat-only journey with post-hoc exact tool proof;
2. re-record surface-only with the strengthened readable-state holds;
3. pass one uncut normal-speed hybrid journey with shared state and no repeats;
4. prove the corrected public-versus-owner diagnostics boundary without hiding
   the plumbing from internal evidence;
5. inspect every retained final screenshot/video and reconcile Studio, manifest,
   architecture, validation, and current-context truth.

Depth after horizontal completion:

- Source deletion;
- Builder start/stop/pause/delete lifecycle and automatic evalset generation;
- full Evaluation CRUD and ToolRouter evalset authoring;
- deployment rollback evidence;
- broader Workspace questions and non-baseline Agent lifecycle evidence.

## Current regression gate

After the Designer provider correction, Agent/ToolRouter delegation correction,
cross-thread RouteDeck store serialization, and anti-spoonfeeding recorder
changes, the repository gate is: backend `368 passed` with six existing
dependency deprecation warnings; frontend `24 files / 118 passed`; strict
typecheck and production build passed with the existing large-chunk warning;
the generated RouteDeck frontend contract is current; Studio parity and
architecture-boundary checks passed. These gates do not replace the still
pending three real browser journeys.

## RouteDeck change ledger

The authorized sibling change is separately recorded in
`audits/2026-08-08-routedeck-chat-review-resolution.md`. It added framework-owned
empty-input current-review accept/reject tools so natural chat can resolve a
durable review without receiving a review ID. Focused RouteDeck proof is 27
passed and the expanded affected suite is 255 passed.

The second authorized sibling change is recorded in
`audits/2026-08-09-routedeck-inspection-operation-history.md`. It adds a
bounded, authenticated, public-safe `recent_operations` collection to the
finite RouteDeck inspection snapshot so genuine multi-operation chat turns can
be verified without coupling Corpus to RouteDeck's private SQLite store. It
does not change model prompts, operation legality, reviews, navigation, or
product behavior. The combined current review-resolution plus finite-inspection
focus is `39 passed` with one existing Starlette/httpx deprecation warning.
