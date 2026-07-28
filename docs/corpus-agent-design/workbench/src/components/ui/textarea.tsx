import * as React from "react"

import { cn } from "@/lib/utils"

function Textarea({ className, ...props }: React.ComponentProps<"textarea">) {
  return <textarea data-slot="textarea" className={cn("block min-h-14 w-full resize-y rounded-none border border-input bg-transparent px-2 py-1.5 !text-[13px] !leading-[18px] transition-colors outline-none placeholder:text-muted-foreground focus-visible:border-ring focus-visible:ring-0 disabled:cursor-not-allowed disabled:resize-none disabled:bg-muted/20 disabled:opacity-70 aria-invalid:border-destructive dark:disabled:bg-muted/20 dark:aria-invalid:border-destructive/50", className)} {...props} />
}

export { Textarea }
