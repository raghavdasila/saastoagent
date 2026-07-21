# Corpus

Corpus is a chat-first agentic app for designing, building, evaluating,
deploying, operating, and improving agents. RouteDeck supplies the legal
interaction topology and scopes the Corpus agent to the prompt, context, tools,
operations, and surfaces of the active node.

This repository is at the architecture-scaffold stage. There is deliberately no
new feature implementation or package manifest yet.

## Start Here

- `critical_prompt.md` — product north star and non-negotiable boundaries
- `context.md` — concise current restart state
- `docs/corpus-product-definition.md` — locked layout and fifteen-feature set
- `docs/corpus-routedeck-design-notebook.html` — mobile design notebook and proposed Navgraph
- `docs/corpus-behavior-reference.md` — verified behavior of the preserved v0.1 baseline
- `structure.md` — current repository layout

## Repository Boundary

- `backend/`, `frontend/`, and `contracts/` are the empty new Corpus scaffold.
- `benchmark/saastoagent-v0.1/` is the preserved legacy application for
  behavior and video comparison. New code must not import from it.
- `docs/` and the context-architecture files describe the new direction and the
  proven baseline.

## Runtime Status

No new Corpus runtime has been selected, installed, or started from the new
scaffold. Framework and dependency decisions will be made against the current
standalone RouteDeck contracts and reference agent before implementation.
