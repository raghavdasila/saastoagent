import {
  createRouteDeckStore,
  type RouteDeckClientState,
  type RouteDeckDispatchResult,
} from '@routedeck/react'

import { api } from '@/lib/api'
import type { AppGraphState } from '@/types/appGraph'
import type { CorpusActionResponse, CorpusStateResponse } from '@/types/corpus'

export function corpusStatePath(nodeId?: string, saasAgentId?: string) {
  const params = new URLSearchParams()
  const effectiveNodeId = nodeId || (saasAgentId ? 'agent_home' : undefined)
  if (effectiveNodeId) params.set('node_id', effectiveNodeId)
  if (saasAgentId) params.set('saas_agent_id', saasAgentId)
  const query = params.toString()
  return `/corpus/state${query ? `?${query}` : ''}`
}

export function createSaaStoAgentRouteDeckStore({
  initialState,
  statePath,
  nodeId,
  saasAgentId,
}: {
  initialState: CorpusStateResponse
  statePath: string
  nodeId?: string
  saasAgentId?: string
}) {
  return createRouteDeckStore({
    initialState: corpusStateToRouteDeckState(initialState),
    snapshot: async () => corpusStateToRouteDeckState(await api.get<CorpusStateResponse>(statePath)),
    dispatch: async (input, currentState) => {
      const graphState = graphStateFromRouteDeckState(currentState)
      if (!graphState) throw new Error('Graph state is unavailable')
      const response = await api.post<CorpusActionResponse>('/corpus/action', {
        state: graphState,
        node_id: graphState.node || nodeId,
        saas_agent_id: graphState.active_saas_agent_id || saasAgentId,
        operation_id: input.operation_id,
        args: input.args || {},
        projection_version: currentState.projection.projection_version || 1,
      })
      return corpusActionToDispatchResult(response, input.operation_id)
    },
  })
}

export function corpusStateToRouteDeckState(response: CorpusStateResponse): RouteDeckClientState {
  return {
    projection: response.projection,
    status: 'idle',
    graph_state: response.state as unknown as Record<string, unknown>,
    location: response.replace_path || null,
  }
}

export function corpusActionToDispatchResult(
  response: CorpusActionResponse,
  operationId: string,
): RouteDeckDispatchResult {
  return {
    operation_id: operationId,
    accepted: true,
    state: corpusStateToRouteDeckState({
      state: response.state,
      projection: response.projection,
      replace_path: response.replace_path,
    }),
    active_surface: response.active_surface || null,
    messages: response.messages.map((message) => ({ ...message })),
    events: [],
    metadata: {},
  }
}

export function graphStateFromRouteDeckState(state: RouteDeckClientState): AppGraphState | null {
  const graphState = state.graph_state
  if (!graphState || typeof graphState.node !== 'string') return null
  return graphState as unknown as AppGraphState
}

export function syncBrowserPathWithoutNavigation(nextPath: string) {
  window.history.replaceState(window.history.state, '', nextPath)
}
