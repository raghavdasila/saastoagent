# Repository Documentation Instructions

1. Start with `critical_prompt.md`, `context.md`, the latest checkpoint,
   `architecture/code-map.md`, and any active plan.
2. Treat live source and executable tests as implementation truth. Treat the
   benchmark as evidence, not as the new architecture.
3. Before adding a feature, identify its RouteDeck nodes, legal operations,
   surfaces, providers, guards, transitions, and agent-configuration impact.
4. Update only the owning documentation surface:
   - product meaning in `docs/`;
   - subsystem ownership in `architecture/`;
   - durable direction changes in `decisions/`;
   - current restart state in `context.md`;
   - validation meaning in `test_index/`.
5. Keep unknowns explicit. Do not invent runtime contracts, dependencies, or
   readiness claims.
6. Never edit the preserved benchmark as part of new-product implementation.
