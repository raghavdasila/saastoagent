# SaaStoAgent v0.1 — Project Structure

Last Updated: May 5, 2026

```text
saastoagent-v0.1/
|
|- README.md
|- .env.example
|- critical_prompt.md
|- context.md
|- context_pipeline.md
|- docker-compose.yml
|- instructions.md
|- work_prompt.md
|- structure.md
|- SYSTEM_FLOW_INDEX.md
|
|- backend/
|  |- Dockerfile
|  |- requirements.txt
|  |- main.py
|  |- __init__.py
|  |
|  |- core/
|  |  |- __init__.py
|  |  |- config.py
|  |  |- database.py
|  |  |- auth.py
|  |  |- tenancy.py
|  |  |
|  |  |- models/
|  |  |  |- base.py
|  |  |  |- public.py
|  |  |  |- __init__.py
|  |  |
|  |  |- schemas/
|  |     |- auth.py
|  |     |- workspace.py
|  |     |- __init__.py
|  |
|  |- routes/
|  |  |- __init__.py
|  |  |- health.py
|  |  |- workspaces.py
|  |
|  |- services/
|     |- __init__.py
|     |- support/
|        |- __init__.py
|        |- stats.py
|
|- frontend/
|  |- Dockerfile
|  |- package.json
|  |- tsconfig.json
|  |- vite.config.ts
|  |- tailwind.config.js
|  |- postcss.config.js
|  |- index.html
|  |
|  |- src/
|     |- vite-env.d.ts
|     |- index.css
|     |- main.tsx
|     |- App.tsx
|     |
|     |- context/
|     |  |- AuthContext.tsx
|     |  |- WorkspaceContext.tsx
|     |
|     |- lib/
|     |  |- api.ts
|     |  |- storage.ts
|     |
|     |- types/
|     |  |- domain.ts
|     |
|     |- components/
|     |  |- layout/
|     |     |- AppShell.tsx
|     |     |- Header.tsx
|     |     |- Sidebar.tsx
|     |     |- WorkspaceLayout.tsx
|     |
|     |- pages/
|        |- DashboardPage.tsx
|        |- WorkspaceOverviewPage.tsx
|        |- LoginPage.tsx
|        |- RegisterPage.tsx
|        |- ConnectionsPage.tsx
|        |- ChatPage.tsx
|
|- context_history/
|  |- README.md
|
|- context_checkpoints/
|  |- README.md
|
|- plans/
|  |- README.md
|  |- saastoagent_v0_1_workspace_agent_plan.md
|
|- knowledgebase/
|  |- README.md
|  |- patterns/
|     |- README.md
|
|- skills/
|  |- README.md
|
|- logs/
|  |- README.md
|
|- decisions/
|  |- README.md
|
|- errors/
|  |- README.md
|
|- docs/
|  |- README.md
|
|- test_index/
|  |- README.md
|
|- architecture/
|  |- README.md
|  |- changelog.md
|  |- components/
|  |  |- README.md
|  |- diagrams/
|  |  |- README.md
|  |- dev_validated_docs/
|     |- README.md
|
|- audits/
   |- README.md
```

Slice 1 implementation directories are now present and validated. Later slices should extend these folders rather than introducing parallel runtime surfaces.