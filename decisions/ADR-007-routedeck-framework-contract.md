# ADR-007 - RouteDeck Framework Contract

Date: 2026-05-10
Status: Accepted

## Context

The entry/auth/setup flow exposed control-flow problems: sign-in and signup could reach dead ends, frontend action ids were duplicated, backend stages carried hardcoded node/action copy, and users had little visibility into where they were in the flow.

The first fix was a backend-owned graph UI contract. During implementation, the name `GraphUI` was replaced with `RouteDeck` because GraphUI already exists elsewhere. The work also revealed that the contract should not live only as SaaStoAgent product code. We want a reusable package shape that can later publish to PyPI/npm and ship its own debugger widget.

## Decision

RouteDeck is the contract layer for graph-driven agentic navigation.

- LangGraph remains the execution engine.
- FastAPI remains the transport layer in this product.
- SaaStoAgent owns product-specific catalogs under `backend/services/route_deck/`.
- Reusable framework code lives in the sibling `../routedeck/` project.
- `routedeck_core` owns Python manifest/runtime models, validation, and snapshot helpers.
- `routedeck_langgraph` owns optional LangGraph integration: manifest/handler/condition parity checks, allowed transition diagnostics, and common graph-builder helpers.
- `@routedeck/react` owns frontend types and reusable debugger/navigation widgets.
- SaaStoAgent consumes RouteDeck through pinned local sibling packages.
- Product shells may choose placement, but the RouteDeck widget must remain independent from evidence/trace UI.
- LangGraph support is best-supported but optional. `routedeck_core` must remain framework-neutral and must not import LangGraph.

The first RouteDeck scope is entry/auth/setup/workspace handoff. Generated REST execution, approvals, QA, and learnings should adopt the same contract later instead of creating separate action/navigation conventions.

## Consequences

- Backend node/action/field/sensitive-policy definitions become the source of truth.
- Frontend auth/setup controls should render and dispatch RouteDeck metadata, not local hardcoded ids.
- Invalid submitted actions are validated before stage execution and recover with visible alternatives.
- The debugger can show focused current-node flow and a full-site graph without changing runtime decisions.
- Packaging concerns are explicit: Docker build contexts must include the sibling RouteDeck project, frontend packages should consume `@routedeck/react` through local package install, and the framework example must avoid SaaStoAgent product dependencies.
- RouteDeck needs framework-grade docs, examples, and validation commands, not only product-local comments.
- SaaStoAgent may prove reusable RouteDeck/LangGraph patterns locally first, but extraction belongs in the optional adapter package, not in product handlers or `routedeck_core`.
