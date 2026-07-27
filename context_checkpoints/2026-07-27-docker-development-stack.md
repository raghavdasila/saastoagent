# Docker Development Stack Checkpoint

Date: 2026-07-27

The authoritative checkout is `D:\Dev\AI Projects\saastoagent-v0.1`. The local
development stack is implemented and currently running through Docker Compose.

Start or rebuild everything:

```powershell
docker compose up --build
```

Detached operation and shutdown:

```powershell
docker compose up --build -d
docker compose logs -f
docker compose down
```

URLs: product `http://127.0.0.1:5199/`, backend readiness
`http://127.0.0.1:8099/readyz`, Structure explorer
`http://127.0.0.1:8771/#structure`.

Ollama remains on the Windows host. ToolRouter remains embedded and reaches it
at the explicit configured `host.docker.internal` URL. RouteDeck comes from the
filtered local sibling source. Persistent runtime data is under `.runtime`.

Final proof and screenshots are in `logs/20260727_docker_development_stack.md`.
No Git operation was performed.
