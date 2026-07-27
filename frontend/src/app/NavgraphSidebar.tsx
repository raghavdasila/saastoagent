import { useCallback, useState } from "react";
import { ChevronLeft, ChevronRight, Network } from "lucide-react";
import {
  RouteDeckError,
  RouteDeckNavGraph,
  RouteDeckStatus,
  useRouteDeckClientError,
  useRouteDeckMutationRecovery,
  useRouteDeckProjection,
} from "@routedeck/react";

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
  const projection = useRouteDeckProjection();
  const clientError = useRouteDeckClientError();
  const mutationRecovery = useRouteDeckMutationRecovery();
  const [expanded, setExpanded] = useState(false);
  const [mobileExpanded, setMobileExpanded] = useState(false);
  const [recoveryError, setRecoveryError] = useState<Error | null>(null);

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
      <div data-navgraph-map="">
        <RouteDeckNavGraph />
      </div>
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
