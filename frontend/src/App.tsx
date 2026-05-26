import { BrowserRouter, Navigate, Route, Routes, useLocation, useParams } from 'react-router-dom'

import { AppGraphShell } from '@/components/appGraph/AppGraphShell'
import { DeployedAgentChatPage } from '@/pages/DeployedAgentChatPage'

function AppGraphRoute() {
  const location = useLocation()
  const appPath = location.pathname.replace(/^\/app\/?/, '')
  const segments = appPath.split('/').filter(Boolean).map((segment) => decodeURIComponent(segment))

  if (segments.length === 0) {
    return <Navigate to="/app/home" replace />
  }
  if (segments[0] === 'agents') {
    const saasAgentId = segments[1]
    if (!saasAgentId) return <Navigate to="/app/home" replace />
    return <AppGraphShell saasAgentId={saasAgentId} nodeId={segments[2]} />
  }
  return <AppGraphShell nodeId={segments[0]} />
}

function LegacySaaSAgentRoute() {
  const { saasAgentId } = useParams<{ saasAgentId: string }>()
  return saasAgentId
    ? <Navigate to={`/app/agents/${encodeURIComponent(saasAgentId)}`} replace />
    : <Navigate to="/app/home" replace />
}

export function App() {
  return (
    <BrowserRouter future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
      <Routes>
        {/* Corpus owns product interaction; RouteDeck projects graph state into UI context. */}
        <Route path="/app/*" element={<AppGraphRoute />} />
        <Route path="/a/:slug" element={<DeployedAgentChatPage />} />

        {/* Compatibility links hydrate graph context; they do not bypass Corpus. */}
        <Route path="/login" element={<Navigate to="/app/auth_sign_in" replace />} />
        <Route path="/register" element={<Navigate to="/app/auth_register" replace />} />
        <Route path="/agents/:saasAgentId" element={<LegacySaaSAgentRoute />} />
        <Route index element={<Navigate to="/app/home" replace />} />

        <Route path="*" element={<Navigate to="/app/home" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
