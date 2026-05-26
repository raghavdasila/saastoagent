# Owner Workbench Shell

## Purpose

This component owns the mounted owner application shell. It keeps the main
workbench stable while graph state changes, routes owners through auth and SaaS
Agent workspaces, and renders product surfaces without exposing framework-only
RouteDeck wording.

## Owner Files

- `frontend/src/App.tsx`
- `frontend/src/main.tsx`
- `frontend/src/components/layout/*.tsx`
- `frontend/src/context/*.tsx`
- `frontend/src/components/saasAgent/*.tsx`
- `frontend/src/components/appGraph/AppGraphShell.tsx`
- `frontend/src/stores/saasAgentUiStore.ts`

## Public Interfaces

- `/app/home`
- `/app/:nodeId`
- `/app/agents/:saasAgentId`
- `/app/agents/:saasAgentId/:nodeId`
- Auth and SaaS Agent React contexts.
- Product controls projected from RouteDeck/Corpus state.

## Dependent Flows

- Owner sign-in/register.
- SaaS Agent list/open/create flow.
- API connection setup and activation.
- Catalog, entities, actions, learning, approvals, and deployment surfaces.
- Chat-driven navigation that must not remount the full shell.

## Tests And Evidence

- `test_index/route-deck-contract.md`
- `test_index/saas-agent-foundation-contract.md`
- `frontend/scripts/e2e-docker.mjs`
- `frontend/scripts/e2e-medusa-docker.mjs`
- `npm run type-check`

## Update Triggers

Update this component doc and the code map when changing:

- React route hierarchy.
- Shell mount behavior.
- Auth or SaaS Agent context ownership.
- Owner navigation and layout.
- Product surface rendering rules.
- Quick-action visibility or copy that could leak internal route operations.
