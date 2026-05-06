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
        'inline-flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-700 transition hover:bg-slate-50',
        'dark:border-white/10 dark:bg-white/[0.03] dark:text-slate-200 dark:hover:bg-white/[0.08]',
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
