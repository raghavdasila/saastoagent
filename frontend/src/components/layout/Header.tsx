import { useNavigate } from 'react-router-dom'

import { useAuth } from '@/context/AuthContext'
import { PRODUCT_NAME } from '@/lib/entryGraph'
import { ThemeToggleButton } from '@/components/theme/ThemeToggleButton'
import { useSaaSAgent } from '@/context/SaaSAgentContext'

export function Header() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { saasAgentId } = useSaaSAgent()

  return (
    <header className="border-b border-slate-200 bg-white/90 backdrop-blur dark:border-white/10 dark:bg-[#050506]/90">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="text-left text-sm font-semibold tracking-tight text-foreground"
            type="button"
          >
            {PRODUCT_NAME}
          </button>
          {saasAgentId && (
            <button
              className="text-sm font-medium text-muted-foreground transition hover:text-foreground"
              onClick={() => navigate('/')}
              type="button"
            >
              SaaSAgents
            </button>
          )}
        </div>

        <div className="flex items-center gap-3 text-sm">
          <ThemeToggleButton />
          {user?.email && <span className="hidden text-muted-foreground sm:inline">{user.email}</span>}
          <button
            onClick={() => {
              logout()
              navigate('/login')
            }}
            className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground transition hover:opacity-90"
            type="button"
          >
            Log out
          </button>
        </div>
      </div>
    </header>
  )
}
