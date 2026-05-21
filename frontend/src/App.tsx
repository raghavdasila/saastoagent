import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom'

import { AppGraphShell } from '@/components/appGraph/AppGraphShell'
import { DeployedAgentChatPage } from '@/pages/DeployedAgentChatPage'

function SaaSAgentOperatorRoute() {
  const { saasAgentId } = useParams<{ saasAgentId: string }>()
  return <AppGraphShell saasAgentId={saasAgentId} />
}

function GraphNodeRoute() {
  const { nodeId } = useParams<{ nodeId: string }>()
  return <AppGraphShell nodeId={nodeId} />
}

function SaaSAgentGraphNodeRoute() {
  const { saasAgentId, nodeId } = useParams<{ saasAgentId: string; nodeId: string }>()
  return <AppGraphShell saasAgentId={saasAgentId} nodeId={nodeId} />
}

export function App() {
  return (
    <BrowserRouter future={{ v7_relativeSplatPath: true, v7_startTransition: true }}>
      <Routes>
        {/* Corpus owns product interaction; RouteDeck projects graph state into UI context. */}
        <Route path="/app/home" element={<AppGraphShell nodeId="home" />} />
        <Route path="/app/:nodeId" element={<GraphNodeRoute />} />
        <Route path="/app/agents/:saasAgentId" element={<SaaSAgentOperatorRoute />} />
        <Route path="/app/agents/:saasAgentId/:nodeId" element={<SaaSAgentGraphNodeRoute />} />
        <Route path="/a/:slug" element={<DeployedAgentChatPage />} />

        {/* Compatibility links hydrate graph context; they do not bypass Corpus. */}
        <Route path="/login" element={<Navigate to="/app/auth_sign_in" replace />} />
        <Route path="/register" element={<Navigate to="/app/auth_register" replace />} />
        <Route path="/agents/:saasAgentId" element={<SaaSAgentOperatorRoute />} />
        <Route index element={<Navigate to="/app/home" replace />} />

        <Route path="*" element={<Navigate to="/app/home" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
