# Step 2 Validation: Studio Governance

## Scope

This validation covers only Step 2 of the horizontal delivery plan:

- readiness-gated Studio approval and explicit invalid-approval display;
- corrected Lounge capability guidance;
- independent current-result identity per evaluation definition;
- accepted product design for deployed-agent clarification;
- unchanged RouteDeck and user-owned behavior notes.

It does not claim that deployed-agent clarification or the remaining launch
lifecycle is implemented at runtime.

## Runtime

- Location: local Windows development environment
- Studio URL: `http://127.0.0.1:8782/`
- Studio command: `pnpm --dir docs/corpus-agent-design/workbench dev --host 0.0.0.0 --port 8782 --strictPort`
- Corpus backend URL: `http://127.0.0.1:8099/`
- Corpus frontend URL: `http://127.0.0.1:5199/`
- Corpus stack command: `docker compose up --build -d backend frontend`

## Automated gates

| Command | Result |
| --- | --- |
| `pnpm --dir docs/corpus-agent-design/workbench test -- --run` | 42 passed |
| `pnpm --dir docs/corpus-agent-design/workbench typecheck` | Passed |
| `pnpm --dir docs/corpus-agent-design/workbench build` | Passed |
| `.\.venv\Scripts\python.exe -m pytest backend/tests/evaluation/test_evidence_index.py backend/tests/evaluation/test_product_journey_artifacts.py backend/tests/workspace/test_workspace_feature.py -q` | 12 passed |
| `.\.venv\Scripts\python.exe -m pytest tests/test_agent_design_parity.py -q` | 4 passed |
| `.\.venv\Scripts\python.exe scripts/check_agent_design_parity.py` | Passed |
| `.\.venv\Scripts\python.exe scripts/check_architecture_boundaries.py` | Passed |
| `.\.venv\Scripts\python.exe scripts/check_doc_coverage.py` | Changed owned files covered; pre-existing `mockruns/` warnings retained |

## E2E and visual evidence

Passing run: `20260807T051949Z-00e2a0fb37`

- Result: `.runtime/evaluations/20260807T051949Z-00e2a0fb37/result.json`
- Desktop clarification contract: `.runtime/evaluations/20260807T051949Z-00e2a0fb37/04-studio-clarification-contract.png`
- Desktop clarification evaluations: `.runtime/evaluations/20260807T051949Z-00e2a0fb37/05-studio-clarification-evals.png`
- Mobile 390x844: `.runtime/evaluations/20260807T051949Z-00e2a0fb37/06-studio-clarification-mobile-390x844.png`
- Interaction video: `.runtime/evaluations/20260807T051949Z-00e2a0fb37/design-studio-walkthrough.webm`
- Browser trace: `.runtime/evaluations/20260807T051949Z-00e2a0fb37/browser-trace.zip`

The run passed six behavioral assertions with no HTTP, console, or page errors.
It exercised Studio load/save readiness, the four ready approved Agents
behaviors, complete Agent-create evaluation coverage, the clarification design
contract, its six evaluation definitions, and the representative mobile layout.

The first evidence attempt, `20260807T051914Z-adba6f51bc`, was retained as a
failed artifact. It exposed a recorder race: the runner asserted `Saved` while
the initial Studio autosave still displayed `Saving`. The recorder was corrected
to wait for the accessible saved status, and the next run passed without changing
the product behavior.

## Current limitations

- The clarification behavior is a ready draft design and manifest entry marked
  unimplemented. Runtime delivery belongs to Step 7.
- Changed definition hashes intentionally make older runtime evaluation evidence
  stale or not run. No evaluation was rerun merely to manufacture a green status.
- Source Hub through Operations remain outside this slice.

