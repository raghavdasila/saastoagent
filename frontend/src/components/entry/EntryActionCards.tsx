import { useState } from 'react'

import type { EntryActionCard } from '@/types/entry'
export type { EntryActionCard } from '@/types/entry'

interface EntryActionCardsProps {
  actions: EntryActionCard[]
  busy?: boolean
  onSelect: (action: EntryActionCard, payload?: Record<string, unknown>) => void
}

export function EntryActionCards({ actions, busy = false, onSelect }: EntryActionCardsProps) {
  if (actions.length === 0) return null

  const formActions = actions.filter((action) => action.kind === 'form')
  const buttonActions = actions.filter((action) => action.kind !== 'form')

  return (
    <div className="space-y-3 px-4 pb-2 pt-1 sm:px-6">
      {formActions.map((action) => (
        <EntryActionForm
          key={action.id}
          action={action}
          busy={busy}
          onSubmit={(payload) => onSelect(action, payload)}
        />
      ))}
      <div className="flex flex-wrap gap-2">
        {buttonActions.map((action) => {
        const isPrimary = action.emphasis === 'primary'
        const isChip = action.kind === 'chip'
        return (
          <button
            key={action.id}
            type="button"
            disabled={busy || !!action.disabled_reason}
            title={action.description ?? undefined}
            onClick={() => onSelect(action)}
            className={[
              'inline-flex items-center rounded-full border text-xs font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50',
              isChip ? 'px-3 py-1' : 'px-3.5 py-1.5',
              isChip
                ? 'border-slate-200 bg-slate-50 text-slate-600 hover:border-sky-200 hover:bg-sky-50 hover:text-sky-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-300 dark:hover:border-sky-500/40 dark:hover:bg-sky-500/10 dark:hover:text-sky-300'
                : isPrimary
                ? 'border-sky-300 bg-sky-50 text-sky-700 hover:bg-sky-100 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-300 dark:hover:bg-sky-500/20'
                : 'border-border bg-background text-muted-foreground hover:bg-accent hover:text-accent-foreground',
            ].join(' ')}
          >
            {action.label}
          </button>
        )
        })}
      </div>
    </div>
  )
}

function EntryActionForm({
  action,
  busy,
  onSubmit,
}: {
  action: EntryActionCard
  busy: boolean
  onSubmit: (payload: Record<string, unknown>) => void
}) {
  const [values, setValues] = useState<Record<string, unknown>>(() => {
    const initial: Record<string, unknown> = { ...(action.payload || {}) }
    for (const field of action.fields || []) {
      if (field.default !== undefined && field.default !== null && initial[field.key] === undefined) {
        initial[field.key] = field.default
      }
    }
    return initial
  })

  return (
    <form
      className="max-w-2xl rounded-lg border border-slate-200 bg-white p-3 shadow-sm dark:border-white/10 dark:bg-[#0b0b0d]"
      onSubmit={(event) => {
        event.preventDefault()
        onSubmit(values)
      }}
    >
      <div className="text-sm font-semibold text-slate-950 dark:text-white">{action.label}</div>
      {action.description && (
        <p className="mt-1 text-xs leading-5 text-slate-500 dark:text-slate-400">{action.description}</p>
      )}

      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        {(action.fields || []).map((field) => (
          <label key={field.key} className="space-y-1 text-xs font-medium text-slate-600 dark:text-slate-300">
            <span>{field.label}</span>
            {field.field_type === 'select' ? (
              <select
                required={field.required}
                value={String(values[field.key] ?? '')}
                onChange={(event) => setValues((prev) => ({ ...prev, [field.key]: event.target.value }))}
                className="h-9 w-full rounded-md border border-slate-200 bg-white px-2 text-sm text-slate-950 outline-none focus:border-sky-400 dark:border-white/10 dark:bg-[#050506] dark:text-white"
              >
                {(field.options || []).map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            ) : (
              <input
                required={field.required}
                type={field.field_type === 'password' ? 'password' : field.field_type === 'url' ? 'url' : 'text'}
                value={String(values[field.key] ?? '')}
                placeholder={field.placeholder ?? undefined}
                onChange={(event) => setValues((prev) => ({ ...prev, [field.key]: event.target.value }))}
                className="h-9 w-full rounded-md border border-slate-200 bg-white px-2 text-sm text-slate-950 outline-none focus:border-sky-400 dark:border-white/10 dark:bg-[#050506] dark:text-white"
              />
            )}
            {field.help_text && <span className="block text-[11px] font-normal text-slate-400">{field.help_text}</span>}
          </label>
        ))}
      </div>

      <button
        type="submit"
        disabled={busy}
        className="mt-3 inline-flex rounded-full border border-sky-300 bg-sky-50 px-3.5 py-1.5 text-xs font-medium text-sky-700 transition hover:bg-sky-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-sky-500/40 dark:bg-sky-500/10 dark:text-sky-300"
      >
        {action.label}
      </button>
    </form>
  )
}
