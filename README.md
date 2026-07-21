# Corpus

Corpus is a chat-first agentic app for designing, building, evaluating,
deploying, operating, and improving agents. RouteDeck supplies the legal
interaction topology and scopes the Corpus agent to the prompt, context, tools,
operations, and surfaces of the active node.

This repository is at the architecture-scaffold stage. There is deliberately no
new feature implementation or package manifest yet.

## Start Here

- `AGENTIC_CODING_GUIDE.md` — start, feature-completion, and closeout sequence
- `critical_prompt.md` — product north star and non-negotiable boundaries
- `context.md` — concise current restart state
- `docs/corpus-product-definition.md` — locked layout and fifteen-feature set
- `docs/corpus-routedeck-design-notebook.html` — mobile design notebook and proposed Navgraph
- `docs/corpus-behavior-reference.md` — verified behavior of the preserved v0.1 baseline
- `structure.md` — current repository layout

The context architecture was reconciled against the canonical
[Context Architecture Bundle](https://github.com/saastoagent/context_architecture_bundle)
at commit `e68dc62fe2083193bf2111b95c670cdd815d0f72`.

## Repository Boundary

- `backend/`, `frontend/`, and `contracts/` are the empty new Corpus scaffold.
- `benchmark/saastoagent-v0.1/` is the ignored local legacy application for
  behavior and video comparison. New code must not import from it.
- `docs/` and the context-architecture files describe the new direction and the
  proven baseline.

## Runtime Status

No new Corpus runtime has been selected, installed, or started from the new
scaffold. Framework and dependency decisions will be made against the current
standalone RouteDeck contracts and reference agent before implementation.

## Current Validation

```powershell
python scripts/validate_design_notebook.py
python -m unittest discover -v
python scripts/check_doc_coverage.py
```

See `test_index/README.md` for what these commands prove and what they do not
prove.
