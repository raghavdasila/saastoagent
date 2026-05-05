import { useNavigate } from 'react-router-dom'

import { useAuth } from '@/context/AuthContext'
import { useWorkspace } from '@/context/WorkspaceContext'

export function Header() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const { workspaceId } = useWorkspace()

  return (
    <header className="border-b bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="text-left text-sm font-semibold tracking-tight text-foreground"
            type="button"
          >
            SaaStoAgent v0.1
          </button>
          {workspaceId && (
            <span className="rounded-full bg-muted px-2 py-1 text-xs text-muted-foreground">
              Workspace agent
            </span>
          )}
        </div>

        <div className="flex items-center gap-3 text-sm">
          {user?.email && <span className="hidden text-muted-foreground sm:inline">{user.email}</span>}
          <button
            onClick={() => {
              logout()
              navigate('/login')
            }}
            className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-white transition hover:opacity-90"
            type="button"
          >
            Log out
          </button>
        </div>
      </div>
    </header>
  )
}
