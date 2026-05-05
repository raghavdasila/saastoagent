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

- Slice 1 backend, frontend, and Docker Compose foundation are implemented and runtime-validated.
- The current implementation proves auth, workspace, tenancy, and shell plumbing.
- The visible product surface still needs an agentic reset before further slice expansion.