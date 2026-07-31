import { decodeFrontendContract } from "@routedeck/core";
import { validateRouteDeckSurfaceRegistry } from "@routedeck/react";
import { expect, it } from "vitest";

import compiledContract from "../routedeck/corpus-frontend-contract.generated.json";
import { SourceClient } from "../features/sources/sourceClient";
import { createCorpusSurfaceRegistry } from "../routedeck/surfaces";


it("keeps the Corpus registry exactly aligned with the compiled backend contract", () => {
  const contract = decodeFrontendContract(compiledContract);
  const registry = createCorpusSurfaceRegistry(
    new SourceClient({ fetch: async () => new Response("{}") }),
  );

  expect(() =>
    validateRouteDeckSurfaceRegistry(contract, registry),
  ).not.toThrow();
});
