import { Moon, Sun } from 'lucide-react'

import { useThemeStore } from '@/stores/themeStore'

interface ThemeToggleButtonProps {
  className?: string
}

export function ThemeToggleButton({ className = '' }: ThemeToggleButtonProps) {
  const theme = useThemeStore((state) => state.theme)
  const toggleTheme = useThemeStore((state) => state.toggleTheme)

  return (
    <button
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
      className={[
        'inline-flex h-10 w-10 items-center justify-center rounded-[0.8rem] border border-border/25 bg-card/80 text-foreground shadow-sm transition hover:bg-muted',
        'dark:border-white/10 dark:bg-muted/60 dark:text-slate-200 dark:hover:bg-muted',
        className,
      ].join(' ')}
      onClick={toggleTheme}
      title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
      type="button"
    >
      {theme === 'dark' ? <Sun className="h-4 w-4" aria-hidden="true" /> : <Moon className="h-4 w-4" aria-hidden="true" />}
    </button>
  )
}
