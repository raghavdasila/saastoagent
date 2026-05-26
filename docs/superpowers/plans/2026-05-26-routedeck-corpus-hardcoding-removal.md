# RouteDeck Corpus Hardcoding Removal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the Python-side phrase router from Corpus, restore RouteDeck-aligned ownership boundaries, and make owner-workbench chat navigation flow through one model-planned typed-operation path only.

**Architecture:** RouteDeck remains the reusable runtime, projection, navigation, and surface contract. Corpus remains the SaaStoAgent product agent that reads the current RouteDeck projection, chooses one typed legal operation or a clarification, and never relies on heuristic phrase tables in Python. The graph runtime remains the only authority for legality, guards, node transitions, and active surface state.

**Tech Stack:** FastAPI backend, SQLAlchemy async runtime, `routedeck_core`, `@routedeck/react`, OpenAI chat-completions router prompt, pytest, Playwright/browser E2E.

## Implementation Outcome - 2026-05-26

Status: implemented and verified on the current worktree.

Completed in this session:

- deleted the owner-workbench heuristic chat router from `runtime.py`
- added `corpus_turn_planning.py` with structured planning context and output normalization
- moved owner-workbench chat planning fully onto model-selected typed legal operations
- added active-surface selectable entity context so chat can open visible SaaS Agent list items without hidden-id prompts
- reran focused backend tests, broader backend tests, frontend type-check, Docker rebuild, manual in-app browser chat verification, `npm run e2e:docker`, and `npm run e2e:medusa:docker`

Residual debt intentionally left for the next slice:

- browser URL replay / popstate still constructs a frontend-authored `route.open_node` payload
- snapshot/load still needs stricter `surface_id` validation
- `route.open_node` planner schema can still be made more faithful to legal node/surface combinations

---

## Boundary Rules For This Fix

- Delete the hardcoded router completely. Do not keep it behind feature flags, compatibility branches, or "fast path" exceptions.
- Do not add replacement synonym tables, alias maps, or phrase matchers in Python, RouteDeck metadata, or prompt-side hidden config.
- Do not move product navigation interpretation into RouteDeck shared code.
- Keep owner workbench Corpus chat separate from deployed-agent public chat in code, tests, and wording.
- If the model cannot choose a legal operation confidently, it must clarify. That is acceptable. A heuristic fallback is not.

## Decision Authority

RouteDeck exposes awareness. Corpus decides. Graph validates.

That means:

- RouteDeck provides the agent with the current navgraph-facing context: legal operations, blocked constraints, active surfaces, current location, required args, missing args, and valid navigation/surface options.
- Corpus interprets the user turn against that current context and decides what to do next.
- AppGraph runtime validates the chosen typed operation, enforces guards, and commits or rejects it.

This fix must preserve that exact split:

- RouteDeck must not decide intent.
- Python helper code in Corpus runtime must not guess intent from phrases.
- The model should choose from current legal possibilities, not from a hidden lookup table.
- If multiple legal operations could fit, Corpus may clarify instead of forcing a route.

## Current Violations To Remove

The current heuristic layer lives in [runtime.py](</D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/services/app_graph/runtime.py>) and must be deleted:

- `_deterministic_turn_plan(...)`
- `_deterministic_surface_open_plan(...)`
- `_deterministic_surface_switch_plan(...)`
- `_projection_current_surface_id(...)`
- `_projection_surfaces(...)`
- `_match_surface_from_request(...)`
- `_normalized_turn_text(...)`
- `_turn_tokens(...)`
- `_looks_like_api_setup_request(...)`
- `_looks_like_agent_list_request(...)`
- `_surface_match_phrases(...)`
- the `stream_corpus_turn(...)` branch that calls `_deterministic_turn_plan(...)` before `_corpus_turn_plan(...)`

The now-coupled deterministic copy in [corpus_surfaces.py](</D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/services/app_graph/corpus_surfaces.py>) should also be removed if it becomes dead:

- `CorpusSurfaceRegistry.deterministic_open_message(...)`

The contract tests added to prove heuristic routing must be deleted from [test_corpus_graph_contract.py](</D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/tests/test_corpus_graph_contract.py>):

- `test_deterministic_turn_plan_opens_saas_agent_list_for_clear_chat_request`
- `test_deterministic_turn_plan_switches_learning_peer_surfaces_from_chat`

## Target Runtime Design

### 1. One planner path only

Owner-workbench free-text turns should follow exactly one interpretation path:

```text
current AppGraph state
  -> RouteDeck projection
    -> Corpus turn-planning context
      -> LLM chooses typed legal operation or clarify/reply
        -> runtime validates operation against current projection
          -> AppGraph commits
            -> RouteDeck projection refreshes
```

No Python code should infer "list agents", "open memory", "show failed executions", or similar intents from text. Those decisions must come from the model reading the current projected legal operations and active surfaces.

### 2. Product-owned planner context, not raw heuristic routing

Add a dedicated Corpus planner-context builder in a new backend module:

- Create: [backend/services/app_graph/corpus_turn_planning.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/services/app_graph/corpus_turn_planning.py)

This module should own two things:

- `build_corpus_turn_planning_context(...)`
- `normalize_corpus_turn_plan(...)`

The context builder should derive a compact product-owned planning payload from the current RouteDeck projection and current AppGraph state. It should include:

- current node id and node label
- active SaaS Agent summary if bound
- current active surface id, label, kind, and component
- active surfaces on the current node with `surface_id`, `label`, `surface_kind`, `variant`, and a short product-owned description when needed
- legal operations with:
  - `id`
  - `label`
  - `description`
  - `invocation_kind`
  - `can_dispatch_now`
  - `required_args`
  - `missing_args`
  - `target_node`
  - `execution_mode`
- blocked operations only as compact diagnostics when useful for clarification, not as the default action set

This is still Corpus-owned product behavior. RouteDeck remains unchanged unless a missing product-neutral contract blocks this work.

### 3. Planner output validation

`normalize_corpus_turn_plan(...)` should enforce:

- `intent` is one of the allowed values
- `operation_id` is either null or present in the current legal operations
- `args` is always an object
- `surface_intent` is always an object
- when `operation_id` is absent, the runtime falls back to `reply_now`, `clarify`, or `deep_work`
- when `operation_id` is present but illegal, the runtime treats it as a clarification failure, not a silent fallback to heuristics

This keeps the LLM inside the typed-operation contract without teaching Python to guess intents.

### 4. Prompt cleanup

Update the router prompt in [runtime.py](</D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/services/app_graph/runtime.py>) so it stops enumerating product workflow examples and instead says:

- choose only from the provided planning context
- prefer a legal typed operation when one clearly satisfies the request
- use `route.switch_surface` for same-node peer-surface changes only when that operation is legal and the desired target surface is present in `active_surfaces`
- clarify instead of inventing a route

Do not add hidden prompt phrase lists. The prompt should explain the contract, not encode lookup tables.

### 5. Surface switching stays generic

`route.switch_surface` remains the generic same-node peer-surface primitive defined in [manifest.py](</D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/services/app_graph/manifest.py>).

The model may select it when the planning context exposes multiple active peer surfaces on the current node. The runtime still validates the payload and current node before commit. No label matching helper should exist in Python.

## File Map

### Backend files to modify

- Modify: [backend/services/app_graph/runtime.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/services/app_graph/runtime.py)
  - remove deterministic router branch and helper functions
  - route all owner-workbench free-text planning through `_corpus_turn_plan(...)`
  - call the new context builder and plan normalizer
  - keep non-heuristic stale-review-surface cleanup intact

- Modify: [backend/services/app_graph/corpus_surfaces.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/services/app_graph/corpus_surfaces.py)
  - remove deterministic surface-open copy if unused
  - optionally add short product-owned surface descriptions if the model needs clearer semantics

- Create: [backend/services/app_graph/corpus_turn_planning.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/services/app_graph/corpus_turn_planning.py)
  - build compact turn-planning context from the current projection
  - validate and normalize model output

### Tests to modify or add

- Modify: [backend/tests/test_corpus_graph_contract.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/tests/test_corpus_graph_contract.py)
  - remove deterministic phrase-routing tests
  - add contract tests for planner-context shape and heuristic-removal guarantees

- Modify: [backend/tests/test_app_graph_contract.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/tests/test_app_graph_contract.py)
  - add source scan assertions that the backend app-graph runtime contains no phrase-routing helpers or deterministic text matcher names

- Add if needed: [backend/tests/test_corpus_turn_planning.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/tests/test_corpus_turn_planning.py)
  - isolate context-builder and output-normalization behavior from the larger runtime test file

### Browser/runtime verification targets

- Owner workbench Corpus chat navigation:
  - `/api/corpus/state`
  - `/api/corpus/stream`
  - `/api/corpus/action`

- Deployed agent task chat:
  - `/api/deployed-agents/*`

These must stay distinct in wording and test coverage.

## Implementation Tasks

### Task 1: Delete the heuristic router entirely

**Files:**
- Modify: [backend/services/app_graph/runtime.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/services/app_graph/runtime.py)
- Modify: [backend/services/app_graph/corpus_surfaces.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/services/app_graph/corpus_surfaces.py)
- Modify: [backend/tests/test_corpus_graph_contract.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/tests/test_corpus_graph_contract.py)

- [ ] Remove `_deterministic_turn_plan(...)` and all phrase-matching helper functions from `runtime.py`.
- [ ] Remove the `stream_corpus_turn(...)` branch that tries deterministic routing before `_corpus_turn_plan(...)`.
- [ ] Remove `CorpusSurfaceRegistry.deterministic_open_message(...)` if it is no longer referenced.
- [ ] Delete the deterministic router tests from `test_corpus_graph_contract.py`.
- [ ] Run:

```powershell
python -m pytest backend/tests/test_corpus_graph_contract.py -q
```

Expected:

- the old deterministic tests are gone
- any remaining failures point to code paths still referencing deleted helpers

### Task 2: Introduce a product-owned planning context builder

**Files:**
- Create: [backend/services/app_graph/corpus_turn_planning.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/services/app_graph/corpus_turn_planning.py)
- Modify: [backend/services/app_graph/runtime.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/services/app_graph/runtime.py)
- Modify: [backend/services/app_graph/corpus_surfaces.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/services/app_graph/corpus_surfaces.py)

- [ ] Build `build_corpus_turn_planning_context(...)` around the current RouteDeck projection instead of passing raw projection JSON directly.
- [ ] Keep the context compact and model-friendly. Include legal operation ids and active surface ids, but not unrelated diagnostics noise.
- [ ] If active-surface labels are too thin for reliable model selection, add short descriptions in Corpus-owned surface definitions, not alias tables.
- [ ] Update `_corpus_turn_plan(...)` to send `{ user_input, planning_context }` to the model instead of the current raw projection dump.
- [ ] Run:

```powershell
python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py -q
```

Expected:

- planner-context tests pass
- no new product literals were added to RouteDeck shared code

### Task 3: Validate planner output instead of guessing intent in Python

**Files:**
- Create or Modify: [backend/services/app_graph/corpus_turn_planning.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/services/app_graph/corpus_turn_planning.py)
- Modify: [backend/services/app_graph/runtime.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/services/app_graph/runtime.py)

- [ ] Add `normalize_corpus_turn_plan(...)` to enforce intent, operation legality, and object defaults.
- [ ] Make `stream_corpus_turn(...)` call the normalizer on model output before acting on it.
- [ ] Ensure illegal `operation_id` values result in clarification or refusal, never heuristic recovery.
- [ ] Remove prompt wording that enumerates product workflows as routing examples. Keep only contract-oriented instructions.
- [ ] Run:

```powershell
python -m pytest backend/tests/test_corpus_graph_contract.py -q
```

Expected:

- model-output normalization is covered
- no heuristic fallback behavior remains

### Task 4: Tighten boundary tests and wording

**Files:**
- Modify: [backend/tests/test_app_graph_contract.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/tests/test_app_graph_contract.py)
- Modify: [backend/tests/test_corpus_graph_contract.py](/D:/Dev/AI Projects/agent-core/agent-lab-powered-projects/saastoagent-v0.1/backend/tests/test_corpus_graph_contract.py)

- [ ] Add a backend source-scan test that fails if runtime source contains the deleted heuristic helper names or phrase-routing helper patterns.
- [ ] Add a contract test proving owner-workbench chat planning consumes structured legal operations and surfaces from the current projection, not a hardcoded intent table.
- [ ] Review existing test names and comments so owner-workbench navigation is not described as deployed-agent action execution.
- [ ] Run:

```powershell
python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py -q
```

Expected:

- the boundary tests explicitly guard against phrase-router regressions
- workbench/deployed-agent terminology is clean

### Task 5: Verify behavior as black-box navigation, not heuristic internals

**Files:**
- No required code changes if earlier tasks are correct

- [ ] Rebuild Docker services after backend changes:

```powershell
docker compose up -d --build backend frontend
```

- [ ] Browser-check owner workbench chat-only navigation through Corpus:
  - `list my agents`
  - `create a SaaS agent named ...`
  - `open instructions`
  - `open learning`
  - `show failed executions`
  - `go home`

- [ ] Verify these work because the model selects legal operations from the current projection, not because any Python phrase matcher exists.
- [ ] Separately browser-check deployed-agent checkout flow with:

```powershell
cd frontend
npm run e2e:medusa:docker
```

Expected:

- owner-workbench navgraph behavior works through `/api/corpus/*`
- deployed-agent checkout behavior works through deployed-agent runtime
- no workbench-only operations leak into public agent chat

## Acceptance Criteria

The fix is complete only when all of the following are true:

- no deterministic phrase-routing helpers remain in `backend/services/app_graph/runtime.py`
- no synonym or alias tables were added anywhere as a replacement
- owner-workbench free-text navigation uses the model planner only
- the model chooses only typed legal operations from the current projection
- `route.switch_surface` remains the generic same-node surface primitive
- workbench navigation and deployed-agent task execution are clearly separated in code, tests, and verification
- Docker/browser verification proves the behavior end to end

## Verification Command Set

```powershell
python -m pytest backend/tests/test_app_graph_contract.py backend/tests/test_corpus_graph_contract.py backend/tests/test_corpus_routedeck_runtime.py backend/tests/test_corpus_routedeck_state.py -q
cd frontend
npm run type-check
npm run e2e:docker
npm run e2e:medusa:docker
git diff --check
```

## Notes

- This plan intentionally prefers temporary clarification behavior over any hardcoded router fallback.
- If the model still struggles after the planner-context cleanup, improve the structured planning context first. Do not add phrase logic.
- RouteDeck shared code should change only if a genuinely product-neutral surface or planning contract is missing. The default assumption for this fix is that the drift lives in Corpus runtime, not in RouteDeck.
