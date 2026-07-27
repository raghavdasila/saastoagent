# Corpus Validation Index

## Executable Suite Index

| Suite | Command | Protects | Claim boundary |
| --- | --- | --- | --- |
| Backend framework/product suite | `.\.venv\Scripts\python.exe -m pytest backend\tests -q` | 59 tests: host/runtime/container entrypoint, owner identity, Workspace, ToolRouter provenance/adapter/settings, generic Sources lifecycle/HTTP/RouteDeck contract, API connector configuration/HTTP/engine boundary, cross-owner isolation, artifact reload, retrieval, and evalset semantics | Uses isolated persistence. Focused ToolRouter tests inject deterministic embedding/model transports to protect orchestration; the real models and real collection are proven separately below. |
| Frontend component suite | `pnpm --dir frontend test` | 19 tests: generic shell/bootstrap, owner session context, credential/recovery surfaces, incremental Lounge greeting, composer lockout, eight live RouteDeck surfaces, and Sources upload/retrieval/evalset UI contracts | jsdom component/contract coverage, not rendered browser proof |
| ToolRouter snapshot and adapter | `.\.venv\Scripts\python.exe -m pytest backend\tests\integrations\toolrouter -q` | Exact source hashes/no sibling import; normalization, graph/conformance/index artifacts, fresh-adapter reload, GRAG decisions/traces, model identity, resume, token ledger, quarantine, and accepted export | Algorithm fixture is isolated; injected test transports never enter product composition. Real MiniLM/Ollama behavior is a separate acceptance gate. |
| Sources feature and API connector | `.\.venv\Scripts\python.exe -m pytest backend\tests\sources -q` | Explicit generic storage, API-owned upload settings/HTTP, compact safe paths, atomic state, connector-neutral contracts, engine delegation, upload rejection, ToolRouter bridge translation, auth/origin/cross-owner HTTP, one Sources node, and import/transport ownership boundaries | Exercises feature integration against isolated temporary roots; real browser/product proof is separate. |
| Linked RouteDeck React recovery suite | From `D:\Dev\AI Projects\routedeck`: `pnpm --filter @routedeck/react test` | Normalized loading/ready/recovery phases, retained session-create retry, legal resync, and boundary gating | Framework proof for the linked package; Corpus remains responsible for product copy and owner-auth cleanup policy |
| Owner auth migration | `.\.venv\Scripts\python.exe -m corpus.auth.migrations` | Explicitly upgrades the separate Corpus auth database to `0001_owner_auth` | Product startup only checks this revision and fails when behind |
| Frontend type gate | `pnpm --dir frontend typecheck` | Strict TypeScript compatibility with the linked RouteDeck packages | Compile-time only |
| Frontend production build | `pnpm --dir frontend build` | Vite production bundling and linked RouteDeck package resolution | Does not serve or interact with the built bundle |
| Live Lounge smoke | `.\.venv\Scripts\python.exe scripts\smoke_live.py` | Running health/readiness, guest cookie, `workspace.lounge`, real assistant-initiated Ollama turn, real user turn, SSE completion, and durable `assistant,user,assistant` history | Requires both local services and the configured real Ollama model; fails rather than substituting a model or response |
| Design notebook structure | `python scripts/validate_design_notebook.py` | Proposed 15-feature/53-node design artifact, edge targets, summary counts, and inline script syntax | Proposed broader product Navgraph only; not the live eight-node Workspace-plus-Sources graph |
| Context tooling unit suite | `python -m unittest discover -v` | Code-map parsing, Git rename parsing, glob matching, ownership warnings, and design-validator tests | Repository-local context tooling only |
| Feature behavior notebook unit contract | `python -m unittest tests.test_feature_behavior_notebook -v` | Approved 11-feature ordering, Markdown round-trip, payload validation, and atomic repo-local saves | Serialization and persistence only; rendered interaction is checked separately |
| Changed-file ownership advisory | `python scripts/check_doc_coverage.py` | Maps changed supported files to code-map rows and anchors | Advisory and exits zero on warnings |

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
Desktop and 390x844 render checks passed after the navigation row became
horizontally scrollable. Browser warning/error logs were empty. Backend
`/readyz` returned 200.

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

## Not Yet Proven

- Agent Designer behavior/configuration, Sandbox execution, public Web,
  Operations, deployment, or any Source connector beyond API;
- the proposed 53-node product Navgraph as a live runtime;
- background workers, production/object-store persistence, multi-worker
  behavior, remote model access, or human-gold evalset quality.

`architecture/code-map.md` owns source-to-test mapping. Update it with any
test movement or change in claim meaning.
