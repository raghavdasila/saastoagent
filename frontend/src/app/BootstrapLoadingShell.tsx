import { Skeleton } from "@/components/ui/skeleton";

export function BootstrapLoadingShell({
  title = "Preparing Corpus",
  message = "Loading Corpus…",
}: {
  title?: string;
  message?: string;
} = {}) {
  return (
    <section role="status" aria-live="polite" data-bootstrap-loading="">
      <strong>{title}</strong>
      <span>{message}</span>
      <div className="grid gap-2 pt-3" aria-hidden="true">
        <Skeleton className="h-3 w-3/4" />
        <Skeleton className="h-3 w-full" />
      </div>
    </section>
  );
}
