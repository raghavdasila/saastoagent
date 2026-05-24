import { ChevronDown } from 'lucide-react'

interface TimingSpan {
  name?: unknown
  duration_ms?: unknown
  start_ms?: unknown
  metadata?: unknown
}

interface TimingSnapshot {
  total_ms?: unknown
  spans?: unknown
}

interface Props {
  metadata?: Record<string, unknown> | null
}

export function MessageTimingDetails({ metadata }: Props) {
  const timing = parseTiming(metadata)
  if (!timing) return null

  const spans = [...timing.spans]
    .filter((span) => typeof span.name === 'string')
    .sort((left, right) => toNumber(right.duration_ms) - toNumber(left.duration_ms))
    .slice(0, 12)

  return (
    <details className="group rounded-lg border border-border/70 bg-background/45" data-testid="assistant-timing-details">
      <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-3 py-2 text-xs font-medium text-muted-foreground marker:hidden [&::-webkit-details-marker]:hidden">
        <span>View timing ({formatMs(timing.total_ms)} total)</span>
        <ChevronDown className="h-3.5 w-3.5 shrink-0 transition-transform group-open:rotate-180" />
      </summary>
      <div className="border-t border-border/60 px-3 py-2">
        <div className="grid gap-1.5 text-xs">
          {spans.map((span, index) => (
            <div key={`${String(span.name)}-${index}`} className="grid grid-cols-[minmax(0,1fr)_auto] gap-3">
              <span className="truncate font-mono text-muted-foreground" title={String(span.name)}>
                {String(span.name)}
              </span>
              <span className="tabular-nums text-foreground">{formatMs(span.duration_ms)}</span>
            </div>
          ))}
        </div>
      </div>
    </details>
  )
}

function parseTiming(metadata?: Record<string, unknown> | null): { total_ms: number; spans: TimingSpan[] } | null {
  const timing = metadata?.timing
  if (!isRecord(timing)) return null

  const totalMs = toNumber((timing as TimingSnapshot).total_ms)
  const rawSpans = (timing as TimingSnapshot).spans
  if (!Array.isArray(rawSpans)) return null

  const spans = rawSpans.filter(isRecord) as TimingSpan[]
  return { total_ms: totalMs, spans }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value != null && !Array.isArray(value)
}

function toNumber(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0
}

function formatMs(value: unknown): string {
  const ms = toNumber(value)
  if (ms >= 1000) {
    return `${(ms / 1000).toFixed(2)}s`
  }
  return `${Math.round(ms)}ms`
}
