# Corpus boundary refactor validation

Date: 2026-08-14

Status: passed locally

## Result

ADR-005 is implemented without changing the accepted Corpus product path.
Every immediate backend and frontend feature is governed by the same
directory-discovered dependency rule with zero exemptions. Process composition
is owned by `corpus.app.worker`. Cross-feature use is through public contracts,
consumer-owned ports, neutral shared types, and application adapters. Generic
API execution validates the exact selected reviewed revision, while the Medusa
2.13.6 correction is an explicitly selected acceptance integration.

## Fresh executable gates

All commands ran from `D:\Dev\AI Projects\saastoagent-v0.1`.

| Gate | Result |
| --- | --- |
| `.\.venv\Scripts\python.exe scripts\check_architecture_boundaries.py` | Passed with `Corpus architecture boundaries passed.` and zero baseline/exemptions |
| `.\.venv\Scripts\python.exe -m pytest tests -q` | 98 passed in 9.44s |
| `.\.venv\Scripts\python.exe -m pytest backend\tests -q` | 532 passed, 6 dependency deprecation warnings, in 120.80s |
| `pnpm --dir frontend test` | 35 files and 188 tests passed in 10.89s |
| `pnpm --dir frontend typecheck` | Passed |
| `pnpm --dir frontend build` | Passed; Vite retained its non-failing greater-than-500-kB chunk advisory |
| `docker compose config --quiet` | Passed |
| production Compose with digest-shaped placeholder images and `CORPUS_RUNTIME_ENV_FILE=.env.example` | Passed; this validates interpolation/schema only and does not start production |
| repo-local boundary skill through `skill-creator/scripts/quick_validate.py` | `Skill is valid!` |

`scripts/check_doc_coverage.py` exited zero. Current files have code-map owners;
its one remaining advisory names the intentionally deleted legacy path
`backend/src/corpus/clarification.py`. The live clarification contract is owned
by `backend/src/corpus/shared/clarification.py`; the advisory reports the
deleted changed path and is not a missing owner in the present tree.

The first frontend full-suite attempt was deliberately run concurrently with
both Python suites and timed out in two tests without assertion mismatches.
Those exact tests then passed 18/18 alone in 5.21s, and the unchanged complete
frontend suite passed 188/188 serially. No timeout was raised and no assertion
was weakened.

## Local runtime proof

The final product runtime was local. It had been started/rebuilt through the
documented Docker Compose path, equivalent to:

```powershell
docker compose up --build -d backend frontend source-worker
```

The active backend and frontend containers were healthy and the application-
owned Source worker was running. Fresh smoke requests returned HTTP 200:

- `http://127.0.0.1:8099/healthz`
- `http://127.0.0.1:8099/readyz`
- `http://127.0.0.1:5199/`
- `http://127.0.0.1:9100/health`

Medusa is reached from the host at `127.0.0.1:9100`; Sources executed by the
Docker backend persist `http://host.docker.internal:9100`. ToolRouter provider
selection is independent from the product conversation-model provider. The
local stack explicitly selected Ollama for ToolRouter; production Compose
explicitly selects its configured OpenAI ToolRouter models. Neither boundary
silently falls back.

## Final three-mode acceptance

The existing recorder ran sequentially against frontend
`http://127.0.0.1:5199` and backend `http://127.0.0.1:8099` after the focused
boundary/runtime corrections.

| Mode | Result | Run ID | Immutable result |
| --- | --- | --- | --- |
| Surface | 39/39 | `20260814T093227Z-c2b50e9520` | `artifacts/horizontal-product-surface/20260814T093227Z-c2b50e9520/result.json` |
| Hybrid | 40/40 | `20260814T094346Z-c08c93dd9e` | `artifacts/horizontal-product-hybrid/20260814T094346Z-c08c93dd9e/result.json` |
| Chat | 39/39 | `20260814T104438Z-b8dd360dbc` | `artifacts/horizontal-product-chat/20260814T104438Z-b8dd360dbc/result.json` |

The strict recorder assertions were not reduced. Owner-language prompts were
made more explicit where a model could otherwise request a downstream action
before its required Source, Agent, or Evaluation binding existed.

## Claim boundary

This proves the refactored modular-monolith boundaries and the already accepted
Medusa ecommerce vertical in three local interaction modes. It does not claim
generic success for every external API, complete Behavior Note breadth,
microservice/process isolation per Agent, production deployment, or an SLA.
RouteDeck was inspected only through its existing read-only contracts and was
not changed. The user-owned behavior notes were not changed.
