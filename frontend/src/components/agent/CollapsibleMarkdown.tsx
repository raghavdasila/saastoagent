import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { ChevronDown } from 'lucide-react'

import { cn } from '@/lib/cn'

interface MarkdownSection {
  level: number
  heading: string
  body: string
}

interface Props {
  content: string
  forcePlain?: boolean
}

function isListOrFieldLine(line: string): boolean {
  return (
    /^[-*+]\s+/.test(line) ||
    /^\d+[.)]\s+/.test(line) ||
    /^[A-Za-z0-9_-]+$/.test(line) ||
    /^[A-Za-z0-9_.-]+:\s+/.test(line)
  )
}

function stripBoldHeading(line: string): string | null {
  const bold = /^\*\*(.+?)\*\*:?\s*$/.exec(line)
  return bold ? bold[1].trim() : null
}

function isPlainHeading(lines: string[], index: number): boolean {
  const raw = lines[index]
  const trimmed = raw.trim()
  if (!trimmed || raw.startsWith('    ') || isListOrFieldLine(trimmed)) return false
  if (trimmed.length > 90 || /https?:\/\//i.test(trimmed)) return false
  if (/[.!?;:]$/.test(trimmed)) return false

  const words = trimmed.split(/\s+/)
  if (words.length < 2 || words.length > 10) return false

  return index === 0 || lines[index - 1].trim() === ''
}

function splitIntoSections(markdown: string): { intro: string; sections: MarkdownSection[] } {
  const lines = markdown.split(/\r?\n/)
  const intro: string[] = []
  const sections: MarkdownSection[] = []
  let current: MarkdownSection | null = null
  let inFence = false

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index]
    if (line.trim().startsWith('```')) {
      inFence = !inFence
    }

    const markdownHeading = !inFence ? /^(#{1,3})\s+(.+?)\s*$/.exec(line) : null
    const boldHeading = !inFence ? stripBoldHeading(line.trim()) : null
    const plainHeading = !inFence && !markdownHeading && !boldHeading && isPlainHeading(lines, index)
      ? line.trim()
      : null
    if (markdownHeading || boldHeading || plainHeading) {
      if (current) {
        sections.push({ ...current, body: current.body.trim() })
      }
      current = {
        level: markdownHeading ? markdownHeading[1].length : 2,
        heading: (markdownHeading ? markdownHeading[2] : boldHeading || plainHeading || '').trim(),
        body: '',
      }
      continue
    }

    if (current) {
      current.body += `${line}\n`
    } else {
      intro.push(line)
    }
  }

  if (current) {
    sections.push({ ...current, body: current.body.trim() })
  }

  return { intro: intro.join('\n').trim(), sections }
}

function MarkdownBody({ content, className }: { content: string; className?: string }) {
  return (
    <div className={cn('prose dark:prose-invert max-w-none text-sm', className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  )
}

function sectionDefaultOpen({ isStreaming, index, sectionCount }: { isStreaming: boolean; index: number; sectionCount: number }): boolean {
  if (isStreaming) {
    return index === sectionCount - 1
  }
  return index === 0
}

export function CollapsibleMarkdown({ content, forcePlain = false }: Props) {
  const { intro, sections } = splitIntoSections(content)
  const isStreaming = forcePlain

  if (sections.length < 2) {
    return <MarkdownBody content={content} />
  }

  return (
    <div
      className="space-y-2"
      data-testid="assistant-collapsible-markdown"
      data-section-count={sections.length}
      data-streaming={isStreaming ? 'true' : 'false'}
    >
      {intro && <MarkdownBody content={intro} />}

      <div className="space-y-1.5">
        {sections.map((section, index) => {
          const isActiveStreamingSection = isStreaming && index === sections.length - 1
          return (
            <details
              key={`${section.heading}-${index}`}
              className="group rounded-lg border border-border/70 bg-background/35"
              data-testid="assistant-markdown-section"
              data-section-state={isActiveStreamingSection ? 'streaming-active' : 'complete'}
              open={sectionDefaultOpen({ isStreaming, index, sectionCount: sections.length })}
            >
              <summary
                className="flex cursor-pointer list-none items-center justify-between gap-3 px-3 py-2 text-sm font-medium marker:hidden [&::-webkit-details-marker]:hidden"
                data-testid="assistant-markdown-section-summary"
              >
                <span
                  className={cn(
                    'min-w-0 truncate',
                    section.level === 1 && 'text-foreground',
                    section.level > 1 && 'text-foreground/90',
                  )}
                >
                  {section.heading}
                </span>
                <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-open:rotate-180" />
              </summary>
              {section.body && (
                <div className="border-t border-border/60 px-3 py-2">
                  <MarkdownBody content={section.body} className="prose-p:my-2 prose-ul:my-2 prose-ol:my-2" />
                </div>
              )}
            </details>
          )
        })}
      </div>
    </div>
  )
}
