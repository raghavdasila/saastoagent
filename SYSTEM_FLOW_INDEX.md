# Corpus System Flow Index

These are product/runtime relationships, not Navgraphs. The proposed RouteDeck
Navgraph is maintained separately in the design notebook.

## Corpus Interaction

```text
owner message or surface action
  -> active RouteDeck node
  -> node-scoped prompt, context, tools, legal operations and surfaces
  -> Corpus agent chooses or proposes a typed operation
  -> RouteDeck validates and commits legal interaction state
  -> Corpus renders chat plus projected surfaces
```

## Agent Creation And Release

```text
source manifests + owner intent
  -> Agent Designer
  -> accepted design
  -> Agent Builder
  -> draft agent revision
  -> Sandbox
  -> Evaluation and evalsets
  -> Channels and deployment configuration
  -> Deployment
  -> Operations
```

## Governed Improvement

```text
sandbox evidence + evaluation evidence + production evidence
  -> Learning candidate
  -> owner review
  -> accepted change request
  -> new design and agent-configuration revision
```

## Deployed Agent Interaction

```text
channel event
  -> deployed agent revision and channel binding
  -> RouteDeck node scope
  -> model and legal source/tool execution
  -> RouteDeck state transition and surface projection
  -> channel-compatible response
```
