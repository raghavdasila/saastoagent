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
- Reusable framework code lives under `routedeck_framework/`.
- `routedeck_core` owns Python manifest/runtime models, validation, and snapshot helpers.
- `@routedeck/react` owns frontend types and reusable debugger/navigation widgets.
- Product shells may choose placement, but the RouteDeck widget must remain independent from evidence/trace UI.

The first RouteDeck scope is entry/auth/setup/workspace handoff. Generated REST execution, approvals, QA, and learnings should adopt the same contract later instead of creating separate action/navigation conventions.

## Consequences

- Backend node/action/field/sensitive-policy definitions become the source of truth.
- Frontend auth/setup controls should render and dispatch RouteDeck metadata, not local hardcoded ids.
- Invalid submitted actions are validated before stage execution and recover with visible alternatives.
- The debugger can show focused current-node flow and a full-site graph without changing runtime decisions.
- Packaging concerns are explicit: Docker must copy `routedeck_framework/`, Vite aliases must resolve inside container paths, and the framework example must avoid SaaStoAgent product dependencies.
- RouteDeck needs framework-grade docs, examples, and validation commands, not only product-local comments.
