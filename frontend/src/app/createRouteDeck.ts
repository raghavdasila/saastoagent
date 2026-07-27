import {
  createBrowserHistoryAdapter,
  createPrivateFormState,
  createRouteDeckRouteCodec,
  createRouteDeckRouteController,
  createRouteDeckStore,
  decodeFrontendContract,
  type BrowserHistoryTarget,
  type FrontendContract,
  type RouteDeckClient,
  type RouteDeckProjection,
  type RouteDeckRouteCodec,
  type RouteDeckRouteController,
  type RouteDeckStore,
} from "@routedeck/core";
import type { RouteDeckNavigationActions } from "@routedeck/react";

import { routeDeckClient } from "../routedeck/client";

export interface AppRouteDeck {
  store: RouteDeckStore;
  privateForms: ReturnType<typeof createPrivateFormState>;
  client: RouteDeckClient;
  contract: FrontendContract;
  routes: RouteDeckRouteCodec;
  routeController: RouteDeckRouteController;
  navigationActions: RouteDeckNavigationActions;
}

export function createAppRouteDeck(options: {
  contract: FrontendContract | unknown;
  browser: BrowserHistoryTarget;
  client?: RouteDeckClient;
}): AppRouteDeck {
  const contract = decodeFrontendContract(options.contract);
  const client = options.client ?? routeDeckClient;
  const history = createBrowserHistoryAdapter(options.browser);
  let store: RouteDeckStore | null = null;
  const validatePublicRouteKey = (name: string, value: string) => {
    const projection = store?.getState().projection;
    if (projection === null || projection === undefined) return false;
    return (
      projection.current.route_params.some(
        (parameter) => parameter.name === name && parameter.value === value,
      ) ||
      projection.entities.some((entity) =>
        entity.values.some(
          (item) => item.name === name && item.value === value,
        ),
      )
    );
  };
  const validateResumeCapability = (
    handle: string,
    nodeId: string,
    params: Readonly<Record<string, string>>,
  ) => {
    const projection = store?.getState().projection;
    return (
      projection !== null &&
      projection !== undefined &&
      projection.navigation.resume_handle === handle &&
      projection.current.node_id === nodeId &&
      sameRouteParams(projection, params)
    );
  };
  const routes = createRouteDeckRouteCodec(contract, {
    validatePublicRouteKey,
    validateResumeCapability,
  });
  const routeController = createRouteDeckRouteController({
    codec: routes,
    history,
    context: () => ({
      sessionAvailable: store !== null && store.getState().projection !== null,
      validateResumeCapability,
    }),
  });
  store = createRouteDeckStore({
    client,
    history,
    routes,
    routeController,
    bootstrapMode: "resume_or_create_shareable",
  });
  return {
    store,
    privateForms: createPrivateFormState(client.privateForms),
    client,
    contract,
    routes,
    routeController,
    navigationActions: {
      back: store.back,
      forward: store.forward,
      cancel: store.cancel,
      openPath: store.openPath,
      retryNavigation: store.retryNavigation,
      abandonNavigation: store.abandonNavigation,
    },
  };
}

function sameRouteParams(
  projection: RouteDeckProjection,
  params: Readonly<Record<string, string>>,
): boolean {
  const projected = new Map<string, string>();
  for (const parameter of projection.current.route_params) {
    if (typeof parameter.value !== "string") return false;
    projected.set(parameter.name, parameter.value);
  }
  const names = Object.keys(params);
  return (
    names.length === projected.size &&
    names.every((name) => projected.get(name) === params[name])
  );
}
