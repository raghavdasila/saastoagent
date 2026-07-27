# Corpus Frontend Boundaries

- `app/` owns the permanent Corpus shell and primary chat interface.
- `routedeck/` consumes typed RouteDeck state, transitions, and projections.
- `features/workspace/` owns Lounge, credentials, recovery, Home, and
  Workspace navigation content.
- `features/sources/` owns the authenticated API connector debug workbench and
  its typed same-origin client.
- `routedeck/surfaces.tsx` maps projected surface IDs to feature-owned
  components without owning their behavior.
- `shared/` contains frontend primitives that have no feature ownership.
