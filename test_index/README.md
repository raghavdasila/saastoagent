# Corpus Validation Index

## Executable Suite Index

| Suite | Command | Protects | Claim boundary |
| --- | --- | --- | --- |
| Backend framework/product suite | `.\.venv\Scripts\python.exe -m pytest backend\tests -q` | 532 tests including universal feature-boundary adapters, application-owned worker registration, generic reviewed API revision identity, explicit Medusa acceptance, the Source-to-Operations horizontal lifecycle, exact Designer-to-Builder topology, neutral Builder/Sandbox/Evaluation/Delivery adapters, Agent lineage/lifecycle, reviewed deployment and channel availability, plus the prior Source/API execution contracts | Uses isolated persistence; live visual/runtime paths are proven separately. |
| Frontend component suite | `pnpm --dir frontend test` | 188 tests including chat focus/scroll, responsive dock/maximize shell, authenticated Lounge/history, Agent lifecycle, selected-Agent hub, semantic graph, Designer topology, immutable build and deployed NavGraphs, Sandbox clarification, Evaluation, Channels/deployment reviews, public delivery boundary, Operations, and Source/API surfaces | jsdom component/contract coverage, not rendered browser proof |
| Designer/Builder topology correspondence | `.\.venv\Scripts\python.exe -m pytest backend\tests\designer backend\tests\builder\test_agent_navgraph.py -q`; `pnpm --dir frontend test -- designer-surfaces.test.tsx build-navgraph.test.tsx` | One immutable Designer topology and stable hash, exhaustive capability/tool membership, fail-closed invalid customization, exact capability correspondence in the compiled per-build RouteDeck Application, and visible matching Designer/Builder topology identity | Focused contracts protect correspondence; current surface/chat/hybrid ecommerce journeys visibly prove the generated topology and immutable compiled NavGraph across interaction modes. |
| Owner-described Designer generation milestone | `.\.venv\Scripts\python.exe -m pytest backend\tests\designer backend\tests\agents -q`; `pnpm --dir frontend test -- designer-surfaces.test.tsx`; `.\.venv\Scripts\python.exe scripts\run_horizontal_product_journey.py --mode surface --stop-after designer` | Configured real-model generation from ordinary owner language, exact selected-Agent/Source/semantic-group/curation grounding, immutable Revision 2, owner customization Revision 3, exhaustive curated-tool repartition, review/build separation, generated NavGraph selection, desktop maximized and mobile rendering | Bounded run `20260811T171207Z-98270a1d7f` remains the short feature film. Current full surface `20260812T183856Z-02c48c5a50`, hybrid `20260812T221223Z-0e9ec6eb55`, and chat `20260812T222652Z-403a886798` runs prove the same Designer boundary in all three modes. |
| Durable asynchronous Builder milestone | `.\.venv\Scripts\python.exe -m pytest backend\tests\builder backend\tests\persistence -q`; `pnpm --dir frontend test -- builder-runtime-lifecycle.test.tsx build-navgraph.test.tsx`; `.\.venv\Scripts\python.exe scripts\run_horizontal_product_journey.py --mode surface --stop-after builder` | One persisted queued attempt and opaque job, source-worker-only running/completion, exact accepted-design recheck, explicit retained failure retry, immutable build/NavGraph, and automatic exact-build evaluation scheduling with leave-and-return UI refresh | Local bounded run `20260811T163659Z-73c50607a2` passed 15/15 with a 13.84-second normal-speed maximized Builder film and zero unexpected diagnostics. It intentionally stops before Sandbox/Evaluation and is not a full horizontal claim. |
| Horizontal ecommerce lifecycle by interaction mode | Local: `.\.venv\Scripts\python.exe scripts\run_horizontal_product_journey.py --url http://127.0.0.1:5199 --backend-url http://127.0.0.1:8099 --mode <surface\|chat\|hybrid>`. GCP: add `--url https://corpus.saastoagent.com --backend-url https://corpus.saastoagent.com --runtime-mode gcp-production --medusa-env .runtime/deployed-e2e/medusa.env --medusa-base-url http://10.138.0.2:9100 --gcp-project saastoagent --corpus-vm corpus-vm-1 --corpus-zone asia-south1-a --medusa-vm medusa-test-vm-1 --medusa-zone us-west1-a`. | Independent direct-surface, ordinary owner-chat, and mixed continuation paths across staged file intake, explicit Source analysis/semantic graph, reviewed effective API definition, exact shopping curation, Agent attachment, Designer topology/review, asynchronous immutable build NavGraph plus automatic coverage, real Sandbox product search, Evaluation eligibility, reviewed hosted releases/rollback/pause/resume, backend/worker restart, public product search, separate reviewed cart creation/add-to-cart, owner Operations evidence/promotion, and 390x844 rendering. Chat requests state the intended product actions explicitly but never contain operation IDs; exact persisted operation sequences remain mandatory. Assistant-response parsing excludes presentation headers before interpreting clarification questions. | Deployed post-ADR-005 runs: Surface `20260815T113953Z-89bb70e514` passed 39/39; Hybrid `20260815T102407Z-828e3735c3` passed 40/40; Chat `20260815T115153Z-5847710253` passed 39/39. All used independent lineages, the same real Medusa Source hash, continuous videos, and zero unexpected diagnostics. Exact evidence: `docs/superpowers/validation/2026-08-15-deployed-boundary-refactor.md`. |

The local horizontal runner persists `http://host.docker.internal:9100` by default because the Source connection is executed by the Docker backend. The host smoke URL remains `http://127.0.0.1:9100`; override `--medusa-base-url` only when the backend itself runs at a different network boundary.

| ToolRouter snapshot and adapter | `.\.venv\Scripts\python.exe -m pytest backend\tests\integrations\toolrouter -q` | Exact source hashes/no sibling import; normalization, graph/conformance/index artifacts, fresh-adapter reload, GRAG decisions/traces, model identity, resume, token ledger, quarantine, and accepted export | Algorithm fixture is isolated; injected test transports never enter product composition. Real MiniLM/Ollama behavior is a separate acceptance gate. |
| API execution snapshot and Corpus adapters | `.\.venv\Scripts\python.exe -m pytest backend\tests\integrations\api_execution -q` | Exact byte-identical neutral closure, restricted imports, internal-use provenance, approved dependency pins, Prance/openapi-core compatibility, JIT credential handling, request/response validation, one-call/no-retry execution, reviewed writes, and redacted result identity | Phase A remains the neutral foundation. Corpus-owned connection-check and routed adapters now invoke it through explicit Source/assembled-Agent boundaries. Current three-mode ecommerce evidence proves one validated product read plus separately reviewed cart creation and add-to-cart against reviewed effective hash `c0b9c6bf...`; it is not a generic executor or production claim. |
| Sources feature and API connector | `.\.venv\Scripts\python.exe -m pytest backend\tests\sources -q`; `.\.venv\Scripts\python.exe scripts\record_source_hub_first_slice.py` | Owner isolation, API YAML plus optional Markdown intake, source/revision/job linkage, real registered Huey task, queued/running/ready/failed transitions, persisted semantic groups and exact owner/source/revision/stage inspection, protected revision-bound connection profile saving, empty public save arguments, explicit retry, ToolRouter bridge translation, auth/origin HTTP, Source Hub RouteDeck declarations, and rendered desktop/mobile lifecycle evidence | Local Compose run `20260807T082751Z-47061af05e` passed 7/7 with eight screenshots and continuous video. Its raw Playwright trace was later removed because it retained an Authorization header; exact pre-removal identity is in the security manifest. Credentials remained private-form-only and absent from public dispatch/profile evidence. Ordered replay controls, connection checks, and real Medusa API execution are not claimed. |
| Immutable API contract revision Phase B | `.\.venv\Scripts\python.exe -m pytest backend\tests\sources -q`; `pnpm --dir frontend test -- api-contract-revision-surfaces.test.tsx framework-shell.test.tsx`; `.\.venv\Scripts\python.exe scripts\run_api_contract_revision_journey.py --url http://127.0.0.1:5199` | Exact raw/repair/parent/final/local/evidence provenance, ten patch records and shared impact 2, owner isolation, pointer-last Source publication, lifecycle read/write coherence, new immutable revision, historical reads, Source-scoped concurrency, durable required review/reject/accept/recheck, active/detail/review projection, safe result handling, no target transport, and redacted evidence shape | Automated contracts are green. Run `20260807T173632Z-466c48dc53` passed 8/8 with exact identities, reject/accept, immutable child, reload/restart, mobile bounds, video, safe trace, four non-execution operations and zero diagnostics. Its desktop stills missed the tall proposal/review panels; three downscaled `from-video` frames with exact sample/time/hash provenance now provide a truthful multi-frame desktop sequence. Final visual attempt `20260807T175743Z-215fdca86b` exposed and retained one real transient inventory 500 during Huey `mark_running`; pointer ordering and shared Source-lock coherence are fixed with RED/GREEN tests and clean review, but no post-fix browser run occurred. See `docs/superpowers/validation/2026-08-07-api-contract-revision-phase-b.md`. |
| Safe API connection check Phase C | `.\.venv\Scripts\python.exe -m pytest backend\tests\sources backend\tests\integrations\api_execution backend\tests\evaluation\test_api_connection_check_journey_recorder.py -q`; `.\.venv\Scripts\python.exe scripts\run_api_connection_check_journey.py --url http://127.0.0.1:5199` | Exact owner/Source/effective-revision/profile/credential-version recheck, JIT secret resolution, one-call/no-retry GetProductTypes/GetProductTags reads, exact-contract validation, immutable redacted success/failure, real SQL RouteDeck agent/surface guards, restart persistence, inventory coherence and owner isolation | Focused gate is 64 passed. Run `20260807T201347Z-311a9da2f3` retained 8/8 passing behavior assertions, six screenshots, continuous video and a 208-event safe trace. Its immutable status remains failed solely for Playwright sign-out `ERR_ABORTED`; backend logged the exact request 204 and the second-owner assertion passed. The exact-204-correlated recorder fix is green/reviewed but was not browser-rerun. See `docs/superpowers/validation/2026-08-08-api-connection-check-phase-c.md`. |
| API operation curation Phase D | `.\.venv\Scripts\python.exe -m pytest backend\tests\sources backend\tests\evaluation\test_api_operation_curation_journey_recorder.py -q`; `pnpm --dir frontend test -- api-operation-curation.test.tsx`; `.\.venv\Scripts\python.exe scripts\run_api_operation_curation_journey.py --url http://127.0.0.1:5199 --backend-url http://127.0.0.1:8099` | Exact READY revision/ToolRouter inventory, exhaustive include/exclude, non-mutating filtering, append-only history, exact CAS and concurrent conflict, corrupt-history failure, real SQL RouteDeck agent/surface guards, stale visible authoritative refetch, reload/restart, owner isolation, and non-execution | Run `20260807T212855Z-f8596ef591` passed 9/9 with eight inspected screenshots, 62.16-second chronological video, two raw clips, 171-event safe trace, zero unexpected diagnostics and zero API calls. The OpenAPI input is explicitly a development probe through the real Source Hub/Huey/ToolRouter path. See `docs/superpowers/validation/2026-08-08-api-operation-curation-phase-d.md`. |
| API route planning Phase E | `.\.venv\Scripts\python.exe -m pytest backend\tests\sources\test_api_route_plans.py backend\tests\sources\test_api_route_plan_routedeck.py backend\tests\evaluation\test_api_route_planning_journey_recorder.py -q`; `pnpm --dir frontend test -- api-operation-test-panel.test.tsx conversation-lifecycle.test.ts corpus-connection.test.ts`; `.\.venv\Scripts\python.exe scripts\run_api_route_planning_journey.py --url http://127.0.0.1:5199` | Curated ToolRouter subset before routing, immutable owner/conversation/session lineage, no ambiguity preselection, typed same-lineage choice and missing-input clarification, managed-profile/current-request provenance, zero calls, restart, three-conversation and owner isolation | Run `20260808T000249Z-c67d5b0004` passed 13/13 with six inspected screenshots, a 143.760-second continuous video, a 293-event safe trace, zero unexpected diagnostics and seven retained zero-call records. This proves route preparation only; read/write execution remains open. See `docs/superpowers/validation/2026-08-08-api-route-planning-phase-e.md`. |
| Linked RouteDeck React recovery suite | From `D:\Dev\AI Projects\routedeck`: `pnpm --filter @routedeck/react test` | Normalized loading/ready/recovery phases, retained session-create retry, legal resync, post-ready continuity, and non-live projected-Surface interaction gating | Framework proof for the linked package; Corpus remains responsible for product copy and owner-auth cleanup policy |
| Linked RouteDeck core conversation contracts | From `D:\Dev\AI Projects\routedeck`: `pnpm --filter @routedeck/core test`, `pnpm --filter @routedeck/core typecheck`, and `pnpm --filter @routedeck/core build` | 89 tests plus strict types/build covering generated history/SSE descriptors, exact field sets, request-ID Unicode-code-point limits, JavaScript-safe version integers, legacy conversation decoder parity, and Corpus-authorized empty-success reliability semantics | Framework contract proof. RouteDeck is read-only unless a new named upstream change is explicitly authorized. |
| Corpus migration | `docker compose run --rm backend true` | Entry-point migration upgrades the central database through Agent build lineage, Designer, Builder/Sandbox, Evaluation, Channels/Deployment, immutable Builder NavGraph persistence, and durable Builder assembly lifecycle at `0019_builder_assembly_lifecycle` | Product startup checks the configured current revision and fails when behind; focused migration and service tests cover the horizontal schema. |
| Shared infrastructure contracts | `.\.venv\Scripts\python.exe -m pytest backend\tests\jobs backend\tests\credentials backend\tests\infrastructure backend\tests\persistence -q` | 12 tests covering persistence-before-enqueue, Huey opaque scheduling/composition, owner isolation, explicit failure/retry and exhaustion, lifecycle records, SecretBox encrypted-at-rest metadata, rotation, wrong-key/tamper failure, required configuration, and exact migration schema | Infrastructure proof only; no Source or later product feature is wired or claimed by this gate |
| Frontend type gate | `pnpm --dir frontend typecheck` | Strict TypeScript compatibility with the linked RouteDeck packages | Compile-time only |
| Frontend production build | `pnpm --dir frontend build` | Vite production bundling and linked RouteDeck package resolution | Does not serve or interact with the built bundle |
| Live Lounge smoke | `.\.venv\Scripts\python.exe scripts\smoke_live.py` | Running health/readiness, anonymous bearer, opaque conversation, declared entry run, user run, deliberate SSE disconnect/reconnect by cursor, idempotent attach, and durable `assistant,user,assistant` history | Requires the local backend and explicitly selected real Ollama or OpenAI model; fails rather than substituting a provider, model, or response |
| Real Lounge product journeys | `.\.venv\Scripts\python.exe scripts\run_lounge_product_journeys.py` | Studio-owned account journeys through isolated Corpus backends/frontends, official Playwright Chromium, disposable SQLite state, real Gmail SMTP, Mail.tm, rendered outcomes, transcripts, screenshots, traces, and deterministic backend assertions | Requires real mail/network configuration; failures remain immutable artifacts. Fresh aggregate `20260806T062952Z-fac606911c` passed 8/8. |
| Public Lounge boundary recording | `.\.venv\Scripts\python.exe scripts\run_public_lounge_recording.py --backend-port <port> --frontend-port <port>` | Exact public privacy response, Sign-in Surface transition, and immediate post-chat Back-to-Lounge dispatch after RouteDeck resynchronization, with screenshot/video/trace and browser diagnostics | Uses an isolated local backend/frontend and disposable SQLite state. Run `20260806T173245Z-898d846f57` passed 2/2 with zero HTTP, console, or page errors; aborted stream/poll requests during navigation and teardown are retained as diagnostics. |
| Generic feature action/state evaluations | `.\.venv\Scripts\python.exe scripts\run_isolated_feature_evaluations.py --feature <feature> --behavior <behavior>` | Executes Studio-defined setup, real RouteDeck operation dispatch, node transition, bound outcome, domain state, and projection checkpoints with immutable artifacts; action-only plans do not use a semantic chat judge | Fresh local backend/SQLite state per run; current passing evidence covers Workspace quick action plus Agent create/edit |
| Per-definition evaluation evidence index | `.\.venv\Scripts\python.exe -m pytest backend\tests\evaluation\test_evidence_index.py backend\tests\evaluation\test_product_journey_artifacts.py -q` | Both evaluator writers update one atomic latest-evidence index with status, artifact, and definition hash independently for each evaluation ID; refreshing one result preserves unrelated current definitions | Focused immutable-evidence selection proof; does not execute a model or product journey |
| Core Workspace and Agents browser journey | `.\.venv\Scripts\python.exe scripts\run_core_agents_browser_journey.py` | Rendered registration, honest Workspace overview, Agent empty state, supervised create/edit, immutable v1-to-v2 persistence, responsive desktop/mobile surfaces, and return-to-Workspace count | Fresh isolated local backend/frontend and SQLite; latest passing artifact is `.runtime/evaluations/20260806T061531Z-bf0bc49c7c/result.json` |
| Agent Source attachment lifecycle | `.\.venv\Scripts\python.exe scripts\run_agents_lifecycle_journey.py` | Real Agent selection, Source upload + Huey/ToolRouter READY processing, exact revision attachment, Agent return, open attached Source, reload/restart persistence, hardened mobile evidence before mandatory restart, screenshots and video | Latest run `20260807T115259Z-ca04df5b57` passed 6/6 with zero product HTTP/console/page errors, exact 390x844 bounds for Attached Sources/revision/Attach/Open, and successful post-capture backend restart recovery. Its credential-bearing raw Playwright trace was removed and indexed by SHA-256 in the security manifest. See `docs/superpowers/validation/2026-08-07-step5-agent-source-attachments.md`; 3 focused helper tests protect viewport bounds, delayed-bootstrap recovery and evidence order. Later Step 5 behavior remains unclaimed. |
| Phase 6 Agent and Source lifecycle breadth | `.\.venv\Scripts\python.exe scripts\run_phase6_product_breadth_journey.py --module <agents\|sources> --url http://127.0.0.1:5199` | Agent immutable edit, attach/detach, dependency guidance, reviewed archive/delete; Source description isolation, dependency-blocked deletion, reject/accept disposable deletion; normal-speed maximized films with no Source analysis or target API call | Agent milestone `20260812T133737Z-790bea8d` passes its explicit prefix boundary in 27.680s; the parent truthfully remains failed after the later Source recorder ambiguity. Source `20260812T134036Z-db4f8fab` passed independently in 26.200s with zero unexpected HTTP/console/page diagnostics. |
| Owner restart smoke support | `.\.venv\Scripts\python.exe -m pytest tests\test_smoke_restart_recovery.py -q` | 27 tests covering exact cross-restart identity/conversation state, dual-database/path ownership, loopback restrictions, exclusive state reservation, real persisted bearer setup, fail-closed cleanup, stale/crafted-state rejection, decoy preservation, and disabled unsafe direct execution | Helper/ownership proof only. Real recovery is the separate disposable-runtime smoke below. |
| Real isolated restart recovery | `.\.venv\Scripts\python.exe -m scripts.smoke_restart_recovery_isolated` | Starts a loopback backend with fresh owned Corpus-auth and RouteDeck SQLite stores, begins a real Ollama turn, gracefully stops and immediately restarts, verifies authorized conversation plus durable `turn_interrupted`, then removes the entire owned runtime | Real local integration proof. Failure preserves its exact temporary directory/log; success never selects or mutates normal `.runtime` databases. |
| Design notebook structure | `python scripts/validate_design_notebook.py` | Proposed 15-feature/53-node design artifact, edge targets, summary counts, and inline script syntax | Proposed broader product Navgraph only; not the live eight-node Workspace-plus-Sources graph |
| Agent design parity | `.\.venv\Scripts\python.exe scripts\check_agent_design_parity.py` | Studio feature prompts, one-behavior/one-Node shape, exact scoped policies, Capability/Surface/Operation membership, SuggestedAction targets, and complete compiled-feature manifest coverage without technical IDs in Studio state; `--verbose` appends exhaustive scope-level evidence | Fail-closed current-state gate; a pass means the saved Studio design and implementation manifest match the compiled feature contracts covered by the checker. |
| Agent design parity checker | `.\.venv\Scripts\python.exe -m pytest tests\test_agent_design_parity.py -q` | Matching contracts pass, exact policy-scope drift fails with missing and undesigned evidence, and concise/verbose reports preserve the same mismatch set | Synthetic checker proof; does not claim current Corpus parity |
| Context tooling unit suite | `python -m unittest discover -v` | Code-map parsing, Git rename parsing, glob matching, ownership warnings, and design-validator tests | Repository-local context tooling only |
| Feature behavior notebook unit contract | `python -m unittest tests.test_feature_behavior_notebook -v` | Approved 11-feature ordering, Markdown round-trip, payload validation, and atomic repo-local saves | Serialization and persistence only; rendered interaction is checked separately |
| RouteDeck Agent Design Studio | `pnpm --dir docs/corpus-agent-design/workbench test`; `.\.venv\Scripts\python.exe scripts\record_design_studio_walkthrough.py --url http://127.0.0.1:8782/` | 49 tests cover readiness, accepted Agents/Source contracts, behavior completeness, clarification boundaries, and absence of implementation IDs | Product-semantic design only. Agent attachment/create/open handoffs have bounded runtime proof. Archive/delete is implemented with automated contract proof but still lacks a complete post-fix browser campaign; operations hub and build lineage remain runtime-unimplemented. |
| Changed-file ownership advisory | `python scripts/check_doc_coverage.py` | Maps changed supported files to code-map rows and anchors | Advisory and exits zero on warnings |
| Standalone Agent Execution Runtime proof | From `D:\Dev\AI Projects\agent-execution-runtime`, run the six gates listed in `docs/local-runtime-runbook.md` | Immutable build assembly, Ollama intent, ToolRouter decisions, capability-scoped API execution, isolation/recovery, trace, evaluation, and eligibility | External development proof only; Corpus does not import or invoke it, and its proof manifest validates recorded real runs rather than creating a fresh browser run |

## Prerequisites

- Primary runtime: Docker Desktop Linux engine, Ollama, the sibling RouteDeck
  checkout, `gemma4:latest`, and `qwen2.5-coder:7b`, then
  `docker compose up --build`.
- Direct-host validation additionally requires `.\scripts\init-local.ps1`,
  Python 3.11, Node.js, and pnpm.
- `scripts/init-local.ps1` caches MiniLM revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` and fails if it cannot.
- In direct-host mode, start `.\scripts\run-backend.ps1` and
  `.\scripts\run-frontend.ps1` before the live smoke.

## Docker Development Validation

On 2026-07-27, `docker compose up --build -d` started the backend, frontend,
and notebook locally. All three services became healthy and returned HTTP 200
at `http://127.0.0.1:8099/readyz`, `http://127.0.0.1:5199/`, and
`http://127.0.0.1:8771/#structure`. The final backend/notebook image is 2.39 GB
after pinning the official CPU PyTorch wheel; the frontend image is 1.14 GB.

The real authenticated UI path uploaded the ToolRouter repository's Ory Kratos
`api.yaml` (309,572 bytes) and produced 56 endpoints, 477 graph nodes, 876
edges, and 477 cards. `create a new identity` returned
`ASK_DISAMBIGUATE` / `low_score_margin`, led by
`api:createRecoveryLinkForIdentity` at 0.4280. The reviewed evalset completed
1/1 accepted, zero quarantined, and 3,823 offline tokens using
`gemma4:latest` and `qwen2.5-coder:7b`. Reload plus backend-container recreation
retained the owner-scoped Source, artifacts, metrics, and retrieval result.

Evidence screenshots:

- `C:\Users\ragha\.codex\visualizations\2026\07\22\019f895d-bb32-7f31-94ab-df128085c19c\corpus-docker-toolrouter-e2e.png`
- `C:\Users\ragha\.codex\visualizations\2026\07\22\019f895d-bb32-7f31-94ab-df128085c19c\corpus-docker-structure-explorer.png`

Final automated gates: 59 backend passes on the host lane (including the two
tests whose deliberate `127.0.0.1` Ollama contract requires the host), 19
frontend passes plus clean typecheck/build inside the frontend image, clean
Python dependency checks, 15 repository unittest passes, design notebook
validation at 15 features / 53 nodes / 146 edges, clean Compose configuration,
and a successful context-coverage advisory. The isolated backend image passes
the remaining 57 contracts; its two live-loopback Ollama tests are verified on
the host and the actual container-to-host model boundary is proven by the UI
evalset run.

## Rendered Product Validation

On 2026-07-30, cookie-bound session recovery and the client-side 30-second
greeting convergence reset were superseded by bearer identity, public Corpus
conversation selection, and server-owned RouteDeck runs. Current validation is
the bearer reconnect smoke above; older rendered evidence below is retained as
historical UI evidence only and does not describe current session transport.

On 2026-07-28, the preserved browser state that previously rendered
`Application session expired` was reloaded against rebuilt local Docker. The
backend recorded selected-session `410`, replacement-session `201`, and the
replacement event stream `200`. The same tab rendered the Lounge, contained
neither the Corpus nor RouteDeck expiry message, remained stable across a
follow-up observation, and reported no browser warning/error entries.

That short follow-up missed a post-ready resynchronization loop. A sustained
reproduction then measured 33 visible loading/Lounge transitions in six
seconds, alongside 58 selected-session reloads, 58 SSE reconnects, and 116
owner-auth reads in 30 seconds. After RouteDeck preserved the mounted
application across background `resync_required`, `resyncing`, and `connecting`
states, the rebuilt browser remained on the Lounge for 150/150 samples over 15
seconds with zero transitions and zero warning/error console entries.

On 2026-07-22, the running app was exercised at desktop size and 390x844 through:

```text
load contract -> create guest -> register owner -> adopt guest RouteDeck session
  -> workspace.home -> reload persistence -> explicit pre-configuration Gmail error
  -> logout -> fresh guest Lounge -> sign in -> resume owned session
  -> forgot password -> generic request response
```

The rendered run also proved first-field focus, credential-surface composer
lockout, advisory verification state, owner/workspace header data, and no
horizontal overflow at 390x844.

The configured `no-reply@saastoagent.com` Gmail path was subsequently exercised
through the live Corpus API. Gmail accepted both the verification request
(`204`) and password-reset request (`202`) for
`raghavdasila@highpolar.io`; inbox confirmation is external evidence.

The verification-link regression was then reproduced with a fragment-bearing
URL: RouteDeck history replacement had removed the fragment before the surface
hook mounted. After moving capture ahead of bootstrap, an in-app browser run
rendered the verification surface in 2,435 ms, removed the fragment from the
visible URL, left the Verify email button enabled, and showed no missing-token
message. The pre-fix trace attributed 14,664 ms of 14,804 ms startup to the
blocking Ollama greeting; the shell now renders first and token surfaces skip
that greeting.

The live Corpus assistant endpoint subsequently emitted 82 separate assistant
deltas before its terminal event (first delta at 13,419.8 ms; `assistant_end`
at 14,235.9 ms). The linked RouteDeck coordinator test gates terminal
completion and proves the accumulated partial callback fires first; the Corpus
shell test proves that partial callback state renders as a streaming assistant
message rather than remaining a thinking-only buffer.

On 2026-07-23, the sibling `@routedeck/react` suite passed 13 tests and its
typecheck/build passed before Corpus verification. Corpus then passed 18
frontend tests, strict typecheck, and production build. A fresh in-app browser
load at `http://127.0.0.1:5199/` crossed the new
`RouteDeckBootstrapBoundary`, reached RouteDeck `Ready`, and restored the real
persisted Lounge greeting against backend `/healthz` and `/readyz` responses of
200. The framework recovery suite, rather than a Corpus reimplementation,
proves retained create, resync, navigation, and missing/expired-session action
legality.

Later on 2026-07-23, the Sources/ToolRouter product path was exercised in the
same local in-app browser at `http://127.0.0.1:5199/sources`:

```text
create synthetic local owner -> owner Home -> Sources
  -> upload real Ory Kratos v26.2.0 api.json
  -> normalize/build/index -> ready
  -> query create a new identity -> ASK_DISAMBIGUATE
  -> run api-debug-v1 through real Gemma generator and Qwen reviewer
  -> reload Sources -> persisted source/metrics -> run retrieval again
```

The upload produced 56 endpoints, 316 schemas, two security schemes, zero
repairs, 477 graph nodes, 876 edges, and 477 cards. The retrieval reason was
`low_score_margin`; its top five scores were 0.4280, 0.4259, 0.4217, 0.4177,
and 0.4171, led by `api:createRecoveryLinkForIdentity`. After a hard page
reload, the persisted source returned the same explicit decision and included
`api:createIdentity` in the ranking.

The real `api-debug-v1` run completed one of one candidate, accepted one,
quarantined zero, and recorded 2,936 offline tokens plus the exact installed
Gemma/Qwen digests. The accepted candidate selected
`api:listIdentitySessions`; it is a reviewed candidate, not human gold.
The earlier 390x844 check accepted a horizontally scrollable bottom navigation
row. That presentation is superseded: application navigation now opens from a
header hamburger Sheet, and the Navgraph keeps its own header drawer trigger.
Backend `/readyz` returned 200 for the historical Sources run.

On 2026-07-28, the responsive shell regression passed 25 frontend tests plus
strict typecheck and production build. Live in-app-browser checks at 390x844
measured the independently scrolling conversation ending at y=604.5, the
161.5px surface dock directly above the composer, and the composer ending at
y=834 with no horizontal document overflow. The previous 74px bottom
navigation row was absent; the unique hamburger opened a full-height 292.5px
Workspace navigation Sheet. At 1440x900 the 240px desktop rail remained, while
the surface dock still sat immediately above the composer. Browser warning and
error logs were empty at both sizes.

Fresh automated closeout on the same implementation produced 52 backend
passes, 19 frontend passes, a strict TypeScript pass, a production build pass,
12 repository unittest passes, and no broken Python requirements. Vite emitted
only its non-failing >500 kB chunk advisory.

On 2026-07-24, the Source configuration/HTTP boundary refactor produced a
fresh 56-pass backend suite, clean dependency check, 19-pass frontend suite,
strict typecheck, and production build. A real authenticated HTTP run through
the connector-owned API upload router ingested Ory YAML, returned the established
56 endpoint / 477 node / 876 edge / 477 card evidence, returned
`ASK_DISAMBIGUATE`, and completed a 1/1 accepted, zero-quarantine evalset with
2,936 offline tokens using the exact configured Gemma/Qwen digests.

On 2026-07-24, the Structure explorer was corrected to retain the complete
proposal while adding implemented files beside it. Its green implemented,
amber planned, and blue mixed states were checked in the rendered notebook.
The same verification run re-exercised persisted Ory source metrics, live GRAG
retrieval, and real Gemma/Qwen evalset generation. The 35-second H.264 evidence
walkthrough is
`logs/evidence/20260724-toolrouter-sources-walkthrough.mp4`; exact observations
and its SHA-256 are in `logs/20260724_toolrouter_video_evidence.md`.

Later on 2026-07-24, the Sources evidence surface was made explicit as a
four-stage pipeline and exercised end-to-end with the sibling ToolRouter
project's real Ory Kratos `api.yaml`. The rendered rail reached complete for
API collection, graph/index, GRAG retrieval, and reviewed evalset. The upload
produced 56 endpoints, 477 graph nodes, 876 graph edges, and 477 cards.
`create a new identity` returned `ASK_DISAMBIGUATE` with
`low_score_margin`; `api-debug-v1` accepted 1/1 using `gemma4:latest` as
generator and `qwen2.5-coder:7b` as reviewer, recorded 2,936 offline tokens,
and quarantined zero. The component test now asserts YAML multipart upload and
each pipeline-stage transition. Desktop 1440x900 and mobile 390x844 checks
rendered the rail correctly; the mobile document had equal 390 px client and
scroll widths. Browser logs contained no warnings or errors.

## Architecture drift gate

Run:

```powershell
.\.venv\Scripts\python.exe scripts\check_architecture_boundaries.py
.\.venv\Scripts\python.exe -m pytest tests/test_architecture_boundaries.py -q
```

The gate discovers and checks every immediate backend and frontend feature
directory. It allows only self imports, stable shared/public infrastructure,
`corpus.auth.contracts`, and another feature's exact public `contracts` module.
It rejects concrete cross-feature internals, application/runtime composition,
concrete integrations, private infrastructure repositories, and hard-coded
external RouteDeck IDs in the selected-Agent transition handler. The backend
Agents contract suite additionally proves that every exported external-area
allowlist equals the compiled target Node's actual Agent-bound operations. The command
must pass with zero real-repository violations; no checked-in baseline or
current-file ignore is permitted. See
`skills/audit-corpus-boundaries/SKILL.md` for the audit/fix workflow.

## Not Yet Proven

- deeper behavior-note work beyond the accepted ecommerce path and the
  isolated lifecycle milestones, including exhaustive per-behavior
  chat/surface/hybrid matrices rather than one integrated path;
- polished visual hierarchy for several later surfaces, correct docked
  overflow at narrow widths, and natural-language review copy without repeated
  tester vocabulary;
- a browser-produced truthful failed-deployment/retry state (the durable
  explicit retry contract is protected, but no failure was fabricated merely
  for a film);
- the proposed 53-node notebook Navgraph as a live runtime (the product instead
  has an 18-node owner application plus exact one-node per-build Agent apps);
- production/object-store persistence, multi-worker behavior, remote model
  access, or human-gold evalset quality.

`architecture/code-map.md` owns source-to-test mapping. Update it with any
test movement or change in claim meaning.
