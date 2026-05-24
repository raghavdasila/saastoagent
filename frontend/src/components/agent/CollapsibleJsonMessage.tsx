import { useState } from 'react'
import { ChevronDown } from 'lucide-react'

import { CollapsibleMarkdown } from './CollapsibleMarkdown'

interface Props {
  content: string
  forcePlain?: boolean
}

interface JsonPayload {
  before: string
  after: string
  technicalText: string
  summaryLines: string[]
}

function extractJsonPayload(content: string): JsonPayload | null {
  const fencedPayload = extractFencedJsonPayload(content)
  if (fencedPayload) {
    return fencedPayload
  }

  const starts: number[] = []
  for (let index = 0; index < content.length; index += 1) {
    const char = content[index]
    if (char !== '{' && char !== '[') continue
    const previous = index === 0 ? '\n' : content[index - 1]
    if (!/\s/.test(previous)) continue
    starts.push(index)
  }

  for (const start of starts) {
    for (let end = content.length - 1; end > start; end -= 1) {
      const char = content[end]
      if (char !== '}' && char !== ']') continue
      const jsonText = content.slice(start, end + 1).trim()
      try {
        const parsed = JSON.parse(jsonText)
        return {
          before: content.slice(0, start).trim(),
          after: content.slice(end + 1).trim(),
          technicalText: JSON.stringify(parsed, null, 2),
          summaryLines: summarizeJsonPayload(parsed, jsonText),
        }
      } catch {
        // Try the next candidate boundary.
      }
    }
  }

  return null
}

function extractFencedJsonPayload(content: string): JsonPayload | null {
  const fence = /```json\s*/i.exec(content)
  if (!fence || fence.index < 0) {
    return null
  }

  const before = content.slice(0, fence.index).trim()
  const bodyStart = fence.index + fence[0].length
  const closingFence = content.indexOf('```', bodyStart)
  const fallbackAfter = findLikelyAfterTextStart(content, bodyStart)
  const bodyEnd = closingFence >= 0 ? closingFence : fallbackAfter ?? content.length
  const rawText = content.slice(bodyStart, bodyEnd).trim()
  const afterStart = closingFence >= 0 ? closingFence + 3 : fallbackAfter
  const after = afterStart == null ? '' : content.slice(afterStart).trim()

  if (!rawText) {
    return null
  }

  try {
    const parsed = JSON.parse(rawText)
    return {
      before,
      after,
      technicalText: JSON.stringify(parsed, null, 2),
      summaryLines: summarizeJsonPayload(parsed, rawText),
    }
  } catch {
    return { before, after, technicalText: rawText, summaryLines: summarizeJsonPayload(null, rawText) }
  }
}

function findLikelyAfterTextStart(content: string, bodyStart: number): number | null {
  const markers = [
    '\n\nYou can ask me',
    '\r\n\r\nYou can ask me',
  ]
  const starts = markers
    .map((marker) => content.indexOf(marker, bodyStart))
    .filter((index) => index >= 0)
  return starts.length > 0 ? Math.min(...starts) : null
}

function summarizeJsonPayload(parsed: unknown, rawText: string): string[] {
  const labels = new Set<string>()
  collectLabels(parsed, labels)
  if (labels.size === 0) {
    for (const match of rawText.matchAll(/"title"\s*:\s*"([^"]+)"/gi)) {
      if (match[1]) labels.add(match[1])
      if (labels.size >= 5) break
    }
  }
  if (labels.size === 0) {
    return []
  }
  return Array.from(labels).slice(0, 5)
}

function collectLabels(value: unknown, labels: Set<string>) {
  if (labels.size >= 5 || value == null) {
    return
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      collectLabels(item, labels)
      if (labels.size >= 5) return
    }
    return
  }
  if (typeof value !== 'object') {
    return
  }

  const record = value as Record<string, unknown>
  const label = firstString(record.title, record.name, record.label, record.display_name)
  if (label) {
    labels.add(label)
  }
  for (const item of Object.values(record)) {
    collectLabels(item, labels)
    if (labels.size >= 5) return
  }
}

function firstString(...values: unknown[]): string | null {
  for (const value of values) {
    if (typeof value === 'string' && value.trim()) {
      return value.trim()
    }
  }
  return null
}

export function CollapsibleJsonMessage({ content, forcePlain = false }: Props) {
  const [detailsOpen, setDetailsOpen] = useState(false)

  if (forcePlain) {
    return <CollapsibleMarkdown content={content} forcePlain={forcePlain} />
  }

  const payload = extractJsonPayload(content)
  if (!payload) {
    return <CollapsibleMarkdown content={content} />
  }
  const { before, after, technicalText, summaryLines } = payload

  return (
    <div className="space-y-3" data-testid="assistant-json-message">
      {before && <CollapsibleMarkdown content={before} />}

      {summaryLines.length > 0 && (
        <ul className="space-y-1 text-sm" data-testid="assistant-json-summary">
          {summaryLines.map((line) => (
            <li key={line} className="flex gap-2">
              <span className="text-muted-foreground">-</span>
              <span>{line}</span>
            </li>
          ))}
        </ul>
      )}

      <details
        className="group rounded-lg border border-border/70 bg-background/45"
        data-testid="assistant-json-payload"
        open={false}
        onToggle={(event) => setDetailsOpen(event.currentTarget.open)}
      >
        <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-3 py-2 text-sm font-medium marker:hidden [&::-webkit-details-marker]:hidden">
          <span>View technical details</span>
          <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-open:rotate-180" />
        </summary>
        {detailsOpen && (
          <pre className="max-h-96 overflow-auto border-t border-border/60 px-3 py-2 text-xs leading-relaxed text-muted-foreground">
            {technicalText}
          </pre>
        )}
      </details>

      {after && <CollapsibleMarkdown content={after} />}
    </div>
  )
}
