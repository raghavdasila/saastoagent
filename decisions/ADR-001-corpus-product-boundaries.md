# ADR-001: Corpus Product Boundaries And Initial Feature Layout

Status: accepted product-layout direction; feature contracts still proposed

Date: 2026-07-21

## Context

The previous SaaStoAgent v0.1 application and RouteDeck became tightly bound.
RouteDeck has since become a standalone product-neutral framework. Corpus now
needs a clean product boundary while preserving proven behavior for comparison.

## Decision

- Preserve the existing application under `benchmark/saastoagent-v0.1/`.
- Build new Corpus from a feature-free backend/frontend/contracts scaffold.
- Treat Corpus as a chat-first agentic app whose primary agent is scoped by the
  active RouteDeck node.
- Keep fifteen product feature boundaries: Workspace, Agents, Source Hub, four
  source features, Agent Designer, Agent Builder, Sandbox, Evaluation, Channels,
  Deployment, Operations, and Learning.
- Put policy, model-role bindings, memory, surfaces, channel bindings and
  revision lineage inside the versioned Agent Configuration.
- Keep feature ownership maps and lifecycle diagrams distinct from Navgraphs.

## Consequences

- The new implementation cannot import from the benchmark.
- Feature packages are not created until their RouteDeck contracts are refined.
- Evaluation/evalsets and Channels are release-path product features, not later
  infrastructure additions.
- Corpus memory and deployed-agent memory are separate agent-owned concerns.

## Validation

The product definition, notebook, root structure, and code map must agree on the
same feature count and boundaries.
