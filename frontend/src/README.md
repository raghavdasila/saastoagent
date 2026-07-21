# Corpus Frontend Boundaries

- `app/` owns the permanent Corpus shell and primary chat interface.
- `routedeck/` consumes typed RouteDeck state, transitions, and projections.
- `surfaces/` renders standard typed surfaces and later registered custom
  surfaces.
- `shared/` contains frontend primitives that have no feature ownership.

Feature folders will be introduced only when feature contracts are locked.
