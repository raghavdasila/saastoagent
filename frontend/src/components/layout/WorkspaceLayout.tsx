import { Outlet } from 'react-router-dom'

import { Header } from '@/components/layout/Header'
import { ActivityBar } from '@/components/workspace/ActivityBar'
import { WorkspaceProvider } from '@/context/WorkspaceContext'

export function WorkspaceLayout() {
  return (
    <WorkspaceProvider>
      <div className="min-h-screen bg-background text-foreground">
        <Header />
        <div className="md:flex">
          <ActivityBar />
          <main className="min-w-0 flex-1">
            <Outlet />
          </main>
        </div>
      </div>
    </WorkspaceProvider>
  )
}
