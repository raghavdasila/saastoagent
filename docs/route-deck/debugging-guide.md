# RouteDeck Debugging Guide

RouteDeck navigation has two surfaces: a compact status strip for always-visible orientation, and a right-side map overlay for the full debugger. The overlay has a focused current-node graph and a full site graph. It is separate from the Evidence drawer because it describes route/control-flow state, not execution evidence.

## What To Inspect

- Current node: highlighted in the center of the node-link graph.
- Previous nodes: incoming neighbors on the left side of the graph.
- Next nodes: outgoing neighbors on the right side of the graph.
- Full graph: all manifest nodes arranged in top-to-bottom lane rows on a scrollable canvas, with all manifest edges drawn between them.
- Edge labels: action id, condition, or edge type.
- Allowed actions: listed below the graph neighborhood with dark-mode-safe styling.
- Blocked actions: actions known to the manifest but invalid from the current node.

## Dead-End Workflow

1. Use the RouteDeck status strip for current-node orientation.
2. Open the side map from the strip.
3. Use Focus mode to check the current node, incoming edges, outgoing edges, and allowed actions.
4. Use Full graph mode to inspect the full site graph from system entry through auth, workspace, and terminal lanes.
5. Select a node in the graph and inspect expected input/recovery.
6. Use Export JSON to capture manifest, runtime snapshot, run id, and session id.
7. If a visible action is rejected, confirm the action's `allowed_nodes` in `backend/services/route_deck/catalog.py`.

## Export

The debugger exports JSON from the browser so issue reports can include the exact manifest and runtime snapshot without adding a backend file route.
