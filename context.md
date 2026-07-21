# Corpus Current Context

Updated: 2026-07-21

## Current State

- The former SaaStoAgent v0.1 application is preserved under
  `benchmark/saastoagent-v0.1/` for behavior and video comparison.
- The new root contains a feature-free backend/frontend/contracts scaffold.
- `docs/corpus-product-definition.md` records the locked product layout and the
  fifteen proposed features.
- `docs/corpus-routedeck-design-notebook.html` is the mobile discussion artifact
  and contains the proposed interactive Navgraph.
- `docs/corpus-behavior-reference.md` records proven behavior from the benchmark.
- No new runtime, dependency manifest, database, or feature implementation exists.

## Locked Product Direction

- Corpus is a chat-first agentic app whose primary agent is node-scoped by RouteDeck.
- Corpus deploys agents; deployed agents use RouteDeck for interaction state.
- Sources are API, database, Agentic-GRAG knowledge, and Smithery MCP.
- Sandbox, Evaluation, Channels, Operations, and Learning are first-class owner journeys.
- Evaluation owns evalsets and deployment-readiness evidence.
- Memory and the required policy/version/model/surface/channel contracts belong
  to the versioned agent configuration.

## Next Concrete Step

Refine the proposed Corpus Navgraph node by node, beginning with the permanent
chat shell, Agents, Agent Configuration, Evaluation/evalsets, and Channels.
Then compare the approved contract against the standalone RouteDeck Medusa
example before selecting or adding implementation dependencies.

## Runtime

There is no runnable new Corpus application yet. The benchmark remains runnable
from its own preserved directory using its own documented commands.
