# Corpus Backend Boundaries

- `app/` composes the host application and keeps authentication, tenancy, and
  transport outside individual features.
- `routedeck/` binds Corpus definitions to RouteDeck without copying framework
  logic into the product.
- `runtime/` owns the primary Corpus chat loop and applies RouteDeck node scope
  to prompts, context, tools, operations, and surfaces.
- `shared/` is limited to backend primitives used by more than one owner.

There are no feature implementations in this scaffold.
