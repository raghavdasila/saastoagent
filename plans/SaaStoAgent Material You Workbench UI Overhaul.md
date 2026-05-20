# SaaStoAgent Material You Workbench UI Overhaul

## Summary

Rebuild the current Corpus shell into a graph-adaptive Material You workbench using the chosen **Cobalt / Enterprise Agent** palette. Preserve the core SaaStoAgent vision: Corpus remains the permanent central interaction spine, RouteDeck remains the graph-backed source of truth, and active surfaces render as structured inline widgets rather than separate pages or raw workflow controls.

## Key Changes

- Apply a Material You design system:
  - Use Roboto, tonal surfaces, pill buttons/chips, 24px cards, filled text fields, state-layer hover/press behavior, and soft elevation.
  - Light mode tokens: `#FAFBFF`, `#EEF1FA`, `#E2E7F2`, `#285EA8`, `#D8E2F8`, `#1A1B20`.
  - Dark mode tokens: `#111318`, `#1C1E24`, `#262A31`, `#A9C7FF`, `#3F4759`, `#E3E2E8`.
  - Avoid purple as a dominant color; tertiary mauve is allowed only for subtle secondary accents.

- Refactor the UI into a four-panel workbench:
  - Topbar: product identity, graph breadcrumb/current work, Corpus status, user email, profile/logout, theme toggle.
  - Left rail: adaptive capability map with ready/locked/active/needs-setup states.
  - Center: permanent Corpus workspace with fixed composer, messages, quick chips, proposals, and inline RouteDeck surfaces.
  - Right sidebar: context lens, readiness, pending approvals, evidence, trace summary, and docked diagnostics.

- Restore quick action chips:
  - Derive chips from `projection.legal_operations`.
  - Render Corpus-friendly labels/icons, not raw operation ids.
  - Safe navigation/setup chips dispatch through RouteDeck.
  - Form/review/write operations open inline proposal widgets.
  - Locked capability state appears in the rail with guard explanations.

- Improve adaptive agent status:
  - Show operational labels such as `Thinking`, `Navigating`, `Opening surface`, `Preparing proposal`, `Committing`, `Running diagnostics`, and `Waiting for approval`.
  - Show status in the topbar and near the active assistant turn.
  - Do not reveal hidden reasoning or chain-of-thought.

## API / Type Changes

- Add or propagate generic UI metadata on RouteDeck operations: `category`, `kind`, `placement`, `emphasis`.
- Add frontend-only `CorpusQuickAction` mapping from `RouteDeckOperation`.
- Keep endpoint paths unchanged: `/api/corpus/state`, `/api/corpus/stream`, `/api/corpus/action`, `/api/routedeck/projection`, `/api/diagnostics/stream`.

## Test Plan

- Backend:
  - Projection includes operation UI metadata needed for chip and rail rendering.
  - Graph legality still controls every operation.
  - Existing surface-opening, auth-completion, and diagnostics tests continue passing.

- Frontend:
  - `npm run type-check`
  - `npm run build`
  - Add contract checks that quick chips do not display raw operation ids.
  - Add checks that auth user identity and logout/profile controls render after login.

- Browser QA:
  - Signup/login completes without reload and shows authenticated topbar state.
  - Home shows quick chips such as Create SaaS Agent, Connect API, Run QA when legal.
  - Create SaaS Agent opens as an inline Material You widget and commits through RouteDeck.
  - Left rail reflects active/locked/ready capability state.
  - Right diagnostics sidebar opens without breaking the composer.
  - Light and dark modes use the Cobalt Material You tokens and remain readable.

## Assumptions

- First pass focuses on the shell, tokens, quick chips, auth/user state, adaptive sidebars, inline widgets, and status labels.
- Existing SaaS Agent sub-surfaces are restyled enough to fit the new shell but not deeply redesigned.
- RouteDeck remains product-neutral; SaaStoAgent owns labels, icon choices, chip mapping, and capability grouping.
- Diagnostics remains read-only.
- No raw legal-operation UI is rendered in the product surface.
