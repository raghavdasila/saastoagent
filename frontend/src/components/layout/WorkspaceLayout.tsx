import { Outlet } from 'react-router-dom'

import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'
import { WorkspaceProvider } from '@/context/WorkspaceContext'

export function WorkspaceLayout() {
  return (
    <WorkspaceProvider>
      <div className="min-h-screen bg-background text-foreground">
        <Header />
        <div className="md:flex">
          <Sidebar />
          <main className="flex-1 px-4 py-8 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-5xl">
              <Outlet />
            </div>
          </main>
        </div>
      </div>
    </WorkspaceProvider>
  )
}
