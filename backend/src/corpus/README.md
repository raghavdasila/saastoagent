# Corpus Backend Boundaries

- `app/` composes the host application and keeps authentication, tenancy, and
  transport outside individual features.
- `auth/` owns Corpus owner identity, browser sessions, RouteDeck claims,
  migrations, rate limits, and the mail boundary.
- `features/lounge/` owns public help and owner account-access, recovery,
  verification nodes, bindings, and AgentPolicies.
- `features/workspace/` owns authenticated Home, owner context, and entry to
  authenticated Workspace features.
- `features/sources/` owns generic source identity/revisions, connector
  registration, owner APIs, and the `sources.home` debug node. API is a
  connector beneath Sources.
- `integrations/toolrouter/` owns the replaceable ToolRouter facade and private
  hash-manifested engine snapshot. Generic Sources files cannot import it;
  only the API connector's explicit `toolrouter.py` bridge translates its
  contracts into the connector-neutral `ApiSourceEngine` contract.
- `runtime/` owns the primary Corpus chat loop and applies RouteDeck node scope
  to prompts, context, tools, operations, and surfaces.
- `shared/` is limited to backend primitives used by more than one owner.
- `composition.py` selects Lounge, Workspace, and Sources with `lounge.home`
  as the compiled entry node.
