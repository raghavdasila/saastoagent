import { render, type RenderResult } from "@testing-library/react";
import {
  createPrivateFormState,
  createRouteDeckRouteCodec,
  createRouteDeckRouteController,
  createRouteDeckStore,
  type FrontendContract,
  type RouteDeckClient,
  type RouteDeckDispatchRequest,
  type RouteDeckDispatchResult,
  type RouteDeckEventConnection,
  type RouteDeckEventStreamOptions,
  type RouteDeckHistoryAdapter,
  type RouteDeckInspection,
  type RouteDeckNavigationRequest,
  type RouteDeckProjection,
  type RouteDeckPrivateFormSaveRequest,
  type RouteDeckReviewRequest,
  type RouteDeckSessionCreateRequest,
} from "@routedeck/core";
import { RouteDeckProvider } from "@routedeck/react";
import type { ReactElement, ReactNode } from "react";

export class TestRouteDeckClient implements RouteDeckClient {
  private projection: RouteDeckProjection;
  private readonly contract: FrontendContract | null;
  private readonly inspection: RouteDeckInspection | null;

  constructor(
    projection: RouteDeckProjection,
    contract: FrontendContract | null = null,
    inspection: RouteDeckInspection | null = null,
  ) {
    this.projection = structuredClone(projection);
    this.contract = contract === null ? null : structuredClone(contract);
    this.inspection = inspection === null ? null : structuredClone(inspection);
  }

  readonly privateFormSaves: Array<{
    formId: string;
    request: RouteDeckPrivateFormSaveRequest;
  }> = [];

  readonly privateForms = {
    load: async (formId: string) => {
      return {
        form_id: formId,
        revision: 0,
        complete: false,
        session_version: this.projection.session_version,
        value: {},
      };
    },
    save: async (formId: string, request: RouteDeckPrivateFormSaveRequest) => {
      this.privateFormSaves.push({ formId, request: structuredClone(request) });
      this.projection = {
        ...this.projection,
        session_version: request.expected_session_version + 1,
        projection_version: this.projection.projection_version + 1,
      };
      return {
        form_id: formId,
        revision: 1,
        complete: request.complete ?? false,
        session_version: this.projection.session_version,
        projection_version: this.projection.projection_version,
      };
    },
  };

  async getFrontendContract(): Promise<FrontendContract> {
    if (this.contract === null) {
      throw new Error("The contract is injected by the framework test.");
    }
    return structuredClone(this.contract);
  }

  async createSession(
    _request: RouteDeckSessionCreateRequest,
  ): Promise<RouteDeckProjection> {
    return structuredClone(this.projection);
  }

  async getSession(): Promise<RouteDeckProjection> {
    return structuredClone(this.projection);
  }

  async navigate(
    _request: RouteDeckNavigationRequest,
  ): Promise<RouteDeckProjection> {
    return structuredClone(this.projection);
  }

  async dispatch(
    _request: RouteDeckDispatchRequest,
  ): Promise<RouteDeckDispatchResult> {
    throw new Error("No operation result is configured for this framework test.");
  }

  async acceptReview(
    _reviewId: string,
    _request: RouteDeckReviewRequest,
  ): Promise<RouteDeckDispatchResult> {
    throw new Error("No review is configured for this framework test.");
  }

  async rejectReview(
    _reviewId: string,
    _request: RouteDeckReviewRequest,
  ): Promise<RouteDeckDispatchResult> {
    throw new Error("No review is configured for this framework test.");
  }

  async inspect(): Promise<RouteDeckInspection> {
    if (this.inspection === null) {
      throw new Error("No inspection is configured for this framework test.");
    }
    return structuredClone(this.inspection);
  }

  connectEvents(
    options: Omit<
      RouteDeckEventStreamOptions,
      "url" | "fetch" | "credentials"
    >,
  ): RouteDeckEventConnection {
    options.onOpen?.({ after: options.after, reconnecting: false });
    return {
      close() {},
      done: new Promise<void>(() => undefined),
    };
  }
}

class MemoryHistory implements RouteDeckHistoryAdapter {
  private path: string;
  private entryId: number | null = null;
  private readonly listeners = new Set<
    (path: string, historyEntryId: number | null) => void
  >();

  constructor(path: string) {
    this.path = path;
  }

  current(): string {
    return this.path;
  }

  currentEntryId(): number | null {
    return this.entryId;
  }

  push(path: string, historyEntryId: number): void {
    this.path = path;
    this.entryId = historyEntryId;
  }

  replace(path: string, historyEntryId: number): void {
    this.path = path;
    this.entryId = historyEntryId;
  }

  back(): void {}
  forward(): void {}

  subscribe(
    listener: (path: string, historyEntryId: number | null) => void,
  ): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }
}

export async function renderRouteDeckComponent(
  ui: ReactElement,
  options: {
    contract: FrontendContract;
    projection: RouteDeckProjection;
    inspection?: RouteDeckInspection;
  },
): Promise<RenderResult & { client: TestRouteDeckClient; dispose(): void }> {
  const client = new TestRouteDeckClient(
    options.projection,
    null,
    options.inspection ?? null,
  );
  const routes = createRouteDeckRouteCodec(options.contract, {
    validatePublicRouteKey: () => true,
    validateResumeCapability: () => true,
  });
  const history = new MemoryHistory(options.projection.navigation.route_template);
  const routeController = createRouteDeckRouteController({
    codec: routes,
    history,
    context: () => ({ sessionAvailable: true }),
  });
  let requestSequence = 0;
  const store = createRouteDeckStore({
    client,
    history,
    routes,
    routeController,
    bootstrapMode: "resume",
    createRequestId: () => `framework-request-${++requestSequence}`,
  });
  const privateForms = createPrivateFormState(client.privateForms);
  await store.bootstrap();
  const result = render(ui, {
    wrapper: ({ children }: { children: ReactNode }) => (
      <RouteDeckProvider
        store={store}
        contract={options.contract}
        routeCodec={routes}
        routeController={routeController}
        privateForms={privateForms}
        navigationActions={{
          back: store.back,
          forward: store.forward,
          cancel: store.cancel,
          openPath: store.openPath,
          retryNavigation: store.retryNavigation,
          abandonNavigation: store.abandonNavigation,
        }}
        createRequestId={() => `framework-request-${++requestSequence}`}
      >
        {children}
      </RouteDeckProvider>
    ),
  });
  return {
    ...result,
    client,
    dispose() {
      result.unmount();
      privateForms.dispose();
      store.dispose();
    },
  };
}

export function frameworkContractFixture(): FrontendContract {
  const emptySlots = {
    frame: [],
    peer: [],
    detail: [],
    form: [],
    review: [],
    status: [],
    error: [],
    diagnostic: [],
  };
  return {
    name: "framework-test-app",
    entry_node_id: "test.home",
    nodes: {
      "test.home": {
        id: "test.home",
        title: "Home",
        route_template: "/",
        deep_link_policy: "shareable",
        conversation_input: { enabled: true, disabled_message: null },
        operation_ids: ["test.open_detail"],
        surfaces: { active: "test.active", ...emptySlots },
      },
      "test.detail": {
        id: "test.detail",
        title: "Detail",
        route_template: "/detail",
        deep_link_policy: "shareable",
        conversation_input: { enabled: true, disabled_message: null },
        operation_ids: [],
        surfaces: { active: "test.detail", ...emptySlots },
      },
    },
    transitions: [
      {
        source: "test.home",
        operation_id: "test.open_detail",
        outcome: "opened",
        target: "test.detail",
      },
    ],
    surfaces: {
      "test.active": {
        id: "test.active",
        component: "test.active",
        lifecycle: "stable",
        affordances: [
          {
            id: "open_detail",
            event: "open",
            operation: { id: "test.open_detail" },
          },
        ],
        public_props_schema: {},
      },
      "test.detail": {
        id: "test.detail",
        component: "test.detail",
        lifecycle: "stable",
        affordances: [],
        public_props_schema: {},
      },
    },
  };
}

export function frameworkProjectionFixture(): RouteDeckProjection {
  const location = { node_id: "test.home", route_params: [] };
  return {
    current: location,
    diagnostics: {
      schema_version: 1,
      navgraph_version: "framework-test-v1",
      current_node_id: "test.home",
      declared_provider_ids: [],
    },
    entities: [],
    event_cursor: 0,
    failure: null,
    interaction: { phase: "idle", owner: null },
    legal_operations: [],
    suggested_actions: [],
    navigation: {
      current: location,
      current_entry_id: 1,
      route_template: "/",
      resume_handle: null,
      can_back: false,
      can_forward: false,
      can_cancel: false,
      back_node_id: null,
      forward_node_id: null,
      cancel_target_node_id: null,
    },
    projection_version: 1,
    session_version: 1,
    status: { code: "ready", message: null },
    surfaces: {
      active: { surface_id: "test.active", component: "test.active", props: [] },
      detail: [],
      diagnostic: [],
      error: [],
      form: [],
      frame: [],
      peer: [],
      review: [],
      status: [],
    },
  };
}
