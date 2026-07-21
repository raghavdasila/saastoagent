# Frontend Scaffold

The frontend is the chat-first Corpus agentic-app surface. It is intentionally
feature-free at this stage.

```text
frontend/
├── src/
│   ├── app/        # Corpus shell, primary chat and application composition
│   ├── routedeck/  # RouteDeck state/projection bridge and navigation binding
│   ├── surfaces/   # standard surface registry and render boundary
│   └── shared/     # frontend-only primitives with no feature ownership
└── tests/          # browser, interaction and frontend contract tests
```

The primary chat is not an optional assistant feature. RouteDeck changes the
scope available to the same Corpus agent as the active Navgraph node changes.

No frontend framework, dependency set, or executable entrypoint has been
created yet.
