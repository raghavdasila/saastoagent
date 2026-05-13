# RouteDeck and LangGraph Extraction Recommendation

Date: 2026-05-13

## Recommendation

Do not make `routedeck_core` depend on LangGraph. Keep RouteDeck as a framework-neutral navigation contract and extract the SaaStoAgent pattern later as a separate RouteDeck-to-LangGraph adapter.

Recommended next package boundary:

- `routedeck_core`: manifests, nodes, actions, edges, runtime snapshots, validation.
- `routedeck_langgraph`: optional adapter that compiles/validates a RouteDeck manifest against LangGraph handlers and emits RouteDeck-aware graph diagnostics.
- Product apps such as SaaStoAgent: product catalog, product handlers, auth/workspace/setup policy.

## Why

The SaaStoAgent refactor proved the useful boundary:

- RouteDeck owns visible navigation truth.
- LangGraph owns executable control flow.
- Product handlers return state updates, and the runtime validates the next node against RouteDeck before finalizing the turn.

Official LangGraph docs support subgraphs as nodes in a parent graph and describe state sharing/persistence as part of the parent/subgraph interface. That makes an adapter valuable, but it also means RouteDeck should not assume LangGraph semantics in its core model.

## Adapter Capabilities To Consider

- Build LangGraph node groups or subgraphs from RouteDeck node metadata.
- Validate that every manifest node has a handler or is explicitly display-only.
- Validate that every manifest edge condition has a registered executable resolver.
- Validate that handler results only transition to RouteDeck-reachable nodes.
- Emit RouteDeck runtime snapshots from LangGraph state.
- Preserve non-LangGraph runtimes by keeping this adapter optional.

## Sources

- LangGraph subgraphs docs: https://docs.langchain.com/oss/python/langgraph/use-subgraphs
- LangGraph persistence docs: https://docs.langchain.com/oss/python/langgraph/persistence
