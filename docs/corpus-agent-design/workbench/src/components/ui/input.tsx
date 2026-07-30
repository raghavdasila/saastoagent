import * as React from "react"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return <input type={type} data-slot="input" className={cn("h-9 w-full min-w-0 rounded-md border border-input bg-[var(--studio-field)] px-2.5 py-1.5 !text-[13px] !leading-4 shadow-[var(--studio-shadow-panel)] transition-[border-color,box-shadow,background-color] duration-[var(--studio-motion-fast)] outline-none file:inline-flex file:h-5 file:border-0 file:bg-transparent file:text-xs file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/15 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-muted/30 disabled:opacity-65 aria-invalid:border-destructive dark:aria-invalid:border-destructive/50", className)} {...props} />
}

export { Input }
