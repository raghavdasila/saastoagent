# Docker Development Runtime (Superseded)

This document is intentionally retained as a compatibility pointer. The
authoritative startup, health-check, diagnosis, rebuild, and shutdown procedure
is [`local-runtime-runbook.md`](local-runtime-runbook.md).

Use that runbook to run:

- Ollama on the Windows host;
- Corpus `backend` and `frontend` through Docker Compose; and
- the correct RouteDeck Agent Design Studio workbench on port `8782`.

The Compose `notebook` service on port `8771` is a stale legacy notebook. It is
not the Agent Design Studio and is deliberately excluded from the current
startup command.
