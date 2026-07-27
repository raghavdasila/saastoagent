import { Skeleton } from "@/components/ui/skeleton";

export function BootstrapLoadingShell() {
  return (
    <section role="status" aria-live="polite" data-bootstrap-loading="">
      <strong>Preparing application</strong>
      <span>Loading the RouteDeck contract and session.</span>
      <div className="grid gap-2 pt-3" aria-hidden="true">
        <Skeleton className="h-3 w-3/4" />
        <Skeleton className="h-3 w-full" />
      </div>
    </section>
  );
}
