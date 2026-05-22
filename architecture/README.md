# SaaStoAgent v0.1 Architecture

## Overview

This folder tracks the intended and implemented architecture for SaaStoAgent v0.1.

The current architecture direction is:

- workspace-owned agent boundary
- REST-only provider surface
- lighter entity explorer instead of a full graph product
- later reuse of foundation-agent chat shell patterns where appropriate

## Structure

- `changelog.md` — architecture evolution
- `components/` — component deep dives
- `diagrams/` — visual or textual diagrams
- `dev_validated_docs/` — validated implementation notes once code exists

## Current State

- The RouteDeck runtime-store foundation is implemented and now drives the
  current Corpus-centered workbench shell.
- The visible product surface has moved past the initial agentic reset into a
  validated workbench/debugger pass: inline auth/surfaces, fixed composer, and
  read-only docked/fullscreen diagnostics are all implemented.
- The shared RouteDeck debugger now uses compact lane-separated focus routing
  and a root-centered navgraph full map.
- The horizontal sandbox path is now verified through Docker UI E2E and a real
  Medusa fixture, with product runtime kept OpenAPI/user-config driven.
- The next architecture follow-through is RouteDeck/Corpus boundary cleanup,
  collapsible public result details, conversation-grounded product/cart
  continuity, semantic navgraph grouping, browser automation, and removal of
  remaining compatibility `/api/app/graph/*` usage.
