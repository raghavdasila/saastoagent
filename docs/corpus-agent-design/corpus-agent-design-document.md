# Corpus Agent Design Document

Status: Planning index for the locked launch features and intended work slices. This document is not a detailed product specification.

## References

- [Corpus Product Definition](../corpus-product-definition.md) is the authority for the locked feature layout and first-launch subset.
- [Corpus Basic Agent Feature Behavior Notes](./feature-behavior-notes.md) contains the current owner-authored behavior baseline and will be refined as each slice is explored.
- [Corpus Agent Design Workbench](./workbench/README.md) is the local intent, story, mock-chat, action, inline-surface, and approval workspace used to iterate on each slice.

## Locked launch features

1. **Workspace** — Provides the owner context containing their agents, sources, and related activity.
2. **Agents** — Creates and manages agents, their configurations, versions, attached sources, and deployed URLs.
3. **Source Hub** — Provides the inventory and management surface for sources that can be attached to agents.
4. **API Source / API Collection** — Uploads and processes API YAML collections as the first launch source type.
5. **Agent Designer** — Uses the agent goal and selected API operations to propose a RouteDeck-powered agent design.
6. **Agent Builder** — Turns an accepted design into the runnable agent version used by later stages, while remaining part of the Designer experience.
7. **Sandbox** — Runs the actual draft agent in isolation and records how interactions and API activity were resolved.
8. **Evaluation** — Runs configurable evalsets against an exact agent version and provides readiness evidence.
9. **Channels** — Configures where deployed agents interact with users, with hosted Web as the launch channel.
10. **Deployment** — Publishes an eligible agent version to its configured channel and identifies the active version.
11. **Operations** — Shows deployed-agent interactions, API activity, results, and decision traces for review and future evaluation cases.

## Planned work slices

### Slice 1: Workspace and Agents

Define the owner workspace, agent creation and management journey, and how an agent connects to its configuration, sources, versions, and deployed URL.

The workbench now locks the seven currently implemented Corpus owner-authentication behaviors under Workspace as an implementation-backed baseline. This does not approve the remaining Workspace or Agents design, and it does not introduce deployed-agent user authentication into Slice 1.

### Slice 2: Source, API, and Evaluation

Define Source Hub, the API collection source, and the Evaluation journey. ToolRouter provides API processing and evalset generation/review capabilities; Corpus owns the product workflow, execution against agent versions, metrics, and readiness result.

### Slice 3: Agent Designer and Builder

Define how Corpus turns an agent goal and selected API operations into a reviewed RouteDeck design and then produces a runnable agent version.

### Slice 4: Channels

Define channel configuration and the hosted Web channel used for the launch pathway; additional channels remain deferred.

### Slice 5: Sandbox, Deployment, and Operations

Define the path from isolated draft-agent execution through deployment to a hosted Web URL, followed by visibility into real deployed interactions and their reuse as evaluation cases.

## Cross-slice concerns

- **Agent configuration and version identity** connect Agents, Designer/Builder, Sandbox, Evaluation, Channels, Deployment, and Operations; they are not a separate feature.
- **AutomationBench** is a Corpus-wide validation target for Corpus itself and Corpus-produced agents; it is not another launch feature or work slice.
- The minimum end-to-end pathway remains: create agent -> upload API YAML -> attach source -> generate RouteDeck agent -> run a real sandbox interaction -> evaluate -> deploy to hosted Web -> interact publicly -> inspect in Operations.
