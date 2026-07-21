# Backend Scaffold

The backend is intentionally feature-free. It currently establishes only the
boundaries that every future feature will use.

```text
backend/
├── src/corpus/
│   ├── app/        # host composition, transport, auth and workspace context
│   ├── routedeck/  # RouteDeck application/runtime integration
│   ├── runtime/    # Corpus primary chat-agent runtime and node-scoped execution
│   └── shared/     # backend-only primitives with no feature ownership
└── tests/          # backend contract and integration tests
```

Feature packages are intentionally absent. A feature directory should be added
only after its RouteDeck nodes, operations, surfaces, providers, guards, and
outgoing transitions are agreed.

No backend framework, dependency set, or executable entrypoint has been created
yet.
