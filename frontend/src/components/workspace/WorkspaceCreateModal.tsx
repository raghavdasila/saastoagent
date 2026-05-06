import { type FormEvent, useEffect, useState } from 'react'
import { X } from 'lucide-react'

interface WorkspaceCreateModalProps {
  error?: string
  isOpen: boolean
  isPending: boolean
  onClose: () => void
  onCreate: (body: { name: string; slug: string }) => void
}

function toSlug(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
}

export function WorkspaceCreateModal({ error, isOpen, isPending, onClose, onCreate }: WorkspaceCreateModalProps) {
  const [name, setName] = useState('')
  const slug = toSlug(name)

  useEffect(() => {
    if (!isOpen) {
      setName('')
    }
  }, [isOpen])

  if (!isOpen) {
    return null
  }

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault()
    if (!name.trim() || !slug) {
      return
    }
    onCreate({ name: name.trim(), slug })
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4 py-6 backdrop-blur-sm">
      <form className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-xl dark:border-white/10 dark:bg-[#0f0f10] dark:shadow-black/30" onSubmit={handleSubmit}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-600">New agent</div>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-950 dark:text-white">Create workspace</h2>
          </div>
          <button
            aria-label="Close"
            className="surface-outline-button flex h-9 w-9 items-center justify-center rounded-lg text-slate-500 dark:text-slate-300"
            onClick={onClose}
            type="button"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        <div className="mt-6">
          <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300" htmlFor="workspace-name">
            Workspace name
          </label>
          <input
            autoFocus
            id="workspace-name"
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-foreground outline-none focus:border-sky-500 dark:border-white/10 dark:bg-white/[0.03]"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Acme Support Agent"
            required
          />
        </div>

        <div className="surface-muted mt-3 rounded-lg px-3 py-2 text-sm text-slate-600 dark:text-slate-400">
          <span className="font-medium text-slate-900 dark:text-white">Slug:</span> {slug || 'workspace-slug'}
        </div>

        {error && <div className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>}

        <div className="mt-6 flex justify-end gap-3">
          <button
            className="surface-outline-button rounded-lg px-4 py-2 text-sm font-medium"
            onClick={onClose}
            type="button"
          >
            Cancel
          </button>
          <button
            className="surface-solid-button rounded-lg px-4 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-70"
            disabled={isPending || !slug}
            type="submit"
          >
            {isPending ? 'Launching...' : 'Launch workspace'}
          </button>
        </div>
      </form>
    </div>
  )
}
