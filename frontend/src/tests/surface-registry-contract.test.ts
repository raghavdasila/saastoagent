import { decodeFrontendContract } from "@routedeck/core";
import { validateRouteDeckSurfaceRegistry } from "@routedeck/react";
import { expect, it } from "vitest";

import compiledContract from "../routedeck/corpus-frontend-contract.generated.json";
import { SourceClient } from "../features/sources/sourceClient";
import { AgentClient } from "../features/agents/client";
import { AgentStore } from "../features/agents/store";
import { WorkspaceClient } from "../features/workspace/client";
import { WorkspaceStore } from "../features/workspace/store";
import { createCorpusSurfaceRegistry } from "../routedeck/surfaces";


it("keeps the Corpus registry exactly aligned with the compiled backend contract", () => {
  const contract = decodeFrontendContract(compiledContract);
  const registry = createCorpusSurfaceRegistry(
    new SourceClient({ fetch: async () => new Response("{}") }),
    new AgentStore(
      new AgentClient({ fetch: async () => new Response('{"agents":[]}') }),
    ),
    new WorkspaceStore(
      new WorkspaceClient({
        fetch: async () => new Response(JSON.stringify({
          agent_count: 0,
          agents: { status: "empty", message: "No agents." },
          sources: { status: "unavailable", message: "Unavailable." },
          recent_activity: { status: "unavailable", message: "Unavailable." },
        })),
      }),
    ),
  );

  expect(() =>
    validateRouteDeckSurfaceRegistry(contract, registry),
  ).not.toThrow();
});
