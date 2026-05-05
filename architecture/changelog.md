# Architecture Changelog

## 2026-05-05

- Initialized architecture documentation scaffold for `saastoagent-v0.1`
- Adopted product boundary: REST-only workspace agent
- Chose simplified Entity Explorer over the full graph canvas as the v0.1 surface
- Implemented the Slice 1 runnable shell across FastAPI, React, and Docker Compose
- Normalized local runtime to frontend `3005`, backend `8085`, and local `frontend/` naming
- Recorded an architecture correction: re-center the current shell around an agentic workspace home before Slice 2