import * as React from "react"

import { cn } from "@/lib/utils"

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return <textarea data-slot="textarea" className={cn("block min-h-16 w-full resize-y rounded-md border border-input bg-[var(--studio-field)] px-2.5 py-2 !text-[13px] !leading-[19px] shadow-[var(--studio-shadow-panel)] transition-[border-color,box-shadow,background-color] duration-[var(--studio-motion-fast)] outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/15 disabled:cursor-not-allowed disabled:resize-none disabled:bg-muted/30 disabled:opacity-65 aria-invalid:border-destructive dark:aria-invalid:border-destructive/50", className)} {...props} />
}

export { Textarea }
