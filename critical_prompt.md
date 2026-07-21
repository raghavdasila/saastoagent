# Corpus Critical Prompt

## North Star

Corpus is a chat-first agentic app that lets an owner assemble the sources,
design, runtime, evaluation, delivery, operation, and governed improvement of
deployed agents. RouteDeck powers Corpus and is first-class in every deployed
agent.

## Non-Negotiable Boundaries

- Corpus's primary chat agent is the application interaction spine, not a
  separate optional feature.
- RouteDeck scopes that agent to the prompt, context, tools, operations, and
  surfaces legal at the active Navgraph node.
- A Navgraph is RouteDeck navigation topology. Do not label lifecycle,
  ownership, architecture, or sequence diagrams as Navgraphs.
- Corpus deploys agents. An agentic app has a separate product meaning.
- Agents and agent-backed product behavior use role names; model-family
  nicknames never become product, feature, class, or folder names.
- API, database, Agentic-GRAG knowledge, and Smithery MCP are source families.
- RouteDeck capabilities are node-level groupings of operations, surfaces, and
  policies; there is no standalone Capability Catalog feature.
- Sandbox runs the actual draft agent with isolated state and explicit
  bindings. Evaluation runs versioned evalsets and produces immutable evidence.
- Learning proposes reviewed changes and never mutates a live agent.
- Memory belongs to an agent. Corpus has owner memory; deployed agents have
  their own configured memory boundaries.
- Policy, revision lineage, model-role bindings, memory, surfaces, access, and
  channel bindings are part of the versioned agent configuration.
- Failures remain failures. No silent mock, fixture, provider, model, cached, or
  heuristic fallback may make an unavailable dependency appear successful.
- The preserved benchmark is read-only reference material and must never become
  a dependency of the new implementation.

## Current Scope

The product layout contains fifteen proposed feature boundaries. Their concrete
RouteDeck node, operation, surface, provider, guard, and transition contracts
remain subject to node-by-node refinement.
