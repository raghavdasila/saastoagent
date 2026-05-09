import { BrowserRouter, Navigate, Route, Routes, useParams } from 'react-router-dom'

import { OperatorGateway } from '@/components/OperatorGateway'

function WorkspaceOperatorRoute() {
  const { workspaceId } = useParams<{ workspaceId: string }>()
  return <OperatorGateway initialWorkspaceId={workspaceId} />
}

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Entry graph: backend owns the login -> workspace -> operator flow. */}
        <Route path="/login" element={<OperatorGateway initialIntent="login" />} />
        <Route path="/register" element={<OperatorGateway initialIntent="register" />} />
        <Route index element={<OperatorGateway />} />

        {/* Direct workspace links use the same unified operator shell. */}
        <Route
          path="/w/:workspaceId"
          element={<WorkspaceOperatorRoute />}
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
