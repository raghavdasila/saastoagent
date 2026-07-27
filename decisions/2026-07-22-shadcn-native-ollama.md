# Decision: shadcn UI And Native Ollama

Date: 2026-07-22  
Status: accepted

## Decision

- Use shadcn CLI 4.13.1 with the Radix-Nova preset for source-owned frontend
  primitives, Tailwind CSS 4.3.3 for styling, Radix UI 1.6.4 for accessible
  behavior, and Lucide React 1.25.0 for icons.
- Use `langchain-ollama==1.1.0` for the LangChain chat model and
  `ollama==0.6.2` for readiness. Do not route Ollama through the OpenAI
  compatibility endpoint.

All selected projects are open source and license-compatible with this local
application: shadcn/ui, Tailwind CSS, Radix UI, LangChain Ollama, and the Ollama
Python client use MIT licenses; Lucide uses ISC.

## Boundary

- `frontend/src/components/ui/**` and `frontend/src/lib/**` contain generic
  source-owned primitives only.
- `frontend/src/app/**` consumes those primitives without product literals.
- `frontend/src/features/workspace/**` owns Corpus/Workspace copy, components,
  and feature styling.
- `backend/src/corpus/runtime/**` owns model-provider adapters; Workspace owns
  its prompt and RouteDeck feature declarations.

## Verification

- Official shadcn Vite probe generated Button/Card and built successfully.
- Official Ollama Python and ChatOllama probe reached local Ollama 0.21.0 and
  received `CORPUS_OLLAMA_OK` from `gemma4:latest`.
- Project component/type/build/backend tests and live Ollama smoke are the
  ongoing integration gates.
