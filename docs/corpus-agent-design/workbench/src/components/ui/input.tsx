import * as React from "react"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return <input type={type} data-slot="input" className={cn("h-7 w-full min-w-0 rounded-none border border-input bg-transparent px-2 py-1 !text-[13px] !leading-4 transition-colors outline-none file:inline-flex file:h-5 file:border-0 file:bg-transparent file:text-xs file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-0 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-muted/20 disabled:opacity-70 aria-invalid:border-destructive dark:disabled:bg-muted/20 dark:aria-invalid:border-destructive/50", className)} {...props} />
}

export { Input }
