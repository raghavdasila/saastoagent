export function StudioSection({
  id,
  title,
  description,
  action,
  children,
}: {
  id: string
  title: string
  description?: string
  action?: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <section aria-labelledby={id} className="studio-section">
      <div className="studio-section-heading">
        <div className="min-w-0">
          <h2 id={id} className="text-sm font-semibold tracking-[-0.01em]">{title}</h2>
          {description && <p className="mt-0.5 max-w-2xl text-xs leading-5 text-muted-foreground">{description}</p>}
        </div>
        {action && <div className="shrink-0">{action}</div>}
      </div>
      {children}
    </section>
  )
}

