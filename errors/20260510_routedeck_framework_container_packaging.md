# RouteDeck Framework Container Packaging Failures

Date: 2026-05-10

## Symptom

After moving reusable graph-navigation code into a framework folder, the app hit runtime packaging failures:

- Backend container raised `ModuleNotFoundError: No module named 'graphui_framework'`.
- Frontend Vite dev container attempted to resolve host filesystem aliases such as `@fs/D:/.../routedeck_framework/...` and failed.
- Vite HMR websocket errors appeared when the browser connected to the containerized dev server.

## Cause

The reusable framework was outside the previous backend/frontend package copy assumptions. The backend image did not copy the framework package. The frontend dev server also used host-specific alias paths that were invalid from inside Docker.

## Resolution

- Renamed the framework to `RouteDeck` and moved reusable code under `routedeck_framework/`.
- Updated the backend Dockerfile to copy `routedeck_framework/` into the image.
- Updated frontend alias handling so `@routedeck/react` resolves from the mounted/container path.
- Switched the Docker frontend command to build plus Vite preview, avoiding dev-server HMR websocket and host `@fs` path issues during browser QA.
- Verified with `docker compose up -d --build frontend` and Playwright against `http://localhost:3007`.

## Guardrail

When RouteDeck is later split for PyPI/npm, verify both local editable development and containerized preview paths. Framework packages must be copied or installed explicitly; product apps should not depend on host-only aliases.
