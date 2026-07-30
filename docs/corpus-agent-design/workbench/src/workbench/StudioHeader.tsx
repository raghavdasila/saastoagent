import {
  CheckCircle2,
  CircleAlert,
  Download,
  LoaderCircle,
  Menu,
  Moon,
  Route,
  Sun,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { STUDIO_CONFIG } from "@/workbench/studioConfig"
import type { Theme } from "@/workbench/theme"

export type SaveStatus = "saving" | "saved" | "error"

const savePresentation = {
  saving: { label: "Saving", icon: LoaderCircle },
  saved: { label: "Saved", icon: CheckCircle2 },
  error: { label: "Not saved", icon: CircleAlert },
} as const

export function StudioHeader({
  saveStatus,
  theme,
  onToggleTheme,
  onExport,
  onOpenNavigation,
}: {
  saveStatus: SaveStatus
  theme: Theme
  onToggleTheme: () => void
  onExport: () => void
  onOpenNavigation: () => void
}) {
  const save = savePresentation[saveStatus]
  const SaveIcon = save.icon

  return (
    <header className="studio-topbar">
      <div className="flex min-w-0 items-center gap-2.5">
        <Button
          type="button"
          size="icon"
          variant="ghost"
          className="md:hidden"
          aria-label="Open project navigation"
          onClick={onOpenNavigation}
        >
          <Menu />
        </Button>
        <div className="grid size-7 shrink-0 place-items-center rounded-md border border-primary/35 bg-primary/10 text-primary">
          <Route className="size-4" strokeWidth={2.2} />
        </div>
        <h1 className="min-w-0 truncate text-sm font-semibold tracking-[-0.015em] sm:text-[15px]">
          {STUDIO_CONFIG.productName}
        </h1>
        <span className="hidden h-5 w-px bg-border sm:block" aria-hidden="true" />
        <div className="hidden min-w-0 items-baseline gap-2 sm:flex">
          <span className="text-[11px] font-medium uppercase tracking-[0.08em] text-muted-foreground">Project</span>
          <strong className="truncate text-sm font-medium">{STUDIO_CONFIG.projectName}</strong>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
        <div
          role={saveStatus === "error" ? "alert" : "status"}
          aria-label={save.label}
          className={cn(
            "hidden items-center gap-1.5 px-1 text-xs font-medium sm:flex",
            saveStatus === "saved" && "text-[var(--studio-success)]",
            saveStatus === "saving" && "text-muted-foreground",
            saveStatus === "error" && "text-destructive",
          )}
        >
          <SaveIcon className={cn("size-3.5", saveStatus === "saving" && "animate-spin")} />
          {save.label}
        </div>
        <Button type="button" variant="outline" size="lg" className="h-8" aria-label={STUDIO_CONFIG.exportLabel} onClick={onExport}>
          <Download data-icon="inline-start" />
          <span className="hidden sm:inline">{STUDIO_CONFIG.exportLabel}</span>
          <span className="sm:hidden">Export</span>
        </Button>
        <Button
          type="button"
          size="icon-lg"
          variant="ghost"
          aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`}
          onClick={onToggleTheme}
        >
          {theme === "light" ? <Moon /> : <Sun />}
        </Button>
      </div>
    </header>
  )
}
