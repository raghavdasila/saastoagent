# RouteDeck Framework

RouteDeck is a manifest-first framework layer for graph-driven agentic interfaces.

It is split into:

- `routedeck_core`: Python contracts and validation helpers for backend runtimes that sit above LangGraph/FastAPI.
- `react`: React debugger and type contracts for frontend shells.
- `docs`: framework-level architecture and packaging notes.
- `examples/minimal-fastapi-react`: minimal working example showing the full contract without SaaStoAgent product code.

The framework is repo-local for now, but the folders are shaped so `routedeck-core` can later publish to PyPI and `@routedeck/react` can later publish to npm.
