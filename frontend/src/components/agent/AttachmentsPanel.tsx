import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { DatabaseZap, FileText, Trash2, Upload } from 'lucide-react'

import { api, ApiError } from '@/lib/api'
import { useSaaSAgentStore } from '@/stores/saasAgentStore'
import type { AgentDocument } from '@/types/agent'

function formatBytes(n: number) {
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(2)} MB`
}

export function AttachmentsPanel() {
  const saasAgentId = useSaaSAgentStore((state) => state.saasAgentId)
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [error, setError] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)

  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['agent-documents', saasAgentId],
    queryFn: () =>
      api.get<AgentDocument[]>(`/saas-agents/${saasAgentId}/agent/documents`),
    enabled: !!saasAgentId,
  })

  const upload = useMutation({
    mutationFn: (file: File) =>
      api.upload<AgentDocument>(`/saas-agents/${saasAgentId}/agent/documents`, file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-documents', saasAgentId] })
      setError(null)
    },
    onError: (e) => {
      setError(e instanceof ApiError ? e.message : 'Upload failed')
    },
  })

  const generateKnowledge = useMutation({
    mutationFn: () =>
      api.post<{ documents: number; chunks: number }>(`/saas-agents/${saasAgentId}/agent/rag/generate`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-documents', saasAgentId] })
      setError(null)
    },
    onError: (e) => {
      setError(e instanceof ApiError ? e.message : 'Knowledge generation failed')
    },
  })

  const remove = useMutation({
    mutationFn: (docId: string) =>
      api.delete<{ status: string }>(`/saas-agents/${saasAgentId}/agent/documents/${docId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agent-documents', saasAgentId] })
    },
  })

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragActive(false)
    const file = e.dataTransfer.files?.[0]
    if (file) upload.mutate(file)
  }

  return (
    <div className="min-h-[calc(100vh-3.5rem)] bg-slate-50 px-4 py-6 dark:bg-background sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <header className="mb-6">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">
            Attachments
          </h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Upload PDFs, text, markdown, or CSV files. They become searchable context for the agent.
          </p>
        </header>

        {error && (
          <div className="mb-4 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-300">
            {error}
          </div>
        )}

        <div
          onDragOver={(e) => {
            e.preventDefault()
            setDragActive(true)
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={onDrop}
          className={[
            'surface-card rounded-lg border-2 border-dashed p-8 text-center transition',
            dragActive ? 'border-sky-500 bg-sky-50 dark:bg-sky-950/20' : 'border-slate-200 dark:border-white/10',
          ].join(' ')}
        >
          <Upload className="mx-auto h-8 w-8 text-slate-400" />
          <p className="mt-3 text-sm text-slate-700 dark:text-slate-300">
            Drag &amp; drop a file here, or
          </p>
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="surface-solid-button mt-3 rounded-md px-4 py-2 text-sm font-medium"
          >
            Choose file
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.md,.csv,.markdown"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) upload.mutate(file)
              e.target.value = ''
            }}
          />
          <p className="mt-2 text-xs text-slate-500">PDF, TXT, MD, CSV (up to 50 MB)</p>
          {upload.isPending && <p className="mt-3 text-xs text-sky-600">Uploading &amp; embedding…</p>}
        </div>

        <section className="surface-card mt-6 rounded-lg p-4 sm:p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-sm font-semibold text-slate-900 dark:text-white">
              SaaS Agent knowledge
            </h2>
            <button
              type="button"
              onClick={() => generateKnowledge.mutate()}
              disabled={!saasAgentId || generateKnowledge.isPending}
              className="inline-flex items-center gap-2 rounded-md border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-white/10 dark:text-slate-300 dark:hover:bg-white/5"
            >
              <DatabaseZap className="h-3.5 w-3.5" />
              {generateKnowledge.isPending ? 'Generating...' : 'Generate catalog RAG'}
            </button>
          </div>
          {isLoading ? (
            <p className="mt-3 text-sm text-slate-500">Loading…</p>
          ) : documents.length === 0 ? (
            <p className="mt-3 text-sm text-slate-500">No documents uploaded yet.</p>
          ) : (
            <ul className="mt-3 divide-y divide-slate-100 dark:divide-white/5">
              {documents.map((d) => (
                <li key={d.id} className="flex items-center gap-3 py-3">
                  <FileText className="h-5 w-5 shrink-0 text-slate-400" />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-sm font-medium text-slate-900 dark:text-white">
                      {d.original_name}
                    </div>
                    <div className="text-xs text-slate-500">
                      {formatBytes(d.size_bytes)} · {d.chunk_count} chunks ·{' '}
                      {new Date(d.created_at).toLocaleString()}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      if (confirm(`Delete "${d.original_name}"?`)) {
                        remove.mutate(d.id)
                      }
                    }}
                    className="rounded-md p-2 text-slate-400 transition hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
