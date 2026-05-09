# ADR-006 - Operator Workbench Extensibility Contract

Date: 2026-05-09
Status: Accepted

## Context

ADR-003 unified anonymous entry, auth, setup, and workspace chat into one operator shell. ADR-004 made actions backend-owned. ADR-005 made widgets and canvas artifacts backend-emitted. Those decisions corrected the product direction, but the UI still risked reading as "chat plus side panels" rather than a durable operator workbench.

Future slices need a clean way to add generated REST tools, entities, execution, QA, and learnings without adding route sprawl or hardcoded panels.

## Decision

The canonical SaaStoAgent interface is an operator workbench with these stable zones:

- Intent spine: the central conversation where users describe jobs, ask questions, and direct the operator.
- Operator status strip: visible readiness, current mode, workspace stats, and current graph/runtime stage.
- Capability rail: registry-driven capability access with visible state, not generic navigation.
- Action dock: one next best backend-owned action plus secondary persistent actions.
- Context lens: a side/drawer surface that changes with the selected capability or current intent.
- Evidence drawer: collapsed by default, expandable for trace, graph/session ids, citations, tool candidates, approval state, feedback, and learning candidates.
- Autonomy ladder: a visible execution-policy control surface; until REST execution is wired, it is advisory and backend approval gates remain authoritative.

Every new visible capability must define:

- capability state
- primary action or empty state
- locked/failure state
- evidence surface
- test scenarios

The frontend may rank and place backend-emitted actions, but it must not invent auth, setup, or execution actions. Workflow validity remains backend-owned.

## Consequences

- Chat remains primary without becoming the entire product.
- The user can see what the operator can do now, what is missing, and what evidence exists.
- Future slices plug into a capability registry instead of adding one-off navigation and layout code.
- Generated tools, entity browsing, execution approval, QA, and learnings can progressively reveal power without overwhelming first-run users.
- The workbench must preserve mobile behavior by treating context and evidence as drawers when space is constrained.

