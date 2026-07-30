# Corpus Frontend Boundaries

- `app/` owns the permanent Corpus shell, primary chat interface, initial
  conversation phases, and one-shot failed-session reset orchestration.
- `routedeck/` consumes typed RouteDeck state, transitions, and projections.
- `features/lounge/` owns public Lounge, credentials, recovery, verification,
  and owner-session client state.
- `features/workspace/` owns authenticated Home and Workspace navigation
  content.
- `features/sources/` owns the authenticated API connector debug workbench and
  its typed same-origin client.
- `routedeck/surfaces.tsx` maps projected surface IDs to feature-owned
  components without owning their behavior.
- `shared/` contains frontend primitives that have no feature ownership.
