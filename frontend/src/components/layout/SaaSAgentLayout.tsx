import { Outlet } from 'react-router-dom'

import { Header } from '@/components/layout/Header'
import { ActivityBar } from '@/components/saasAgent/ActivityBar'
import { SaaSAgentProvider } from '@/context/SaaSAgentContext'

export function SaaSAgentLayout() {
  return (
    <SaaSAgentProvider>
      <div className="min-h-screen bg-background text-foreground">
        <Header />
        <div className="md:flex">
          <ActivityBar />
          <main className="min-w-0 flex-1">
            <Outlet />
          </main>
        </div>
      </div>
    </SaaSAgentProvider>
  )
}
