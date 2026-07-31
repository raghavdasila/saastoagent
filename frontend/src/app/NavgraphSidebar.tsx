import { useCallback, useEffect, useState } from "react";
import { ChevronLeft, ChevronRight, Network } from "lucide-react";
import {
  RouteDeckError,
  RouteDeckNavGraph,
  RouteDeckStatus,
  useRouteDeckClientError,
  useRouteDeckMutationRecovery,
  useRouteDeckProjection,
  useRouteDeckRuntime,
} from "@routedeck/react";
import type { JsonObject, RouteDeckInspection } from "@routedeck/core";

import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

export function NavgraphSidebar() {
  const runtime = useRouteDeckRuntime();
  const projection = useRouteDeckProjection();
  const clientError = useRouteDeckClientError();
  const mutationRecovery = useRouteDeckMutationRecovery();
  const [expanded, setExpanded] = useState(false);
  const [mobileExpanded, setMobileExpanded] = useState(false);
  const [recoveryError, setRecoveryError] = useState<Error | null>(null);
  const [view, setView] = useState<"graph" | "context">("graph");
  const [inspection, setInspection] = useState<RouteDeckInspection | null>(null);
  const [inspectionError, setInspectionError] = useState<Error | null>(null);
  const [inspectionLoading, setInspectionLoading] = useState(false);

  const loadInspection = useCallback(async () => {
    setInspectionLoading(true);
    setInspectionError(null);
    try {
      setInspection(await runtime.store.inspect());
    } catch (caught) {
      setInspectionError(
        caught instanceof Error
          ? caught
          : new Error("The current agent context could not be inspected."),
      );
    } finally {
      setInspectionLoading(false);
    }
  }, [runtime.store]);

  useEffect(() => {
    if (view !== "context") return;
    void loadInspection();
  }, [loadInspection, projection?.projection_version, view]);

  const recover = useCallback(async (action: () => Promise<unknown>) => {
    setRecoveryError(null);
    try {
      await action();
    } catch (caught) {
      setRecoveryError(
        caught instanceof Error
          ? caught
          : new Error("The RouteDeck mutation recovery failed."),
      );
    }
  }, []);

  const renderNavgraphContent = () => (
    <>
      <RouteDeckStatus>
        {({ code, message, syncStatus }) => (
          <p data-navgraph-status="">
            <span>{message ?? code}</span> <small>{syncStatus}</small>
          </p>
        )}
      </RouteDeckStatus>
      <div aria-label="Navgraph view" data-navgraph-view-switcher="">
        <Button
          type="button"
          size="sm"
          variant={view === "graph" ? "default" : "outline"}
          aria-pressed={view === "graph"}
          onClick={() => setView("graph")}
        >
          Graph
        </Button>
        <Button
          type="button"
          size="sm"
          variant={view === "context" ? "default" : "outline"}
          aria-pressed={view === "context"}
          onClick={() => setView("context")}
        >
          Agent context
        </Button>
      </div>
      {view === "graph" ? (
        <div data-navgraph-map="">
          <RouteDeckNavGraph />
        </div>
      ) : (
        <AgentContextInspection
          inspection={inspection}
          error={inspectionError}
          loading={inspectionLoading}
          onRefresh={() => void loadInspection()}
        />
      )}
      {projection?.failure === null || projection?.failure === undefined ? null : (
        <RouteDeckError failure={projection.failure} />
      )}
      {clientError === null ? null : (
        <RouteDeckError code={clientError.code} message={clientError.message} />
      )}
      {mutationRecovery.pending === null ? null : (
        <section role="alert">
          <strong>Mutation outcome unknown</strong>
          <Button
            type="button"
            disabled={mutationRecovery.retrying}
            onClick={() => void recover(mutationRecovery.retry)}
          >
            Retry exact mutation
          </Button>
          <Button
            type="button"
            variant="outline"
            disabled={mutationRecovery.retrying}
            onClick={() => void recover(mutationRecovery.abandon)}
          >
            Abandon and resync
          </Button>
        </section>
      )}
      {recoveryError === null ? null : (
        <RouteDeckError
          code="mutation_recovery_failed"
          message={recoveryError.message}
        />
      )}
    </>
  );

  return (
    <aside
      aria-label="Navgraph"
      data-expanded={expanded}
      data-navgraph-sidebar=""
    >
      <div data-navgraph-docked="">
        <Button
          type="button"
          variant="ghost"
          aria-controls="corpus-navgraph-docked-panel"
          aria-expanded={expanded}
          aria-label={expanded ? "Collapse docked Navgraph" : "Open docked Navgraph"}
          className="h-full w-full flex-col gap-2 rounded-none px-2 text-xs text-muted-foreground hover:text-foreground"
          onClick={() => setExpanded((value) => !value)}
        >
          <Network data-icon="inline-start" />
          <span>Navgraph</span>
          {expanded ? <ChevronRight aria-hidden="true" /> : <ChevronLeft aria-hidden="true" />}
        </Button>
        {expanded ? (
          <section
            id="corpus-navgraph-docked-panel"
            aria-label="Navgraph"
            data-navgraph-panel=""
          >
            <header data-navgraph-heading="">
              <h2>Navgraph</h2>
              <p>Live nodes, operations, and projected surfaces.</p>
            </header>
            <div data-navgraph-content="">{renderNavgraphContent()}</div>
          </section>
        ) : null}
      </div>

      <div data-navgraph-mobile="">
      <Sheet open={mobileExpanded} onOpenChange={setMobileExpanded}>
        <SheetTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            aria-label="Open Navgraph drawer"
            className="h-full w-full flex-col gap-1 rounded-none px-2 text-xs text-muted-foreground hover:text-foreground"
          >
            <Network data-icon="inline-start" />
            <span>Navgraph</span>
          </Button>
        </SheetTrigger>
        <SheetContent className="w-[min(92vw,440px)] overflow-y-auto p-0 sm:max-w-[440px]">
          <SheetHeader className="border-b px-5 py-5">
            <SheetTitle>Navgraph</SheetTitle>
            <SheetDescription>
              Live nodes, operations, and projected surfaces.
            </SheetDescription>
          </SheetHeader>
          <div className="grid gap-4 p-5" data-navgraph-content="">
            {renderNavgraphContent()}
          </div>
        </SheetContent>
      </Sheet>
      </div>
    </aside>
  );
}

function AgentContextInspection({
  inspection,
  error,
  loading,
  onRefresh,
}: {
  inspection: RouteDeckInspection | null;
  error: Error | null;
  loading: boolean;
  onRefresh: () => void;
}) {
  if (loading && inspection === null) {
    return <p data-agent-context-state="">Loading current agent context…</p>;
  }
  if (error !== null) {
    return (
      <section role="alert" data-agent-context-state="">
        <strong>Agent context unavailable</strong>
        <span>{error.message}</span>
        <Button type="button" size="sm" variant="outline" onClick={onRefresh}>
          Retry
        </Button>
      </section>
    );
  }
  const payload = inspection?.agent_context;
  if (payload === null || payload === undefined) {
    return (
      <section data-agent-context-state="">
        <strong>Agent context unavailable</strong>
        <p>The configured agent driver does not expose an inspection context.</p>
      </section>
    );
  }
  let parsed: ReturnType<typeof parseAgentContext>;
  try {
    parsed = parseAgentContext(payload);
  } catch (caught) {
    return (
      <section role="alert" data-agent-context-state="">
        <strong>Agent context invalid</strong>
        <span>{caught instanceof Error ? caught.message : "The inspection payload is invalid."}</span>
      </section>
    );
  }
  const { modelContext, policies, prompt } = parsed;

  return (
    <section aria-label="Current agent context" data-agent-context="">
      <header>
        <div>
          <strong>Current agent context</strong>
          <small>{requireString(modelContext.current_node, "current_node")}</small>
        </div>
        <Button type="button" size="sm" variant="outline" disabled={loading} onClick={onRefresh}>
          Refresh
        </Button>
      </header>

      <ContextJsonSection title="Status" value={modelContext.status} />
      <ContextJsonSection title="Active surface" value={modelContext.active_surface} />
      <ContextJsonSection title="Visible entities" value={modelContext.visible_entities} />
      <ContextJsonSection title="Legal tools" value={modelContext.legal_tools} />
      <ContextJsonSection title="Suggested actions" value={modelContext.suggested_actions} />
      <ContextJsonSection title="Recent observations" value={modelContext.recent_observations} />

      <section data-agent-context-policies="">
        <h3>Policies in effect</h3>
        {policies.length === 0 ? <p>None.</p> : policies.map((policy) => (
          <article key={requireString(policy.policy_id, "policy_id")}>
            <strong>{requireString(policy.policy_id, "policy_id")}</strong>
            <pre>{requireString(policy.instruction, "instruction")}</pre>
          </article>
        ))}
      </section>

      <section data-agent-context-prompt="">
        <h3>Exact system prompt</h3>
        <pre>{prompt}</pre>
      </section>
    </section>
  );
}

function ContextJsonSection({ title, value }: { title: string; value: unknown }) {
  return (
    <details data-agent-context-section="">
      <summary>{title}</summary>
      <pre>{JSON.stringify(value, null, 2)}</pre>
    </details>
  );
}

function requireObject(value: unknown, field: string): JsonObject {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`Agent context ${field} is invalid.`);
  }
  return value as JsonObject;
}

function parseAgentContext(payload: JsonObject) {
  const modelContext = requireObject(payload.model_context, "model_context");
  return {
    modelContext,
    prompt: requireString(payload.system_prompt, "system_prompt"),
    policies: requireObjectArray(modelContext.policies, "policies"),
  };
}

function requireObjectArray(value: unknown, field: string): JsonObject[] {
  if (!Array.isArray(value)) throw new Error(`Agent context ${field} is invalid.`);
  return value.map((item) => requireObject(item, field));
}

function requireString(value: unknown, field: string): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`Agent context ${field} is invalid.`);
  }
  return value;
}
